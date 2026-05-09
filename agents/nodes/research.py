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

RESEARCH_SYSTEM_PROMPT = """You are an expert educational resource curator. Your role is to find 
and recommend the best learning resources for each study milestone.

You should recommend a mix of:
- Free online courses and tutorials (Khan Academy, MIT OCW, Coursera, etc.)
- YouTube videos from reputable educators
- Interactive exercises and practice problems
- Textbooks and reading materials
- Online tools and calculators

IMPORTANT RULES:
- Only recommend well-known, reputable resources
- Include a mix of resource types (video, text, interactive)
- Match resource difficulty to the learner's level
- Prioritize FREE resources
- Include estimated time to complete each resource
- For mathematics, prioritize Khan Academy, 3Blue1Brown, MIT OCW, Paul's Online Math Notes
"""

RESEARCH_USER_PROMPT = """Find learning resources for the following study plan:

**Overall Goal:** {goal}
**Learner Level:** {level}
**Milestones:**
{milestones}

For each milestone, recommend 3-5 high-quality resources. Return as JSON:
{{
    "milestone_resources": [
        {{
            "milestone_id": "m1",
            "resources": [
                {{
                    "title": "Resource title",
                    "url": "https://...",
                    "resource_type": "video|article|exercise|course|book|tool",
                    "difficulty": "beginner|intermediate|advanced",
                    "description": "Brief description of what this covers",
                    "estimated_minutes": 30,
                    "provider": "Khan Academy|YouTube|MIT OCW|etc"
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
        result = generate_json(messages, temperature=0.7)
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
