"""Document service - handles file processing and storage."""
import uuid
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup


# In-memory document storage (for MVP - use database in production)
documents_db: dict = {}


def get_user_dir(user_id: str) -> Path:
    """Get or create user's upload directory."""
    from backend.config import settings
    user_dir = settings.UPLOADS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def read_pdf_content(file_path: Path) -> str:
    """Extract text from PDF file using pypdf."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")


def read_docx_content(file_path: Path) -> str:
    """Extract text from DOCX file using python-docx."""
    from docx import Document
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {str(e)}")


async def upload_resume(user_id: str, filename: str, content: bytes) -> dict:
    """Upload a resume document."""
    from datetime import datetime

    allowed_extensions = {".pdf", ".docx"}
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{filename}"

    user_dir = get_user_dir(user_id)
    resumes_dir = user_dir / "resumes"
    resumes_dir.mkdir(exist_ok=True)
    file_path = resumes_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    doc_id = uuid.uuid4().hex
    document = {
        "document_id": doc_id,
        "filename": filename,
        "stored_filename": safe_filename,
        "type": "resume",
        "file_type": file_ext[1:].upper(),
        "size": len(content),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "file_path": str(file_path)
    }
    documents_db[doc_id] = document
    return document


async def upload_job_description(user_id: str, text: Optional[str] = None, url: Optional[str] = None) -> dict:
    """Upload a job description from text or URL."""
    from datetime import datetime

    if not text and not url:
        raise ValueError("Either 'text' or 'url' must be provided")

    if text and url:
        raise ValueError("Provide either 'text' or 'url', not both")

    # Fetch content from URL if provided
    if url:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        source_type = "url"
    else:
        source_type = "text"

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"jd_{timestamp}.txt"

    user_dir = get_user_dir(user_id)
    jd_dir = user_dir / "job-descriptions"
    jd_dir.mkdir(exist_ok=True)
    file_path = jd_dir / safe_filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    doc_id = uuid.uuid4().hex
    content_preview = text[:200] + "..." if len(text) > 200 else text

    document = {
        "document_id": doc_id,
        "filename": safe_filename,
        "type": "job_description",
        "source_type": source_type,
        "content": text,
        "content_preview": content_preview,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "file_path": str(file_path)
    }
    documents_db[doc_id] = document

    return {
        "document_id": doc_id,
        "content_preview": content_preview,
        "source_type": source_type,
        "filename": safe_filename
    }


def list_documents(user_id: str) -> list:
    """List all documents for a user."""
    return [
        {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "type": doc["type"],
            "file_type": doc.get("file_type", ""),
            "created_at": doc["created_at"]
        }
        for doc in documents_db.values()
        if doc.get("user_id") == user_id
    ]


def get_document(document_id: str) -> Optional[dict]:
    """Get a document by ID."""
    return documents_db.get(document_id)


def delete_document(document_id: str, user_id: str) -> bool:
    """Delete a document. Returns True if successful."""
    if document_id not in documents_db:
        return False

    doc = documents_db[document_id]
    if doc.get("user_id") != user_id:
        return False

    file_path = Path(doc.get("file_path", ""))
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    del documents_db[document_id]
    return True