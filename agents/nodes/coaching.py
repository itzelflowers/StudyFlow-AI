"""
Coaching Agent — Converts the study plan into actionable daily/weekly tasks.

This agent:
1. Takes the study plan milestones and resources
2. Creates concrete, actionable tasks for each day/week
3. Distributes work evenly across available time
4. Balances theory, practice, and review
"""

from __future__ import annotations

import logging
from agents.state import AgentState
from backend.services.llm_client import generate_json

logger = logging.getLogger(__name__)

COACHING_SYSTEM_PROMPT = """You are a study coach. Convert study plans into daily tasks.
Keep all text concise and actionable. Each task 30-60 minutes.
"""

COACHING_USER_PROMPT = """Create tasks for this plan:

Goal: {goal}
Level: {level}
Hours/week: {hours}
Weeks: {total_weeks}

Milestones:
{milestones}

Resources:
{resources}

Create max 5 tasks per week. Return ONLY this JSON:
{{
    "tasks": [
        {{
            "id": "t1",
            "title": "Short task title",
            "description": "What to do",
            "milestone_id": "m1",
            "day": 1,
            "estimated_minutes": 45,
            "task_type": "learn",
            "resources_used": ["Resource name"]
        }}
    ],
    "weekly_summary": [
        {{
            "week": 1,
            "focus": "Week focus",
            "total_tasks": 5,
            "total_hours": 10
        }}
    ]
}}
"""


def coaching_node(state: AgentState) -> dict:
    """
    Coaching Agent node for the LangGraph workflow.

    Converts milestones and resources into actionable tasks.
    """
    logger.info("📋 Coaching Agent: Creating task schedule...")

    study_plan = state.get("study_plan")
    resources = state.get("resources", [])

    if not study_plan:
        return {
            "task_schedule": [],
            "current_step": "coaching_skipped",
            "error": "No study plan available",
        }

    goal = state["goal"]
    level = state.get("assessed_level", "beginner")
    hours = state.get("available_hours", 10)
    total_weeks = study_plan.get("total_weeks", 4)
    milestones = study_plan.get("milestones", [])

    milestones_text = "\n".join(
        f"- **{m.get('id', f'm{i+1}')}**: {m.get('title', 'Untitled')} "
        f"(Week {m.get('week', i+1)}, ~{m.get('estimated_hours', 5)}h)\n"
        f"  Objectives: {', '.join(m.get('learning_objectives', []))}"
        for i, m in enumerate(milestones)
    )

    resources_text = "\n".join(
        f"- Milestone {mr.get('milestone_id', '?')}: "
        + ", ".join(r.get("title", "?") for r in mr.get("resources", [])[:3])
        for mr in resources
    ) if resources else "No specific resources yet, suggest generic activities."

    messages = [
        {"role": "system", "content": COACHING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": COACHING_USER_PROMPT.format(
                goal=goal,
                level=level,
                hours=hours,
                total_weeks=total_weeks,
                milestones=milestones_text,
                resources=resources_text,
            ),
        },
    ]

    try:
        result = generate_json(messages, temperature=0.7, max_tokens=6000)
        tasks = result.get("tasks", [])

        return {
            "task_schedule": tasks,
            "current_step": "coaching_complete",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Coaching Agent failed: {e}")
        return {
            "task_schedule": [],
            "current_step": "coaching_failed",
            "error": str(e),
        }
