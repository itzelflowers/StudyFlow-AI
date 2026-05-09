"""
Session management service.
"""

from __future__ import annotations

import uuid
from typing import Optional

from backend.models.schemas import Session, GoalInput


# In-memory session store (backed by SQLite for persistence)
_sessions: dict[str, Session] = {}


def create_session(goal_input: GoalInput) -> Session:
    """Create a new study session."""
    session = Session(
        id=str(uuid.uuid4()),
        goal_input=goal_input,
    )
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> Optional[Session]:
    """Retrieve a session by ID."""
    return _sessions.get(session_id)


def update_session(session: Session) -> Session:
    """Update an existing session."""
    _sessions[session.id] = session
    return session


def list_sessions() -> list[Session]:
    """List all active sessions."""
    return list(_sessions.values())
