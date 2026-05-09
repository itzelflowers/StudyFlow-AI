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

COACHING_SYSTEM_PROMPT = """You are an expert study coach AI. Your role is to convert study plan 
milestones into concrete, actionable daily or weekly tasks.

You should create tasks that are:
- Specific and actionable (not vague)
- Achievable in the estimated time
- Balanced between theory and practice
- Progressive (building on previous tasks)
- Include review sessions to reinforce learning

IMPORTANT RULES:
- Each task should take 25-90 minutes (Pomodoro-friendly)
- Include "review" tasks every 3-4 days
- Include practice/exercise tasks, not just reading/watching
- Add specific instructions (e.g., "Watch video X and solve problems 1-5")
- Group tasks by day number within each week
"""

COACHING_USER_PROMPT = """Create an actionable task schedule for the following study plan:

**Goal:** {goal}
**Level:** {level}
**Hours per week:** {hours}
**Total weeks:** {total_weeks}

**Milestones:**
{milestones}

**Available Resources:**
{resources}

Create daily tasks. Return as JSON:
{{
    "tasks": [
        {{
            "id": "t1",
            "title": "Short task title",
            "description": "Detailed instructions for what to do",
            "milestone_id": "m1",
            "day": 1,
            "estimated_minutes": 45,
            "task_type": "learn|practice|review|project",
            "resources_used": ["Resource title 1"]
        }}
    ],
    "weekly_summary": [
        {{
            "week": 1,
            "focus": "What this week covers",
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
