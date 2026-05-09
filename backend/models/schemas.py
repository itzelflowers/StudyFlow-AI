"""
Pydantic schemas for StudyFlow AI data models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    STUCK = "stuck"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ADAPTED = "adapted"
    COMPLETED = "completed"


# ─── Request Schemas ──────────────────────────────────────────────────────────

class GoalInput(BaseModel):
    """User's initial learning goal."""
    goal: str = Field(..., description="The learning goal, e.g. 'I want to learn calculus'")
    available_hours_per_week: float = Field(
        default=10.0, ge=1.0, le=80.0,
        description="Hours available for study per week"
    )
    deadline_weeks: Optional[int] = Field(
        default=None, ge=1, le=52,
        description="Optional target deadline in weeks"
    )


class DiagnosticAnswer(BaseModel):
    """User's answer to a diagnostic question."""
    question_id: str
    answer: str


class DiagnosticSubmission(BaseModel):
    """All diagnostic answers from the user."""
    session_id: str
    answers: list[DiagnosticAnswer]


class TaskUpdate(BaseModel):
    """Update the status of a task."""
    task_id: str
    status: TaskStatus
    notes: Optional[str] = None


class ProgressUpdate(BaseModel):
    """Batch progress update."""
    session_id: str
    task_updates: list[TaskUpdate]
    user_feedback: Optional[str] = Field(
        default=None,
        description="Optional feedback like 'this is too hard' or 'I want to go faster'"
    )


# ─── Data Schemas ─────────────────────────────────────────────────────────────

class DiagnosticQuestion(BaseModel):
    """A diagnostic question to assess the learner's level."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    question: str
    options: list[str]
    category: str = "general"


class Resource(BaseModel):
    """A learning resource recommendation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    url: str
    resource_type: str = Field(description="video, article, exercise, book, course")
    difficulty: DifficultyLevel
    description: str
    estimated_minutes: int = 30
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class Task(BaseModel):
    """A concrete study task."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    milestone_id: str
    day: int = Field(description="Day number in the schedule")
    estimated_minutes: int = 30
    status: TaskStatus = TaskStatus.PENDING
    resources: list[Resource] = []
    notes: Optional[str] = None


class Milestone(BaseModel):
    """A milestone in the study plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    order: int
    week: int
    tasks: list[Task] = []
    resources: list[Resource] = []
    is_completed: bool = False


class StudyPlan(BaseModel):
    """The complete study plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str
    level: DifficultyLevel
    total_weeks: int
    hours_per_week: float
    milestones: list[Milestone] = []
    status: PlanStatus = PlanStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ─── Session Schema ──────────────────────────────────────────────────────────

class Session(BaseModel):
    """A user study session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_input: Optional[GoalInput] = None
    diagnostic_questions: list[DiagnosticQuestion] = []
    diagnostic_answers: list[DiagnosticAnswer] = []
    study_plan: Optional[StudyPlan] = None
    created_at: datetime = Field(default_factory=datetime.now)


# ─── Response Schemas ─────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    """Response after creating a session."""
    session_id: str
    diagnostic_questions: list[DiagnosticQuestion]
    message: str


class PlanResponse(BaseModel):
    """Response with the generated study plan."""
    session_id: str
    study_plan: StudyPlan
    message: str


class ProgressResponse(BaseModel):
    """Response after updating progress."""
    session_id: str
    message: str
    plan_adapted: bool = False
    study_plan: Optional[StudyPlan] = None
    coaching_message: Optional[str] = None
