"""Debrief router."""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.debrief import schemas as debrief_schemas
from backend.api.debrief import service as debrief_service
from backend.api.sessions import service as session_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/debrief", tags=["debrief"])


@router.post("", response_model=debrief_schemas.DebriefResponse)
async def generate_debrief(
    data: debrief_schemas.GenerateDebriefRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate debrief for a completed session."""
    user_id = current_user["id"]

    # Get session
    session = await session_service.get_session(data.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get rubric (could be from agent or custom)
    rubric = data.custom_rubric or []

    # Generate debrief
    transcript = session.get("transcript", [])
    debrief = await debrief_service.generate_debrief(
        session_id=data.session_id,
        user_id=user_id,
        transcript=transcript,
        rubric=rubric
    )
    return debrief


@router.get("/history")
async def get_debrief_history(current_user: dict = Depends(get_current_user)):
    """Get all debriefs for the current user."""
    user_id = current_user["id"]
    return debrief_service.get_debriefs_by_user(user_id)


@router.get("/{session_id}", response_model=debrief_schemas.DebriefResponse)
async def get_session_debrief(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get debrief for a session."""
    user_id = current_user["id"]

    # Verify session ownership
    session = await session_service.get_session(session_id)
    if not session or session.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    debrief = debrief_service.get_debrief(session_id)
    if not debrief:
        raise HTTPException(status_code=404, detail="Debrief not found")

    return debrief


@router.post("/{session_id}/regenerate", response_model=debrief_schemas.DebriefResponse)
async def regenerate_debrief(
    session_id: str,
    data: debrief_schemas.GenerateDebriefRequest | None = None,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate debrief for a session."""
    user_id = current_user["id"]

    # Verify session ownership
    session = await session_service.get_session(session_id)
    if not session or session.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete existing and regenerate
    debrief_service.delete_debrief(session_id)

    rubric = data.custom_rubric if data else []
    transcript = session.get("transcript", [])
    debrief = await debrief_service.generate_debrief(
        session_id=session_id,
        user_id=user_id,
        transcript=transcript,
        rubric=rubric
    )
    return debrief
