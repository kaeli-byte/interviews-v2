"""Sessions service - session and interview context management."""
import uuid
from datetime import datetime
from typing import Optional

# In-memory storage (for MVP)
sessions_db: dict = {}
interview_contexts_db: dict = {}

# Session state constants
SESSION_STATE_PENDING = "pending"
SESSION_STATE_ACTIVE = "active"
SESSION_STATE_PAUSED = "paused"
SESSION_STATE_ENDED = "ended"

VALID_TRANSITIONS = {
    SESSION_STATE_PENDING: [SESSION_STATE_ACTIVE],
    SESSION_STATE_ACTIVE: [SESSION_STATE_PAUSED, SESSION_STATE_ENDED],
    SESSION_STATE_PAUSED: [SESSION_STATE_ACTIVE, SESSION_STATE_ENDED],
    SESSION_STATE_ENDED: []
}


# Interview Contexts
async def create_interview_context(
    user_id: str,
    resume_profile_id: str,
    job_profile_id: str,
    custom_instructions: Optional[str] = None
) -> dict:
    """Create an interview context."""
    context_id = uuid.uuid4().hex
    context = {
        "context_id": context_id,
        "user_id": user_id,
        "resume_profile_id": resume_profile_id,
        "job_profile_id": job_profile_id,
        "custom_instructions": custom_instructions,
        "created_at": datetime.utcnow().isoformat()
    }
    interview_contexts_db[context_id] = context
    return context


def get_interview_context(context_id: str) -> Optional[dict]:
    """Get an interview context by ID."""
    return interview_contexts_db.get(context_id)


def get_interview_contexts_by_user(user_id: str) -> list:
    """Get all interview contexts for a user."""
    return [
        ctx for ctx in interview_contexts_db.values()
        if ctx.get("user_id") == user_id
    ]


# Sessions
def is_valid_transition(current_state: str, new_state: str) -> bool:
    """Check if state transition is valid."""
    return new_state in VALID_TRANSITIONS.get(current_state, [])


async def create_session(
    user_id: str,
    interview_context_id: str,
    agent_id: Optional[str] = None
) -> dict:
    """Create a new interview session."""
    session_id = uuid.uuid4().hex
    reconnect_token = uuid.uuid4().hex

    session = {
        "session_id": session_id,
        "reconnect_token": reconnect_token,
        "user_id": user_id,
        "interview_context_id": interview_context_id,
        "agent_id": agent_id,
        "state": SESSION_STATE_PENDING,
        "transcript": [],
        "created_at": datetime.utcnow().isoformat()
    }
    sessions_db[session_id] = session
    return session


def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    return sessions_db.get(session_id)


def get_sessions_by_user(user_id: str) -> list:
    """Get all sessions for a user."""
    return [
        s for s in sessions_db.values()
        if s.get("user_id") == user_id
    ]


def update_session_state(session_id: str, new_state: str, user_id: str) -> Optional[dict]:
    """Update session state with validation."""
    session = sessions_db.get(session_id)
    if not session:
        return None

    if session.get("user_id") != user_id:
        return None

    if not is_valid_transition(session["state"], new_state):
        return None

    session["state"] = new_state
    return session


def update_session(session_id: str, user_id: str, **updates) -> Optional[dict]:
    """Update session fields."""
    session = sessions_db.get(session_id)
    if not session:
        return None

    if session.get("user_id") != user_id:
        return None

    for key, value in updates.items():
        if key not in ["session_id", "user_id", "created_at"]:
            session[key] = value

    return session


def delete_session(session_id: str, user_id: str) -> bool:
    """Delete a session."""
    session = sessions_db.get(session_id)
    if not session:
        return False

    if session.get("user_id") != user_id:
        return False

    del sessions_db[session_id]
    return True