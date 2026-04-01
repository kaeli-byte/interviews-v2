"""Document ingestion service backed by Supabase Storage and Postgres."""
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from backend.config import settings
from backend.db import queries as db
from backend.api.documents.service_parser import (
    extract_resume_hints,
    normalize_extracted_text,
    parse_document_content,
)


async def upload_bytes_to_storage(storage_path: str, content: bytes, mime_type: str) -> None:
    """Upload file bytes to Supabase Storage."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Supabase storage is not configured")

    url = (
        f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/"
        f"{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
    )
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": mime_type,
        "x-upsert": "true",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, content=content)

    if response.status_code >= 300:
        raise ValueError(f"Storage upload failed: {response.text}")


async def _create_document(
    *,
    user_id: str,
    kind: str,
    source_type: str,
    filename: Optional[str],
    mime_type: Optional[str],
    storage_path: Optional[str],
    source_url: Optional[str],
    raw_text: str,
    content: Optional[dict] = None,
) -> dict:
    normalized_text = normalize_extracted_text(raw_text)
    document = await db.create_document(
        user_id=user_id,
        kind=kind,
        source_type=source_type,
        filename=filename,
        mime_type=mime_type,
        storage_path=storage_path,
        source_url=source_url,
        raw_text=normalized_text,
        content=content,
        parse_status="parsed",
    )
    return {
        "document_id": document["id"],
        "filename": document["filename"],
        "type": document["kind"],
        "source_type": document["source_type"],
        "mime_type": document["mime_type"],
        "storage_path": document["storage_path"],
        "parse_status": document["parse_status"],
        "created_at": document["created_at"],
    }


async def upload_resume(user_id: str, filename: str, content: bytes) -> dict:
    """Upload and parse a resume."""
    file_ext = Path(filename).suffix.lower()
    if file_ext not in {".pdf", ".docx"}:
        raise ValueError("Invalid file type. Please upload a PDF or DOCX file.")

    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parsed_text = parse_document_content(filename, content)
    if not parsed_text.strip():
        raise ValueError("Resume could not be parsed")
    structured = extract_resume_hints(parsed_text)

    storage_path = f"resumes/{user_id}/{uuid.uuid4().hex}{file_ext}"
    await upload_bytes_to_storage(storage_path, content, mime_type)

    result = await _create_document(
        user_id=user_id,
        kind="resume",
        source_type="file",
        filename=filename,
        mime_type=mime_type,
        storage_path=storage_path,
        source_url=None,
        raw_text=parsed_text,
        content=structured,
    )
    result["file_type"] = file_ext[1:].upper()
    result["size"] = len(content)
    return result


async def upload_job_description_file(user_id: str, filename: str, content: bytes) -> dict:
    """Upload a JD from PDF or DOCX."""
    file_ext = Path(filename).suffix.lower()
    if file_ext not in {".pdf", ".docx"}:
        raise ValueError("Invalid file type. Please upload a PDF or DOCX file.")

    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parsed_text = parse_document_content(filename, content)
    if not parsed_text.strip():
        raise ValueError("Job description could not be parsed")

    storage_path = f"job-descriptions/{user_id}/{uuid.uuid4().hex}{file_ext}"
    await upload_bytes_to_storage(storage_path, content, mime_type)

    result = await _create_document(
        user_id=user_id,
        kind="job_description",
        source_type="file",
        filename=filename,
        mime_type=mime_type,
        storage_path=storage_path,
        source_url=None,
        raw_text=parsed_text,
    )
    result["content_preview"] = parsed_text[:200]
    return result


async def upload_job_description_text(user_id: str, text: str) -> dict:
    """Persist pasted JD text."""
    normalized_text = normalize_extracted_text(text)
    if not normalized_text:
        raise ValueError("Job description text is required")

    result = await _create_document(
        user_id=user_id,
        kind="job_description",
        source_type="text",
        filename="job-description.txt",
        mime_type="text/plain",
        storage_path=None,
        source_url=None,
        raw_text=normalized_text,
    )
    result["content_preview"] = normalized_text[:200]
    return result


async def upload_job_description_url(user_id: str, url: str) -> dict:
    """Fetch, normalize, and persist JD text from a URL."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    normalized_text = normalize_extracted_text(text)
    if not normalized_text:
        raise ValueError("No readable content found at the provided URL")

    result = await _create_document(
        user_id=user_id,
        kind="job_description",
        source_type="url",
        filename="job-description-url.txt",
        mime_type="text/plain",
        storage_path=None,
        source_url=url,
        raw_text=normalized_text,
    )
    result["content_preview"] = normalized_text[:200]
    return result


async def list_documents(user_id: str) -> list:
    """List documents for a user."""
    documents = await db.get_documents_by_user(user_id)
    return [
        {
            "document_id": doc["id"],
            "filename": doc["filename"],
            "type": doc["kind"],
            "source_type": doc["source_type"],
            "file_type": Path(doc["filename"] or "").suffix.replace(".", "").upper(),
            "created_at": doc["created_at"],
        }
        for doc in documents
    ]


async def get_document(document_id: str) -> Optional[dict]:
    """Get a single document."""
    return await db.get_document_by_id(document_id)


async def delete_document(document_id: str, user_id: str) -> bool:
    """Delete a document if it belongs to the current user."""
    document = await db.get_document_by_id(document_id)
    if not document or document["user_id"] != user_id:
        return False
    return await db.delete_document(document_id)
