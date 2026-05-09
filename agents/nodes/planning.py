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

PLANNING_SYSTEM_PROMPT = """You are an expert educational planner AI. Your role is to create 
personalized, structured study plans for learners.

Given a learning goal, the learner's self-assessment, and their available time, you must:
1. Assess their current level (beginner, intermediate, advanced)
2. Break the topic into logical milestones (3-6 milestones)
3. Estimate the time needed for each milestone
4. Ensure the plan is achievable within their available hours

IMPORTANT RULES:
- Be realistic about time estimates
- Start from fundamentals if the learner is a beginner
- Each milestone should build on the previous one
- Include both theory and practice in each milestone
- Focus on mathematics topics when relevant
"""

PLANNING_USER_PROMPT = """Create a study plan for the following learner:

**Goal:** {goal}
**Available Time:** {hours} hours per week
**Target Duration:** {deadline} weeks
**Diagnostic Responses:** {diagnostic}

Generate a structured study plan as JSON with this exact format:
{{
    "assessed_level": "beginner|intermediate|advanced",
    "total_weeks": <number>,
    "milestones": [
        {{
            "id": "m1",
            "title": "Milestone title",
            "description": "What the learner will achieve",
            "order": 1,
            "week": 1,
            "topics": ["topic1", "topic2"],
            "learning_objectives": ["objective1", "objective2"],
            "estimated_hours": <number>
        }}
    ],
    "plan_summary": "A brief overview of the entire plan"
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
        result = generate_json(messages, temperature=0.6)

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
