"""Profiles service - AI-powered structured analysis."""
import json
import logging
from typing import Any, Optional

from backend.api.documents import service as doc_service
from backend.db import queries as db
from backend.api.profiles.service_extractor import (
    JobExtractionModel,
    ResumeExtractionModel,
    ResumeRepairModel,
    build_job_input,
    build_resume_input,
    extract_with_gemini,
)

logger = logging.getLogger(__name__)


def _has_resume_detail(extracted: dict) -> bool:
    experience = extracted.get("experience", []) or []
    education = extracted.get("education", []) or []

    experience_has_detail = any(
        isinstance(item, dict) and (item.get("title") or item.get("company") or item.get("description"))
        for item in experience
    )
    education_has_detail = any(
        isinstance(item, dict) and (item.get("degree") or item.get("school") or item.get("field_of_study"))
        for item in education
    )
    return experience_has_detail or education_has_detail


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split()).strip()
    return " ".join(str(value).split()).strip()


def _normalize_resume_extracted(extracted: dict) -> dict:
    experience_items = []
    for item in extracted.get("experience", []) or []:
        if not isinstance(item, dict):
            continue
        bullets = [
            _clean_string(bullet)
            for bullet in (item.get("bullets", []) or [])
            if _clean_string(bullet)
        ]
        description = _clean_string(item.get("description")) or " ".join(bullets)
        normalized = {
            "title": _clean_string(item.get("title")),
            "company": _clean_string(item.get("company")),
            "location": _clean_string(item.get("location")),
            "start_date": _clean_string(item.get("start_date")),
            "end_date": _clean_string(item.get("end_date")),
            "description": description,
            "bullets": bullets,
        }
        if any(normalized.values()):
            experience_items.append(normalized)

    education_items = []
    for item in extracted.get("education", []) or []:
        if not isinstance(item, dict):
            continue
        normalized = {
            "degree": _clean_string(item.get("degree")),
            "school": _clean_string(item.get("school")),
            "field_of_study": _clean_string(item.get("field_of_study")),
            "graduation_year": _clean_string(item.get("graduation_year")),
        }
        if any(normalized.values()):
            education_items.append(normalized)

    return {
        "name": _clean_string(extracted.get("name")),
        "headline": _clean_string(extracted.get("headline")),
        "email": _clean_string(extracted.get("email")),
        "phone": _clean_string(extracted.get("phone")),
        "location": _clean_string(extracted.get("location")),
        "linkedin": _clean_string(extracted.get("linkedin")),
        "summary": _clean_string(extracted.get("summary")),
        "skills": [_clean_string(skill) for skill in (extracted.get("skills", []) or []) if _clean_string(skill)],
        "languages": [_clean_string(language) for language in (extracted.get("languages", []) or []) if _clean_string(language)],
        "experience": experience_items,
        "education": education_items,
    }


async def _extract_resume_with_repair(content: str, schema: dict, prompt: str) -> dict:
    try:
        return await extract_with_gemini(
            content,
            prompt,
            schema,
            response_model=ResumeExtractionModel,
        )
    except ValueError as exc:
        if "invalid structured output" not in str(exc):
            raise

        repair_prompt = """The previous resume extraction response was invalid and did not match the required schema.

Re-read the resume and return a corrected JSON object that matches the schema exactly.

Rules:
- Do not invent information.
- Use empty strings instead of null when a field is missing.
- Keep skills and languages as arrays of strings.
- Keep experience bullets as arrays of strings.
- Preserve dates exactly as written when available.
"""
        repaired = await extract_with_gemini(
            content,
            repair_prompt,
            schema,
            response_model=ResumeRepairModel,
        )
        return {
            "name": repaired.get("name") or "",
            "headline": repaired.get("headline") or "",
            "email": repaired.get("email") or "",
            "phone": repaired.get("phone") or "",
            "location": repaired.get("location") or "",
            "linkedin": repaired.get("linkedin") or "",
            "summary": repaired.get("summary") or "",
            "skills": repaired.get("skills") or [],
            "languages": repaired.get("languages") or [],
            "experience": repaired.get("experience") or [],
            "education": repaired.get("education") or [],
        }


async def _repair_resume_extracted(content: str, extracted: dict) -> dict:
    repair_schema = {
        "type": "object",
        "properties": {
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company": {"type": "string"},
                        "location": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "description": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "company", "location", "start_date", "end_date", "description", "bullets"],
                },
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "degree": {"type": "string"},
                        "school": {"type": "string"},
                        "field_of_study": {"type": "string"},
                        "graduation_year": {"type": "string"},
                    },
                    "required": ["degree", "school", "field_of_study", "graduation_year"],
                },
            },
        },
        "required": ["experience", "education"],
    }
    repair_prompt = f"""The first extraction found the candidate's top-level identity but failed to extract detailed resume chronology.

Existing extraction:
{json.dumps(extracted, ensure_ascii=True)}

Re-read the resume and repair only the experience and education arrays.

Rules:
- Do not invent employers, schools, or dates.
- Prefer partial truth over fabricated completeness.
- Use empty strings instead of null.
- Do not return empty objects.
- description should be a concise summary of what the candidate did in that role.
- bullets should preserve the key bullet points for each role as a string array.
"""
    repaired = await extract_with_gemini(
        content,
        repair_prompt,
        repair_schema,
        response_model=ResumeRepairModel,
    )
    merged = dict(extracted)
    merged["experience"] = repaired.get("experience", [])
    merged["education"] = repaired.get("education", [])
    return merged


async def _load_document_for_user(user_id: str, document_id: str) -> dict:
    document = await doc_service.get_document(document_id)
    if not document:
        raise ValueError("Document not found")
    if document["user_id"] != user_id:
        raise ValueError("Not authorized to access this document")
    return document


def _build_match_analysis(resume_profile: dict, job_profile: dict) -> dict:
    resume_skills = {skill.lower() for skill in resume_profile.get("skills", [])}
    requirements = {item.lower() for item in job_profile.get("requirements", [])}
    matched = sorted(requirement for requirement in requirements if requirement in resume_skills)
    gaps = sorted(requirement for requirement in requirements if requirement not in resume_skills)
    return {
        "matched_requirements": matched,
        "gap_requirements": gaps,
        "match_score": round((len(matched) / len(requirements)) * 100, 2) if requirements else 0,
        "candidate_strengths": resume_profile.get("skills", [])[:8],
    }


async def extract_resume_profile(user_id: str, document_id: str) -> dict:
    """Extract candidate profile from a parsed resume document."""
    document = await _load_document_for_user(user_id, document_id)
    if document["kind"] != "resume":
        raise ValueError("Document is not a resume")

    content = build_resume_input(document)
    if not content.strip():
        raise ValueError("Resume appears to be empty")

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "headline": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "location": {"type": "string"},
            "linkedin": {"type": "string"},
            "summary": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "languages": {"type": "array", "items": {"type": "string"}},
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company": {"type": "string"},
                        "location": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "description": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "company", "location", "start_date", "end_date", "description", "bullets"],
                },
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "degree": {"type": "string"},
                        "school": {"type": "string"},
                        "field_of_study": {"type": "string"},
                        "graduation_year": {"type": "string"},
                    },
                    "required": ["degree", "school", "field_of_study", "graduation_year"],
                },
            },
        },
        "required": [
            "name",
            "headline",
            "email",
            "phone",
            "location",
            "linkedin",
            "summary",
            "skills",
            "languages",
            "experience",
            "education",
        ],
    }
    prompt = """Extract a structured candidate profile from this resume.

Rules:
- Return name, headline, email, phone, location, linkedin, summary, skills, and languages when available.
- Return every experience item with title, company, location, start_date, end_date, description, and bullets.
- bullets must preserve the major bullet points for each role as a string array.
- Return every education item with degree, school, field_of_study, and graduation_year.
- Use empty strings instead of null when a field is missing.
- Do not return empty objects in experience or education.
- headline should be the candidate's current or most recent professional title.
"""
    extracted = _normalize_resume_extracted(
        await _extract_resume_with_repair(content, schema, prompt)
    )
    if not _has_resume_detail(extracted):
        extracted = _normalize_resume_extracted(await _repair_resume_extracted(content, extracted))
    await db.update_document_parse(document_id, content=extracted)

    summary = extracted.get("summary") or f"{extracted.get('name', 'Candidate')} | {extracted.get('headline', '')}".strip(" |")
    return await db.create_profile(
        user_id=user_id,
        profile_type="resume",
        document_id=document_id,
        name=extracted.get("name"),
        headline=extracted.get("headline"),
        skills=extracted.get("skills", []),
        experience={
            "experience": extracted.get("experience", []),
            "education": extracted.get("education", []),
        },
        structured_json=extracted,
        summary_text=summary,
    )


async def extract_job_profile(user_id: str, document_id: str) -> dict:
    """Extract job profile from a parsed JD document."""
    document = await _load_document_for_user(user_id, document_id)
    if document["kind"] != "job_description":
        raise ValueError("Document is not a job description")

    content, tools = build_job_input(document)
    if not content.strip():
        raise ValueError("Job description appears to be empty")
    lowered = (document.get("raw_text") or "").lower()
    if document.get("source_type") == "url" and "linkedin.com" in (document.get("source_url") or "").lower():
        if "sign in" in lowered or "join linkedin" in lowered or "session_redirect" in lowered:
            raise ValueError(
                "The provided LinkedIn URL redirects to a login page, so the job description cannot be extracted reliably. Paste the job description text instead."
            )

    schema = {
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "role": {"type": "string"},
            "requirements": {"type": "array", "items": {"type": "string"}},
            "nice_to_have": {"type": "array", "items": {"type": "string"}},
            "responsibilities": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": ["company", "role", "requirements", "nice_to_have", "responsibilities", "summary"],
    }
    prompt = """Extract a structured job profile with:
- company
- role
- requirements
- nice_to_have
- responsibilities
- summary

Rules:
- Prefer information stated explicitly in the source.
- Do not invent company details, compensation, or requirements.
- For URL-backed job descriptions, use the URL context as primary and the fallback text only when needed."""
    extracted = await extract_with_gemini(
        content,
        prompt,
        schema,
        response_model=JobExtractionModel,
        tools=tools,
    )
    await db.update_document_parse(document_id, content=extracted)

    return await db.create_profile(
        user_id=user_id,
        profile_type="job_description",
        document_id=document_id,
        company=extracted.get("company"),
        role=extracted.get("role"),
        requirements={
            "requirements": extracted.get("requirements", []),
            "nice_to_have": extracted.get("nice_to_have", []),
            "responsibilities": extracted.get("responsibilities", []),
        },
        structured_json=extracted,
        summary_text=extracted.get("summary"),
    )


async def get_profile(profile_id: str) -> Optional[dict]:
    """Get a single profile."""
    return await db.get_profile_by_id(profile_id)


async def get_profiles_by_user(user_id: str) -> list:
    """List all profiles for a user."""
    return await db.get_profiles_by_user(user_id)


async def build_match_analysis(resume_profile_id: str, job_profile_id: str) -> dict:
    """Build a lightweight deterministic match summary."""
    resume_profile = await db.get_profile_by_id(resume_profile_id)
    job_profile = await db.get_profile_by_id(job_profile_id)
    if not resume_profile or not job_profile:
        raise ValueError("Resume or job profile not found")
    return _build_match_analysis(resume_profile, job_profile)
