"""Sessions Pydantic schemas."""
from typing import List, Optional
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    interview_context_id: str
    agent_id: Optional[str] = None


class CreateContextRequest(BaseModel):
    resume_profile_id: str
    job_profile_id: str
    custom_instructions: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    reconnect_token: str
    user_id: str
    interview_context_id: str
    agent_id: Optional[str]
    state: str
    created_at: str


class UpdateSessionRequest(BaseModel):
    interview_context_id: Optional[str] = None
    agent_id: Optional[str] = None


class InterviewContextResponse(BaseModel):
    context_id: str
    user_id: str
    resume_profile_id: str
    job_profile_id: str
    custom_instructions: Optional[str]
    created_at: str