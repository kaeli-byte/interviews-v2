"""Main API router."""
from fastapi import APIRouter

from backend.api.auth import router as auth_router
from backend.api.documents import router as documents_router
from backend.api.profiles import router as profiles_router
from backend.api.sessions import router as sessions_router
from backend.api.interview_contexts import router as interview_contexts_router
from backend.api.agents import router as agents_router
from backend.api.debrief import router as debrief_router

# Create main router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router.router)
api_router.include_router(documents_router.router)
api_router.include_router(profiles_router.router)
api_router.include_router(sessions_router.router)
api_router.include_router(interview_contexts_router.router)
api_router.include_router(agents_router.router)
api_router.include_router(debrief_router.router)