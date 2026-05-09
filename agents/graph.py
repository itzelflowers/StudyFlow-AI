"""
LangGraph workflow definition for StudyFlow AI.

This module wires together all agent nodes into a state machine:
Planning → Research → Coaching → (Progress when updates arrive)
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from agents.state import AgentState
from agents.nodes.planning import planning_node
from agents.nodes.research import research_node
from agents.nodes.coaching import coaching_node
from agents.nodes.progress import progress_node

logger = logging.getLogger(__name__)


# ─── Routing Functions ───────────────────────────────────────────────────────

def should_continue_after_planning(state: AgentState) -> Literal["research", "end"]:
    """After planning, continue to research if plan was created successfully."""
    if state.get("error") or not state.get("study_plan"):
        logger.warning("Planning failed, ending workflow.")
        return "end"
    return "research"


def should_continue_after_research(state: AgentState) -> Literal["coaching", "end"]:
    """After research, continue to coaching."""
    if state.get("error") and not state.get("resources"):
        logger.warning("Research failed completely, ending workflow.")
        return "end"
    return "coaching"


def should_adapt_plan(state: AgentState) -> Literal["planning", "end"]:
    """After progress check, re-plan if adaptation is needed."""
    if state.get("plan_adapted"):
        logger.info("Plan adaptation needed, re-running planning.")
        return "planning"
    return "end"


# ─── Build the Graph ─────────────────────────────────────────────────────────

def build_study_plan_graph() -> StateGraph:
    """
    Build the main study plan creation workflow.

    Flow: Planning → Research → Coaching → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planning", planning_node)
    graph.add_node("research", research_node)
    graph.add_node("coaching", coaching_node)

    # Set entry point
    graph.set_entry_point("planning")

    # Add edges with conditional routing
    graph.add_conditional_edges(
        "planning",
        should_continue_after_planning,
        {"research": "research", "end": END},
    )
    graph.add_conditional_edges(
        "research",
        should_continue_after_research,
        {"coaching": "coaching", "end": END},
    )
    graph.add_edge("coaching", END)

    return graph.compile()


def build_progress_graph() -> StateGraph:
    """
    Build the progress monitoring workflow.

    Flow: Progress → (Conditional: Re-plan or END)
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("progress", progress_node)
    graph.add_node("planning", planning_node)
    graph.add_node("research", research_node)
    graph.add_node("coaching", coaching_node)

    # Set entry point
    graph.set_entry_point("progress")

    # Conditional: re-plan if needed
    graph.add_conditional_edges(
        "progress",
        should_adapt_plan,
        {"planning": "planning", "end": END},
    )

    # If re-planning, go through full flow again
    graph.add_conditional_edges(
        "planning",
        should_continue_after_planning,
        {"research": "research", "end": END},
    )
    graph.add_conditional_edges(
        "research",
        should_continue_after_research,
        {"coaching": "coaching", "end": END},
    )
    graph.add_edge("coaching", END)

    return graph.compile()


# ─── Pre-compiled Graphs ─────────────────────────────────────────────────────

study_plan_workflow = build_study_plan_graph()
progress_workflow = build_progress_graph()


# ─── Public API ──────────────────────────────────────────────────────────────

def create_study_plan(
    goal: str,
    available_hours: float = 10.0,
    deadline_weeks: int | None = None,
    diagnostic_answers: list[dict] | None = None,
) -> dict:
    """
    Run the full study plan creation pipeline.

    Returns the final state with study_plan, resources, and task_schedule.
    """
    logger.info(f"🚀 Starting study plan creation for: {goal}")

    initial_state: AgentState = {
        "goal": goal,
        "available_hours": available_hours,
        "deadline_weeks": deadline_weeks,
        "diagnostic_answers": diagnostic_answers or [],
        "assessed_level": "",
        "study_plan": None,
        "resources": [],
        "task_schedule": [],
        "progress_update": None,
        "plan_adapted": False,
        "coaching_message": "",
        "messages": [],
        "current_step": "starting",
        "error": None,
    }

    result = study_plan_workflow.invoke(initial_state)
    logger.info(f"✅ Study plan creation complete. Step: {result.get('current_step')}")
    return result


def check_progress(
    goal: str,
    study_plan: dict,
    task_schedule: list[dict],
    task_statuses: dict[str, str],
    user_feedback: str = "",
) -> dict:
    """
    Run the progress monitoring pipeline.

    Returns the final state with coaching_message and potential plan adaptation.
    """
    logger.info(f"📊 Checking progress for: {goal}")

    initial_state: AgentState = {
        "goal": goal,
        "available_hours": 10.0,
        "deadline_weeks": None,
        "diagnostic_answers": [],
        "assessed_level": "",
        "study_plan": study_plan,
        "resources": [],
        "task_schedule": task_schedule,
        "progress_update": {
            "task_statuses": task_statuses,
            "user_feedback": user_feedback,
        },
        "plan_adapted": False,
        "coaching_message": "",
        "messages": [],
        "current_step": "checking_progress",
        "error": None,
    }

    result = progress_workflow.invoke(initial_state)
    logger.info(f"✅ Progress check complete. Adapted: {result.get('plan_adapted')}")
    return result
