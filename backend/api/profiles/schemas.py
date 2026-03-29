"""Profiles Pydantic schemas."""
from typing import List, Optional
from pydantic import BaseModel


class ExtractResumeRequest(BaseModel):
    document_id: str


class ExtractJDRequest(BaseModel):
    document_id: str


class ResumeProfileResponse(BaseModel):
    profile_id: str
    type: str
    document_id: str
    name: str
    headline: str
    skills: List[str]
    experience: List[dict]
    education: List[dict]
    confidence_score: float
    created_at: str


class JobProfileResponse(BaseModel):
    profile_id: str
    type: str
    document_id: str
    company: str
    role: str
    requirements: List[str]
    nice_to_have: List[str]
    responsibilities: List[str]
    created_at: str