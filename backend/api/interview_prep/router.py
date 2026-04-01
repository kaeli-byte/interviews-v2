"""Interview prep router."""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.sessions import schemas as session_schemas
from backend.api.sessions import service as session_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/interview-prep", tags=["interview-prep"])


@router.get("/{session_id}", response_model=session_schemas.InterviewPrepResponse)
async def get_interview_prep(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get interview prep payload for an existing session."""
    prep = await session_service.get_interview_prep_for_session(session_id, current_user["id"])
    if not prep:
        raise HTTPException(status_code=404, detail="Interview prep not found")
    return prep


@router.post("", response_model=session_schemas.InterviewPrepResponse)
async def create_interview_prep(
    data: session_schemas.CreateInterviewPrepRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a session and return interview prep payload."""
    try:
        return await session_service.create_interview_prep_for_context(
            current_user["id"],
            data.context_id,
            data.agent_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)
