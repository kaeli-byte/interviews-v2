"""Sessions and interview-context schemas."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    interview_context_id: str
    agent_id: Optional[str] = None


class CreateContextRequest(BaseModel):
    resume_profile_id: str
    job_profile_id: str
    agent_id: str
    custom_instructions: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    interview_context_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None


class UpdateSessionSetupRequest(BaseModel):
    resume_profile_id: str
    job_profile_id: str
    agent_id: str
    custom_instructions: Optional[str] = None


class DocumentSnapshot(BaseModel):
    document_id: str
    type: str
    source_type: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    source_url: Optional[str] = None
    parse_status: Optional[str] = None
    created_at: Optional[str] = None


class ProfileSnapshot(BaseModel):
    profile_id: str
    type: str
    document_id: Optional[str] = None
    name: Optional[str] = None
    headline: Optional[str] = None
    skills: List[str] = []
    experience: List[dict] = []
    company: Optional[str] = None
    role: Optional[str] = None
    requirements: Any = []
    structured_json: Dict[str, Any] = {}
    summary_text: Optional[str] = None
    created_at: str


class AgentSnapshot(BaseModel):
    agent_id: str
    name: str
    description: Optional[str] = None
    prompt_template: str
    behavior_settings: Dict[str, Any] = {}
    rubric_definition: List[dict] = []
    version: int


class InterviewContextResponse(BaseModel):
    context_id: str
    user_id: str
    resume_profile_id: str
    job_profile_id: str
    agent_id: str
    custom_instructions: Optional[str] = None
    match_analysis: Dict[str, Any] = {}
    resume_profile: ProfileSnapshot
    job_profile: ProfileSnapshot
    resume_document: Optional[DocumentSnapshot] = None
    job_document: Optional[DocumentSnapshot] = None
    agent: AgentSnapshot
    startup_prompt: str
    created_at: str


class SessionResponse(BaseModel):
    session_id: str
    reconnect_token: str
    user_id: str
    interview_context_id: str
    agent_id: Optional[str] = None
    state: str
    created_at: str
    editable: bool = False
    context: Optional[InterviewContextResponse] = None


class SessionListItemResponse(BaseModel):
    session_id: str
    interview_context_id: Optional[str] = None
    agent_id: Optional[str] = None
    state: str
    created_at: Optional[str] = None
    editable: bool = False
    candidate_name: Optional[str] = None
    target_role: Optional[str] = None
    company: Optional[str] = None
    agent_name: Optional[str] = None


class InterviewPrepResponse(BaseModel):
    session_id: str
    context_id: Optional[str] = None
    startup_prompt: str
    agent: Dict[str, Any]
    resume_profile: Dict[str, Any]
    job_profile: Dict[str, Any]
    match_analysis: Dict[str, Any]


class CreateInterviewPrepRequest(BaseModel):
    context_id: str
    agent_id: Optional[str] = None
