"""
FastAPI server for StudyFlow AI.

Provides REST endpoints for the Gradio frontend to interact with the agent system.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import (
    GoalInput,
    DiagnosticSubmission,
    ProgressUpdate,
    SessionResponse,
    PlanResponse,
    ProgressResponse,
    DiagnosticQuestion,
)
from backend.models.database import init_db, save_session, get_session
from backend.services.session import (
    create_session,
    get_session as get_mem_session,
    update_session,
)
from backend.services.llm_client import generate_json
from agents.graph import create_study_plan, check_progress

logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting StudyFlow AI server...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Seed Qdrant with sample resources
    try:
        from rag.indexer import seed_from_file
        count = seed_from_file()
        logger.info(f"✅ Seeded {count} resources into Qdrant")
    except Exception as e:
        logger.warning(f"⚠️ Could not seed Qdrant: {e}")

    yield

    logger.info("👋 Shutting down StudyFlow AI server")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="StudyFlow AI",
    description="AI-powered personalized study plan generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Diagnostic Question Generator ──────────────────────────────────────────

DIAGNOSTIC_PROMPT = """Generate 4 diagnostic questions to assess a learner's level for this goal:

**Goal:** {goal}

The questions should help determine:
1. Their current knowledge level (what do they already know?)
2. Their learning style preference
3. Any prerequisites they may be missing
4. Their motivation and commitment

Return as JSON:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "category": "knowledge|style|prerequisites|motivation"
        }}
    ]
}}
"""


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "StudyFlow AI"}


@app.post("/api/start-session", response_model=SessionResponse)
async def start_session(goal_input: GoalInput):
    """
    Start a new study session.

    Creates a session, generates diagnostic questions for the learner.
    """
    try:
        # Create session
        session = create_session(goal_input)

        # Generate diagnostic questions using LLM
        messages = [
            {"role": "system", "content": "You are an educational assessment expert."},
            {"role": "user", "content": DIAGNOSTIC_PROMPT.format(goal=goal_input.goal)},
        ]

        result = generate_json(messages)
        questions = [
            DiagnosticQuestion(**q) for q in result.get("questions", [])
        ]

        session.diagnostic_questions = questions
        update_session(session)

        # Persist to SQLite
        save_session(session.id, goal=goal_input.goal, status="diagnostic")

        return SessionResponse(
            session_id=session.id,
            diagnostic_questions=questions,
            message=f"Welcome! Let's assess your current level for: {goal_input.goal}",
        )

    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-plan", response_model=PlanResponse)
async def create_plan(submission: DiagnosticSubmission):
    """
    Create a personalized study plan based on diagnostic answers.

    Runs the full agent pipeline: Planning → Research → Coaching.
    """
    try:
        session = get_mem_session(submission.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Store diagnostic answers
        session.diagnostic_answers = submission.answers
        update_session(session)

        # Run the agent pipeline
        result = create_study_plan(
            goal=session.goal_input.goal,
            available_hours=session.goal_input.available_hours_per_week,
            deadline_weeks=session.goal_input.deadline_weeks,
            diagnostic_answers=[a.model_dump() for a in submission.answers],
        )

        # Build the response
        study_plan_data = result.get("study_plan", {})
        task_schedule = result.get("task_schedule", [])
        resources = result.get("resources", [])

        # Merge tasks and resources into milestones
        milestones = study_plan_data.get("milestones", [])
        for milestone in milestones:
            mid = milestone.get("id", "")
            # Attach tasks
            milestone["tasks"] = [
                t for t in task_schedule if t.get("milestone_id") == mid
            ]
            # Attach resources
            for mr in resources:
                if mr.get("milestone_id") == mid:
                    milestone["resources"] = mr.get("resources", [])

        from backend.models.schemas import StudyPlan, DifficultyLevel

        plan = StudyPlan(
            goal=session.goal_input.goal,
            level=DifficultyLevel(result.get("assessed_level", "beginner")),
            total_weeks=study_plan_data.get("total_weeks", 4),
            hours_per_week=session.goal_input.available_hours_per_week,
            status="active",
        )

        session.study_plan = plan
        update_session(session)

        # Persist
        save_session(
            submission.session_id,
            answers=[a.model_dump() for a in submission.answers],
            plan={
                "study_plan": study_plan_data,
                "task_schedule": task_schedule,
                "resources": resources,
            },
            status="active",
        )

        return PlanResponse(
            session_id=submission.session_id,
            study_plan=plan,
            message="Your personalized study plan is ready! 🎉",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update-progress", response_model=ProgressResponse)
async def update_progress(progress: ProgressUpdate):
    """
    Update task progress and get coaching feedback.

    Runs the Progress Agent to analyze completion and potentially adapt the plan.
    """
    try:
        session = get_mem_session(progress.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get stored plan data
        db_session = get_session(progress.session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session data not found")

        plan_data = db_session.get_plan()
        study_plan = plan_data.get("study_plan", {})
        task_schedule = plan_data.get("task_schedule", [])

        # Build task status map
        task_statuses = {
            update.task_id: update.status.value
            for update in progress.task_updates
        }

        # Run progress check
        result = check_progress(
            goal=session.goal_input.goal,
            study_plan=study_plan,
            task_schedule=task_schedule,
            task_statuses=task_statuses,
            user_feedback=progress.user_feedback or "",
        )

        return ProgressResponse(
            session_id=progress.session_id,
            message="Progress updated!",
            plan_adapted=result.get("plan_adapted", False),
            coaching_message=result.get("coaching_message", "Keep going! 💪"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
