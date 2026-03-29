"""Profiles service - AI-powered profile extraction."""
import json
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from backend.api.documents import service as doc_service
from backend.config import settings

logger = logging.getLogger(__name__)

# In-memory profile storage
profiles_db: dict = {}


async def extract_with_gemini(content: str, prompt: str, response_schema: dict) -> dict:
    """Extract structured data using Gemini API."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    full_prompt = f"""{prompt}

Return ONLY valid JSON matching this schema. Do not include any explanation or markdown formatting.

Content to analyze:
---
{content}
---
"""

    try:
        response = client.models.generate_content(
            model=settings.MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        )

        if response.text:
            return json.loads(response.text)
        else:
            raise ValueError("Gemini returned empty response")
    except Exception as e:
        logger.error(f"Gemini extraction error: {e}")
        raise ValueError(f"Profile extraction failed: {str(e)}")


async def extract_resume_profile(user_id: str, document_id: str) -> dict:
    """Extract candidate profile from resume."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise ValueError("Document not found")

    if doc.get("user_id") != user_id:
        raise ValueError("Not authorized to access this document")

    if doc["type"] != "resume":
        raise ValueError("Document is not a resume")

    # Read resume content
    file_path = Path(doc["file_path"])
    if doc["file_type"] == "PDF":
        content = doc_service.read_pdf_content(file_path)
    elif doc["file_type"] == "DOCX":
        content = doc_service.read_docx_content(file_path)
    else:
        raise ValueError("Unsupported file type")

    if not content.strip():
        raise ValueError("Resume appears to be empty")

    # Schema for structured output
    resume_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "headline": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company": {"type": "string"},
                        "duration": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["title", "company", "duration", "description"]
                }
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": "string"},
                        "year": {"type": "string"}
                    },
                    "required": ["institution", "degree"]
                }
            },
            "confidence_score": {"type": "number"}
        },
        "required": ["name", "headline", "skills", "experience", "education", "confidence_score"]
    }

    prompt = """Extract candidate information from this resume as JSON with the following fields:
- name: Full name of the candidate
- headline: Professional headline/title (e.g., "Senior Software Engineer")
- skills: Array of technical and soft skills
- experience: Array of work experiences with title, company, duration, description
- education: Array of education entries with institution, degree, year
- confidence_score: Number 0-100 indicating how confident you are in the extraction quality"""

    extracted_data = await extract_with_gemini(content, prompt, resume_schema)

    # Store profile
    import uuid
    from datetime import datetime

    profile_id = uuid.uuid4().hex
    profile = {
        "profile_id": profile_id,
        "type": "resume",
        "document_id": document_id,
        "name": extracted_data.get("name", ""),
        "headline": extracted_data.get("headline", ""),
        "skills": extracted_data.get("skills", []),
        "experience": extracted_data.get("experience", []),
        "education": extracted_data.get("education", []),
        "confidence_score": extracted_data.get("confidence_score", 0),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id
    }
    profiles_db[profile_id] = profile
    return profile


async def extract_job_profile(user_id: str, document_id: str) -> dict:
    """Extract job profile from job description."""
    from datetime import datetime
    import uuid

    doc = doc_service.get_document(document_id)
    if not doc:
        raise ValueError("Document not found")

    if doc.get("user_id") != user_id:
        raise ValueError("Not authorized to access this document")

    if doc["type"] != "job_description":
        raise ValueError("Document is not a job description")

    # Read JD content
    content = doc.get("content", "")
    if not content:
        file_path = Path(doc["file_path"])
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    if not content.strip():
        raise ValueError("Job description appears to be empty")

    jd_schema = {
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "role": {"type": "string"},
            "requirements": {"type": "array", "items": {"type": "string"}},
            "nice_to_have": {"type": "array", "items": {"type": "string"}},
            "responsibilities": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["company", "role", "requirements", "nice_to_have", "responsibilities"]
    }

    prompt = """Extract job description information as JSON with the following fields:
- company: Company name
- role: Job title/role
- requirements: Array of must-have requirements
- nice_to_have: Array of nice-to-have qualifications
- responsibilities: Array of key responsibilities"""

    extracted_data = await extract_with_gemini(content, prompt, jd_schema)

    profile_id = uuid.uuid4().hex
    profile = {
        "profile_id": profile_id,
        "type": "job_description",
        "document_id": document_id,
        "company": extracted_data.get("company", ""),
        "role": extracted_data.get("role", ""),
        "requirements": extracted_data.get("requirements", []),
        "nice_to_have": extracted_data.get("nice_to_have", []),
        "responsibilities": extracted_data.get("responsibilities", []),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id
    }
    profiles_db[profile_id] = profile
    return profile


def get_profile(profile_id: str) -> Optional[dict]:
    """Get a profile by ID."""
    return profiles_db.get(profile_id)


def get_profiles_by_user(user_id: str) -> list:
    """Get all profiles for a user."""
    return [p for p in profiles_db.values() if p.get("user_id") == user_id]