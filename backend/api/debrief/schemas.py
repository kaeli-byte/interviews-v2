"""Debrief Pydantic schemas."""
from typing import List, Optional
from pydantic import BaseModel


class GenerateDebriefRequest(BaseModel):
    session_id: str
    custom_rubric: Optional[List[dict]] = None


class DebriefResponse(BaseModel):
    debrief_id: str
    session_id: str
    overall_score: int
    strengths: List[str]
    areas_for_improvement: List[str]
    detailed_feedback: dict
    suggested_focus: List[str]
    created_at: str