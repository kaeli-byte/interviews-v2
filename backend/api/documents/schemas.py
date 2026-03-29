"""Documents Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    document_id: str
    filename: str
    type: str
    file_type: str
    size: int
    created_at: str


class JobDescriptionRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    document_id: str
    content_preview: str
    source_type: str
    filename: str


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    type: str
    file_type: str
    created_at: str


class DeleteResponse(BaseModel):
    success: bool