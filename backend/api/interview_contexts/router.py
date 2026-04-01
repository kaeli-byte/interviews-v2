"""Interview contexts router."""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.sessions import schemas as session_schemas
from backend.api.sessions import service as session_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/interview-contexts", tags=["interview-contexts"])


@router.post("", response_model=session_schemas.InterviewContextResponse)
async def create_interview_context(
    data: session_schemas.CreateContextRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create an interview context."""
    user_id = current_user["id"]

    context = await session_service.create_interview_context(
        user_id=user_id,
        resume_profile_id=data.resume_profile_id,
        job_profile_id=data.job_profile_id,
        agent_id=data.agent_id,
        custom_instructions=data.custom_instructions
    )
    return context


@router.get("", response_model=list[session_schemas.InterviewContextResponse])
async def list_interview_contexts(current_user: dict = Depends(get_current_user)):
    """List all interview contexts for the current user."""
    user_id = current_user["id"]
    return await session_service.get_interview_contexts_by_user(user_id)


@router.get("/{context_id}", response_model=session_schemas.InterviewContextResponse)
async def get_interview_context(context_id: str, current_user: dict = Depends(get_current_user)):
    """Get an interview context by ID."""
    user_id = current_user["id"]

    context = await session_service.get_interview_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview context not found")

    if context.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return context
