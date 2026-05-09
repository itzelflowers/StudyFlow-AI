"""
Shared agent state schema for the LangGraph workflow.

This defines the data structure that flows through all agent nodes.
"""

from __future__ import annotations

from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The shared state that flows through the LangGraph agent pipeline.

    Each agent node reads from and writes to this state.
    """

    # ─── User Input ──────────────────────────────────────────────
    goal: str                          # The user's learning goal
    available_hours: float             # Hours per week available
    deadline_weeks: Optional[int]      # Target completion in weeks
    diagnostic_answers: list[dict]     # User's diagnostic responses

    # ─── Planning Agent Output ───────────────────────────────────
    assessed_level: str                # beginner / intermediate / advanced
    study_plan: Optional[dict]         # The structured study plan

    # ─── Research Agent Output ───────────────────────────────────
    resources: list[dict]              # Curated resources per milestone

    # ─── Coaching Agent Output ───────────────────────────────────
    task_schedule: list[dict]          # Daily/weekly task schedule

    # ─── Progress Agent Output ───────────────────────────────────
    progress_update: Optional[dict]    # Progress analysis result
    plan_adapted: bool                 # Whether the plan was re-adjusted
    coaching_message: str              # Encouragement or guidance message

    # ─── Workflow Control ────────────────────────────────────────
    messages: Annotated[list, add_messages]  # Conversation history
    current_step: str                  # Current step in the workflow
    error: Optional[str]              # Error message if something fails
