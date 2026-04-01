"""LLM-backed profile extraction helpers."""
import asyncio
import json
from typing import Any, Dict, Type

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.config import settings


class ExperienceItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    description: str
    bullets: list[str] = Field(default_factory=list)


class EducationItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: str
    school: str
    field_of_study: str
    graduation_year: str


class ResumeExtractionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    headline: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    experience: list[ExperienceItemModel] = Field(default_factory=list)
    education: list[EducationItemModel] = Field(default_factory=list)


class ResumeRepairModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    headline: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    experience: list[ExperienceItemModel] = Field(default_factory=list)
    education: list[EducationItemModel] = Field(default_factory=list)


class JobExtractionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    role: str
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    summary: str


class LLMTemporaryUnavailableError(Exception):
    """Raised when the upstream LLM is temporarily unavailable."""


def _extract_json_payload(text: str) -> dict:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned non-JSON output for structured extraction") from exc


async def extract_with_gemini(
    content: str,
    prompt: str,
    response_schema: Dict[str, Any],
    response_model: Type[BaseModel] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict:
    """Extract structured data using Gemini JSON mode and validate the output."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    full_prompt = f"""{prompt}

Return only JSON matching the schema.

Content:
---
{content}
---
"""
    config_kwargs: dict[str, Any] = {"tools": tools}
    if not tools:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=settings.MODEL_EXTRACT,
            contents=full_prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
    except genai_errors.ServerError as exc:
        raise LLMTemporaryUnavailableError(
            "The extraction model is temporarily unavailable. Please retry in a moment."
        ) from exc
    if not response.text:
        raise ValueError("Gemini returned empty response")
    payload = _extract_json_payload(response.text)
    if response_model is None:
        return payload
    try:
        return response_model.model_validate(payload).model_dump()
    except ValidationError as exc:
        raise ValueError(f"Gemini returned invalid structured output: {exc}") from exc


def build_resume_input(document: dict) -> str:
    raw_text = document.get("raw_text") or ""
    parser_hints = document.get("content") or {}
    if not parser_hints:
        return raw_text
    return f"""You are given:
1) Resume text
2) Deterministic hints extracted by a parser

Use hints as suggestions, but rely primarily on the resume text.
If hints conflict with the text, trust the text.

Deterministic hints:
{json.dumps(parser_hints, ensure_ascii=True)}

Resume text:
---
{raw_text}
---"""


def build_job_input(document: dict) -> tuple[str, list[dict[str, Any]] | None]:
    raw_text = document.get("raw_text") or ""
    source_url = document.get("source_url") or ""

    if document.get("source_type") == "url" and source_url:
        return (
            f"""You are given:
1) A job description URL
2) Fallback text extracted from that URL

Use the URL context as the primary source when it is available.
Use the extracted text as a fallback.
If the URL content and fallback text conflict, trust the URL content.

Job description URL:
{source_url}

Fallback extracted text:
---
{raw_text}
---""",
            [{"url_context": {}}],
        )

    return raw_text, None
