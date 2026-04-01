"""Profiles router."""
from fastapi import APIRouter, Depends, HTTPException

from backend.api.profiles import schemas as profile_schemas
from backend.api.profiles import service as profile_service
from backend.api.profiles.service_extractor import LLMTemporaryUnavailableError
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("/extract-from-resume", response_model=profile_schemas.ResumeProfileResponse)
async def extract_resume_profile(
    data: profile_schemas.ExtractResumeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extract candidate profile from resume using Gemini AI."""
    user_id = current_user["id"]

    try:
        profile = await profile_service.extract_resume_profile(user_id, data.document_id)
        return profile
    except LLMTemporaryUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extract-from-jd", response_model=profile_schemas.JobProfileResponse)
async def extract_job_profile(
    data: profile_schemas.ExtractJDRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extract job profile from job description using Gemini AI."""
    user_id = current_user["id"]

    try:
        profile = await profile_service.extract_job_profile(user_id, data.document_id)
        return profile
    except LLMTemporaryUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{profile_id}")
async def get_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    """Get a profile by ID."""
    user_id = current_user["id"]

    profile = await profile_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")

    return profile
