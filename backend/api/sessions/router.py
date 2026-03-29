"""Sessions router."""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.sessions import schemas as session_schemas
from backend.api.sessions import service as session_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Re-export constants for websocket handlers
SESSION_STATE_ACTIVE = session_service.SESSION_STATE_ACTIVE
SESSION_STATE_PAUSED = session_service.SESSION_STATE_PAUSED
SESSION_STATE_ENDED = session_service.SESSION_STATE_ENDED
sessions_db = session_service.sessions_db


@router.post("", response_model=session_schemas.SessionResponse)
async def create_session(
    data: session_schemas.CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new interview session."""
    user_id = current_user["id"]

    session = await session_service.create_session(
        user_id=user_id,
        interview_context_id=data.interview_context_id,
        agent_id=data.agent_id
    )
    return session


@router.get("/{session_id}", response_model=session_schemas.SessionResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get a session by ID."""
    user_id = current_user["id"]

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return session


@router.patch("/{session_id}", response_model=session_schemas.SessionResponse)
async def update_session(
    session_id: str,
    data: session_schemas.UpdateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a session."""
    user_id = current_user["id"]

    updates = {}
    if data.interview_context_id:
        updates["interview_context_id"] = data.interview_context_id
    if data.agent_id:
        updates["agent_id"] = data.agent_id

    session = session_service.update_session(session_id, user_id, **updates)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session."""
    user_id = current_user["id"]

    success = session_service.delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    return {"success": True}