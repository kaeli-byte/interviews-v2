"""Documents Pydantic schemas."""
from typing import Optional

from pydantic import BaseModel, HttpUrl


class ResumeUploadResponse(BaseModel):
    document_id: str
    filename: str
    type: str
    file_type: str
    size: int
    source_type: str
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None
    parse_status: str
    created_at: str


class JobDescriptionTextRequest(BaseModel):
    text: str


class JobDescriptionUrlRequest(BaseModel):
    url: HttpUrl


class JobDescriptionResponse(BaseModel):
    document_id: str
    filename: str
    type: str
    source_type: str
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None
    parse_status: str
    content_preview: str
    created_at: str


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    type: str
    source_type: Optional[str] = None
    file_type: str
    created_at: str


class DeleteResponse(BaseModel):
    success: bool
