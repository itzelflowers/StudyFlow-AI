"""
Research Agent — Finds and ranks learning resources for each milestone.

This agent:
1. Takes each milestone's topics
2. Searches for relevant learning resources
3. Ranks them by quality and relevance
4. Associates resources with milestones
"""

from __future__ import annotations

import logging
from agents.state import AgentState
from backend.services.llm_client import generate_json

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are an educational resource curator. Recommend the best free learning resources.
Keep all text concise. Prioritize Khan Academy, 3Blue1Brown, MIT OCW for math.
"""

RESEARCH_USER_PROMPT = """Find resources for this study plan:

Goal: {goal}
Level: {level}
Milestones:
{milestones}

For each milestone, recommend exactly 2 resources. Return ONLY this JSON:
{{
    "milestone_resources": [
        {{
            "milestone_id": "m1",
            "resources": [
                {{
                    "title": "Resource name",
                    "url": "https://...",
                    "resource_type": "video",
                    "difficulty": "beginner",
                    "description": "Brief description",
                    "estimated_minutes": 30,
                    "provider": "Khan Academy"
                }}
            ]
        }}
    ]
}}
"""


def research_node(state: AgentState) -> dict:
    """
    Research Agent node for the LangGraph workflow.

    Takes the study plan milestones and finds relevant resources.
    """
    logger.info("🔍 Research Agent: Finding resources...")

    study_plan = state.get("study_plan")
    if not study_plan:
        return {
            "resources": [],
            "current_step": "research_skipped",
            "error": "No study plan available",
        }

    goal = state["goal"]
    level = state.get("assessed_level", "beginner")
    milestones = study_plan.get("milestones", [])

    milestones_text = "\n".join(
        f"- **{m.get('id', f'm{i+1}')}**: {m.get('title', 'Untitled')} — {m.get('description', '')}"
        f" (Topics: {', '.join(m.get('topics', []))})"
        for i, m in enumerate(milestones)
    )

    messages = [
        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": RESEARCH_USER_PROMPT.format(
                goal=goal,
                level=level,
                milestones=milestones_text,
            ),
        },
    ]

    try:
        result = generate_json(messages, temperature=0.7, max_tokens=8192)
        resources = result.get("milestone_resources", [])

        return {
            "resources": resources,
            "current_step": "research_complete",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Research Agent failed: {e}")
        return {
            "resources": [],
            "current_step": "research_failed",
            "error": str(e),
        }
