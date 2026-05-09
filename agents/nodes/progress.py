"""
Progress Agent — Monitors completion, detects bottlenecks, adapts the plan.

This agent:
1. Analyzes task completion data
2. Detects if the learner is behind or ahead
3. Provides coaching encouragement
4. Re-adjusts the plan when needed
"""

from __future__ import annotations

import logging
from agents.state import AgentState
from backend.services.llm_client import generate_json, chat_completion

logger = logging.getLogger(__name__)

PROGRESS_SYSTEM_PROMPT = """You are a supportive study progress coach AI. Your role is to:
1. Analyze a learner's progress on their study plan
2. Identify if they are on track, behind, or ahead
3. Detect bottlenecks or areas of difficulty
4. Provide encouraging, constructive feedback
5. Suggest plan adaptations when needed

IMPORTANT RULES:
- Be encouraging and supportive, never judgmental
- If the learner is behind, suggest realistic catch-up strategies
- If the learner is ahead, suggest bonus challenges
- If the learner is stuck, provide specific help strategies
- Always maintain a positive, growth-mindset tone
"""

PROGRESS_ANALYSIS_PROMPT = """Analyze the learner's progress and provide guidance:

**Original Goal:** {goal}
**Study Plan:** {plan_summary}
**Total Tasks:** {total_tasks}
**Completed:** {completed} ({completion_pct}%)
**In Progress:** {in_progress}
**Stuck:** {stuck}
**Skipped:** {skipped}

**User Feedback:** {feedback}

**Tasks marked as stuck:**
{stuck_tasks}

Respond as JSON:
{{
    "status": "on_track|behind|ahead|stuck",
    "completion_percentage": <number>,
    "coaching_message": "An encouraging, personalized message to the learner",
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "plan_needs_adaptation": true|false,
    "adaptation_reason": "Why the plan should change (if applicable)",
    "adapted_tasks": [
        {{
            "action": "add|remove|modify|reschedule",
            "task_id": "t1",
            "description": "What to change"
        }}
    ]
}}
"""


def progress_node(state: AgentState) -> dict:
    """
    Progress Agent node for the LangGraph workflow.

    Analyzes learner progress and adapts the plan if needed.
    """
    logger.info("📊 Progress Agent: Analyzing progress...")

    study_plan = state.get("study_plan", {})
    task_schedule = state.get("task_schedule", [])
    progress_update = state.get("progress_update", {})

    if not task_schedule:
        return {
            "coaching_message": "Your study plan is being set up! Start with the first task when ready. 🚀",
            "plan_adapted": False,
            "current_step": "progress_initial",
            "error": None,
        }

    # Compute stats from task schedule
    task_statuses = progress_update.get("task_statuses", {})
    total = len(task_schedule)
    completed = sum(1 for s in task_statuses.values() if s == "completed")
    in_progress = sum(1 for s in task_statuses.values() if s == "in_progress")
    stuck = sum(1 for s in task_statuses.values() if s == "stuck")
    skipped = sum(1 for s in task_statuses.values() if s == "skipped")
    completion_pct = round((completed / total) * 100, 1) if total > 0 else 0

    stuck_tasks_text = "\n".join(
        f"- {t.get('title', '?')} (Day {t.get('day', '?')})"
        for t in task_schedule
        if task_statuses.get(t.get("id", ""), "") == "stuck"
    ) or "None"

    feedback = progress_update.get("user_feedback", "No specific feedback")
    plan_summary = study_plan.get("plan_summary", state.get("goal", ""))

    messages = [
        {"role": "system", "content": PROGRESS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": PROGRESS_ANALYSIS_PROMPT.format(
                goal=state.get("goal", ""),
                plan_summary=plan_summary,
                total_tasks=total,
                completed=completed,
                completion_pct=completion_pct,
                in_progress=in_progress,
                stuck=stuck,
                skipped=skipped,
                feedback=feedback,
                stuck_tasks=stuck_tasks_text,
            ),
        },
    ]

    try:
        result = generate_json(messages, temperature=0.7)

        return {
            "coaching_message": result.get(
                "coaching_message",
                "Keep going! Every step counts. 💪"
            ),
            "plan_adapted": result.get("plan_needs_adaptation", False),
            "progress_update": {
                **progress_update,
                "analysis": result,
            },
            "current_step": "progress_complete",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Progress Agent failed: {e}")
        return {
            "coaching_message": "Keep going! Every step forward matters. 💪",
            "plan_adapted": False,
            "current_step": "progress_failed",
            "error": str(e),
        }
