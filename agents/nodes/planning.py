"""
Planning Agent — Interprets the learning goal and creates a structured study plan.

This agent:
1. Analyzes the user's goal and diagnostic answers
2. Assesses the learner's current level
3. Generates a structured study plan with milestones
"""

from __future__ import annotations

import logging
from agents.state import AgentState
from backend.services.llm_client import generate_json

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """You are an expert educational planner. Create concise, actionable study plans.
Keep all text short and to the point. Use simple, clear language.
"""

PLANNING_USER_PROMPT = """Create a study plan for:

Goal: {goal}
Hours/week: {hours}
Weeks: {deadline}
Diagnostic: {diagnostic}

Return ONLY this JSON (keep descriptions under 15 words, max 4 milestones, max 2 topics and 2 objectives per milestone):
{{
    "assessed_level": "beginner",
    "total_weeks": 4,
    "milestones": [
        {{
            "id": "m1",
            "title": "Short title",
            "description": "Brief description",
            "order": 1,
            "week": 1,
            "topics": ["topic1"],
            "learning_objectives": ["objective1"],
            "estimated_hours": 10
        }}
    ],
    "plan_summary": "Brief overview"
}}
"""


def planning_node(state: AgentState) -> dict:
    """
    Planning Agent node for the LangGraph workflow.

    Reads the user's goal and diagnostic answers, generates a study plan.
    """
    logger.info("🎯 Planning Agent: Creating study plan...")

    goal = state["goal"]
    hours = state.get("available_hours", 10)
    deadline = state.get("deadline_weeks") or "flexible (suggest optimal)"
    diagnostic = state.get("diagnostic_answers", [])

    messages = [
        {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": PLANNING_USER_PROMPT.format(
                goal=goal,
                hours=hours,
                deadline=deadline,
                diagnostic=diagnostic,
            ),
        },
    ]

    try:
        result = generate_json(messages, temperature=0.6, max_tokens=8192)

        return {
            "assessed_level": result.get("assessed_level", "beginner"),
            "study_plan": result,
            "current_step": "planning_complete",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Planning Agent failed: {e}")
        return {
            "assessed_level": "beginner",
            "study_plan": None,
            "current_step": "planning_failed",
            "error": str(e),
        }
