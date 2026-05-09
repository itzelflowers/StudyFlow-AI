"""
SQLite database setup for persistent session storage.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./studyflow.db")


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    """Stores user sessions and their study plans."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    goal = Column(Text, nullable=True)
    diagnostic_answers = Column(Text, default="[]")  # JSON
    study_plan = Column(Text, default="{}")  # JSON
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def set_plan(self, plan_dict: dict) -> None:
        self.study_plan = json.dumps(plan_dict)
        self.updated_at = datetime.now()

    def get_plan(self) -> dict:
        try:
            return json.loads(self.study_plan) if self.study_plan else {}
        except json.JSONDecodeError:
            return {}

    def set_answers(self, answers: list[dict]) -> None:
        self.diagnostic_answers = json.dumps(answers)

    def get_answers(self) -> list[dict]:
        try:
            return json.loads(self.diagnostic_answers) if self.diagnostic_answers else []
        except json.JSONDecodeError:
            return []


# ─── Engine & Session Factory ────────────────────────────────────────────────

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def save_session(session_id: str, goal: str = None, answers: list = None,
                 plan: dict = None, status: str = None) -> SessionRecord:
    """Create or update a session record."""
    db = get_db()
    try:
        record = db.query(SessionRecord).filter_by(id=session_id).first()

        if record is None:
            record = SessionRecord(id=session_id)
            db.add(record)

        if goal is not None:
            record.goal = goal
        if answers is not None:
            record.set_answers(answers)
        if plan is not None:
            record.set_plan(plan)
        if status is not None:
            record.status = status

        record.updated_at = datetime.now()
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_session(session_id: str) -> Optional[SessionRecord]:
    """Retrieve a session record."""
    db = get_db()
    try:
        return db.query(SessionRecord).filter_by(id=session_id).first()
    finally:
        db.close()
