"""Database queries using asyncpg with Supabase Postgres."""
import json
import os
import uuid
from typing import Any, Dict, List, Optional

import asyncpg
from dotenv import load_dotenv

from backend.perf import timing_span

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT_DIR, "backend", ".env"), override=False)
load_dotenv(os.path.join(ROOT_DIR, ".env.local"), override=False)

DATABASE_URL = os.getenv("DIRECT_URL") or os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

_pool: Optional[asyncpg.Pool] = None
_schema_ready = False


async def get_pool() -> asyncpg.Pool:
    """Get or create the shared connection pool."""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise ValueError("DIRECT_URL or SUPABASE_DB_URL must be set")
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


async def close_pool():
    """Close the shared connection pool."""
    global _pool, _schema_ready
    if _pool:
        await _pool.close()
        _pool = None
    _schema_ready = False


async def ensure_schema():
    """Guard for environments where migrations are expected to provision schema."""
    global _schema_ready
    if _schema_ready:
        return
    _schema_ready = True


def _uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _json_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _session_from_row(row: asyncpg.Record) -> Dict[str, Any]:
    transcript = row["transcript"] or []
    if isinstance(transcript, str):
        transcript = json.loads(transcript)
    return {
        "id": str(row["id"]),
        "session_id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "context_id": str(row["context_id"]) if row["context_id"] else None,
        "interview_context_id": str(row["context_id"]) if row["context_id"] else None,
        "agent_id": str(row["agent_id"]) if row["agent_id"] else None,
        "status": row["status"],
        "state": row["status"],
        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
        "created_at": row["started_at"].isoformat() if row["started_at"] else None,
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "transcript": transcript,
        "reconnect_token": str(row["reconnect_token"]) if row["reconnect_token"] else None,
    }


def _decode_profile_row(
    *,
    profile_id: Any,
    document_id: Any,
    user_id: Any,
    profile_type: Any,
    name: Any,
    headline: Any,
    skills: Any,
    experience: Any,
    company: Any,
    role: Any,
    requirements: Any,
    confidence_score: Any,
    structured_json: Any,
    summary_text: Any,
    created_at: Any,
) -> Optional[Dict[str, Any]]:
    if not profile_id:
        return None
    structured = structured_json or {}
    if isinstance(structured, str):
        structured = json.loads(structured)
    parsed_experience = json.loads(experience) if experience else []
    parsed_requirements = json.loads(requirements) if requirements else []
    profile = {
        "id": str(profile_id),
        "profile_id": str(profile_id),
        "document_id": str(document_id) if document_id else None,
        "user_id": str(user_id) if user_id else None,
        "profile_type": profile_type,
        "type": profile_type,
        "name": name,
        "headline": headline,
        "skills": json.loads(skills) if skills else [],
        "experience": parsed_experience,
        "company": company,
        "role": role,
        "requirements": parsed_requirements,
        "confidence_score": confidence_score,
        "structured_json": structured,
        "summary_text": summary_text,
        "created_at": created_at.isoformat() if created_at else None,
    }
    if profile_type == "resume" and isinstance(parsed_experience, dict):
        profile["experience"] = parsed_experience.get("experience", [])
        profile["education"] = parsed_experience.get("education", [])
    if profile_type == "job_description" and isinstance(parsed_requirements, dict):
        profile["requirements"] = parsed_requirements.get("requirements", [])
        profile["nice_to_have"] = parsed_requirements.get("nice_to_have", [])
        profile["responsibilities"] = parsed_requirements.get("responsibilities", [])
    return profile


def _decode_agent_row(
    *,
    agent_id: Any,
    name: Any,
    description: Any,
    prompt_template: Any,
    behavior_settings: Any,
    rubric_definition: Any,
    version: Any,
) -> Optional[Dict[str, Any]]:
    if not agent_id:
        return None
    parsed_behavior = behavior_settings or {}
    parsed_rubric = rubric_definition or []
    if isinstance(parsed_behavior, str):
        parsed_behavior = json.loads(parsed_behavior)
    if isinstance(parsed_rubric, str):
        parsed_rubric = json.loads(parsed_rubric)
    return {
        "id": str(agent_id),
        "agent_id": str(agent_id),
        "name": name,
        "description": description,
        "prompt_template": prompt_template,
        "behavior_settings": parsed_behavior,
        "rubric_definition": parsed_rubric,
        "version": version,
    }


async def create_document(
    *,
    user_id: str,
    kind: str,
    source_type: str,
    filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    storage_path: Optional[str] = None,
    source_url: Optional[str] = None,
    raw_text: Optional[str] = None,
    content: Optional[Any] = None,
    parse_status: str = "pending",
) -> Dict[str, Any]:
    """Insert a document row."""
    await ensure_schema()
    pool = await get_pool()
    document_id = uuid.uuid4()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO documents (
                id, user_id, kind, type, source_type, filename, mime_type,
                storage_path, source_url, raw_text, content, parse_status
            )
            VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            document_id,
            _uuid(user_id),
            kind,
            source_type,
            filename,
            mime_type,
            storage_path,
            source_url,
            raw_text,
            _json_text(content),
            parse_status,
        )
    return await get_document_by_id(str(document_id))


async def get_documents_by_user(user_id: str) -> List[Dict[str, Any]]:
    """List documents for a user."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, kind, source_type, filename, mime_type, storage_path,
                   source_url, raw_text, content, parse_status, created_at
            FROM documents
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            _uuid(user_id),
        )
    return [
        {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "kind": row["kind"],
            "type": row["kind"],
            "source_type": row["source_type"],
            "filename": row["filename"],
            "mime_type": row["mime_type"],
            "storage_path": row["storage_path"],
            "source_url": row["source_url"],
            "raw_text": row["raw_text"],
            "content": json.loads(row["content"]) if row["content"] else None,
            "parse_status": row["parse_status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


async def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Load a document by id."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, kind, source_type, filename, mime_type, storage_path,
                   source_url, raw_text, content, parse_status, created_at
            FROM documents
            WHERE id = $1
            """,
            _uuid(document_id),
        )
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "kind": row["kind"],
        "type": row["kind"],
        "source_type": row["source_type"],
        "filename": row["filename"],
        "mime_type": row["mime_type"],
        "storage_path": row["storage_path"],
        "source_url": row["source_url"],
        "raw_text": row["raw_text"],
        "content": json.loads(row["content"]) if row["content"] else None,
        "parse_status": row["parse_status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


async def update_document_parse(
    document_id: str,
    *,
    raw_text: Optional[str] = None,
    content: Optional[Any] = None,
    parse_status: Optional[str] = None,
) -> bool:
    """Update parsed document text/status."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE documents
            SET raw_text = COALESCE($2, raw_text),
                content = COALESCE($3, content),
                parse_status = COALESCE($4, parse_status)
            WHERE id = $1
            """,
            _uuid(document_id),
            raw_text,
            _json_text(content),
            parse_status,
        )
    return result == "UPDATE 1"


async def delete_document(document_id: str) -> bool:
    """Delete a document."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM documents WHERE id = $1", _uuid(document_id))
    return result == "DELETE 1"


async def create_profile(
    *,
    user_id: str,
    profile_type: str,
    document_id: Optional[str] = None,
    name: Optional[str] = None,
    headline: Optional[str] = None,
    skills: Optional[Any] = None,
    experience: Optional[Any] = None,
    company: Optional[str] = None,
    role: Optional[str] = None,
    requirements: Optional[Any] = None,
    confidence_score: Optional[float] = None,
    structured_json: Optional[Dict[str, Any]] = None,
    summary_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a profile row."""
    await ensure_schema()
    pool = await get_pool()
    profile_id = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO profiles (
                id, document_id, user_id, profile_type, name, headline, skills,
                experience, company, role, requirements, confidence_score,
                structured_json, summary_text
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                $8, $9, $10, $11, $12, $13, $14
            )
            """,
            profile_id,
            _uuid(document_id) if document_id else None,
            _uuid(user_id),
            profile_type,
            name,
            headline,
            _json_text(skills),
            _json_text(experience),
            company,
            role,
            _json_text(requirements),
            confidence_score,
            _json_text(structured_json or {}),
            summary_text,
        )
    return await get_profile_by_id(str(profile_id))


async def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """Load a profile by id."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, document_id, user_id, profile_type, name, headline, skills,
                   experience, company, role, requirements, confidence_score,
                   structured_json, summary_text, created_at
            FROM profiles
            WHERE id = $1
            """,
            _uuid(profile_id),
        )
    if not row:
        return None
    structured_json = row["structured_json"] or {}
    if isinstance(structured_json, str):
        structured_json = json.loads(structured_json)
    parsed_experience = json.loads(row["experience"]) if row["experience"] else []
    parsed_requirements = json.loads(row["requirements"]) if row["requirements"] else []

    profile = {
        "id": str(row["id"]),
        "profile_id": str(row["id"]),
        "document_id": str(row["document_id"]) if row["document_id"] else None,
        "user_id": str(row["user_id"]),
        "profile_type": row["profile_type"],
        "type": row["profile_type"],
        "name": row["name"],
        "headline": row["headline"],
        "skills": json.loads(row["skills"]) if row["skills"] else [],
        "experience": parsed_experience,
        "company": row["company"],
        "role": row["role"],
        "requirements": parsed_requirements,
        "confidence_score": row["confidence_score"],
        "structured_json": structured_json,
        "summary_text": row["summary_text"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }
    if profile["profile_type"] == "resume" and isinstance(parsed_experience, dict):
        profile["experience"] = parsed_experience.get("experience", [])
        profile["education"] = parsed_experience.get("education", [])
    if profile["profile_type"] == "job_description" and isinstance(parsed_requirements, dict):
        profile["requirements"] = parsed_requirements.get("requirements", [])
        profile["nice_to_have"] = parsed_requirements.get("nice_to_have", [])
        profile["responsibilities"] = parsed_requirements.get("responsibilities", [])
    return profile


async def get_profiles_by_user(user_id: str) -> List[Dict[str, Any]]:
    """List profiles for a user."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id
            FROM profiles
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            _uuid(user_id),
        )
    results = []
    for row in rows:
        profile = await get_profile_by_id(str(row["id"]))
        if profile:
            results.append(profile)
    return results


async def create_interview_context(
    *,
    user_id: str,
    resume_profile_id: str,
    job_profile_id: str,
    agent_id: str,
    custom_instructions: Optional[str] = None,
    match_analysis_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert an interview context row."""
    await ensure_schema()
    pool = await get_pool()
    context_id = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO interview_contexts (
                id, user_id, resume_profile_id, job_profile_id, agent_id,
                custom_instructions, match_analysis_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            context_id,
            _uuid(user_id),
            _uuid(resume_profile_id),
            _uuid(job_profile_id),
            _uuid(agent_id),
            custom_instructions,
            _json_text(match_analysis_json or {}),
        )
    return await get_interview_context_by_id(str(context_id))


async def get_interview_context_by_id(context_id: str) -> Optional[Dict[str, Any]]:
    """Load an interview context."""
    await ensure_schema()
    pool = await get_pool()
    with timing_span("db.contexts.batch"):
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, resume_profile_id, job_profile_id, agent_id,
                       custom_instructions, match_analysis_json, created_at
                FROM interview_contexts
                WHERE id = $1
                """,
                _uuid(context_id),
            )
    if not row:
        return None
    match_analysis_json = row["match_analysis_json"] or {}
    if isinstance(match_analysis_json, str):
        match_analysis_json = json.loads(match_analysis_json)
    return {
        "id": str(row["id"]),
        "context_id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "resume_profile_id": str(row["resume_profile_id"]) if row["resume_profile_id"] else None,
        "job_profile_id": str(row["job_profile_id"]) if row["job_profile_id"] else None,
        "agent_id": str(row["agent_id"]) if row["agent_id"] else None,
        "custom_instructions": row["custom_instructions"],
        "match_analysis_json": match_analysis_json,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


async def get_hydrated_session_detail(session_id: str) -> Optional[Dict[str, Any]]:
    """Load a session and its interview context in one joined query."""
    await ensure_schema()
    try:
        session_uuid = _uuid(session_id)
    except ValueError:
        return None
    pool = await get_pool()
    with timing_span("db.sessions.detail_joined"):
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    s.id AS session_id,
                    s.user_id AS session_user_id,
                    s.context_id AS session_context_id,
                    s.agent_id AS session_agent_id,
                    s.status AS session_status,
                    s.started_at AS session_started_at,
                    s.ended_at AS session_ended_at,
                    s.transcript AS session_transcript,
                    s.reconnect_token AS session_reconnect_token,

                    ic.id AS context_id,
                    ic.user_id AS context_user_id,
                    ic.resume_profile_id,
                    ic.job_profile_id,
                    ic.agent_id AS context_agent_id,
                    ic.custom_instructions,
                    ic.match_analysis_json,
                    ic.created_at AS context_created_at,

                    rp.id AS resume_profile_id_value,
                    rp.document_id AS resume_document_id_ref,
                    rp.user_id AS resume_user_id,
                    rp.profile_type AS resume_profile_type,
                    rp.name AS resume_name,
                    rp.headline AS resume_headline,
                    rp.skills AS resume_skills,
                    rp.experience AS resume_experience,
                    rp.company AS resume_company,
                    rp.role AS resume_role,
                    rp.requirements AS resume_requirements,
                    rp.confidence_score AS resume_confidence_score,
                    rp.structured_json AS resume_structured_json,
                    rp.summary_text AS resume_summary_text,
                    rp.created_at AS resume_created_at,

                    jp.id AS job_profile_id_value,
                    jp.document_id AS job_document_id_ref,
                    jp.user_id AS job_user_id,
                    jp.profile_type AS job_profile_type,
                    jp.name AS job_name,
                    jp.headline AS job_headline,
                    jp.skills AS job_skills,
                    jp.experience AS job_experience,
                    jp.company AS job_company,
                    jp.role AS job_role,
                    jp.requirements AS job_requirements,
                    jp.confidence_score AS job_confidence_score,
                    jp.structured_json AS job_structured_json,
                    jp.summary_text AS job_summary_text,
                    jp.created_at AS job_created_at,

                    ac.id AS agent_id_value,
                    ac.name AS agent_name,
                    ac.description AS agent_description,
                    ac.prompt_template AS agent_prompt_template,
                    ac.behavior_settings AS agent_behavior_settings,
                    ac.rubric_definition AS agent_rubric_definition,
                    ac.version AS agent_version,

                    rd.id AS resume_document_id_value,
                    rd.kind AS resume_document_kind,
                    rd.source_type AS resume_document_source_type,
                    rd.filename AS resume_document_filename,
                    rd.mime_type AS resume_document_mime_type,
                    rd.source_url AS resume_document_source_url,
                    rd.parse_status AS resume_document_parse_status,
                    rd.created_at AS resume_document_created_at,

                    jd.id AS job_document_id_value,
                    jd.kind AS job_document_kind,
                    jd.source_type AS job_document_source_type,
                    jd.filename AS job_document_filename,
                    jd.mime_type AS job_document_mime_type,
                    jd.source_url AS job_document_source_url,
                    jd.parse_status AS job_document_parse_status,
                    jd.created_at AS job_document_created_at
                FROM sessions s
                LEFT JOIN interview_contexts ic ON ic.id = s.context_id
                LEFT JOIN profiles rp ON rp.id = ic.resume_profile_id
                LEFT JOIN profiles jp ON jp.id = ic.job_profile_id
                LEFT JOIN agent_configs ac ON ac.id = COALESCE(s.agent_id, ic.agent_id)
                LEFT JOIN documents rd ON rd.id = rp.document_id
                LEFT JOIN documents jd ON jd.id = jp.document_id
                WHERE s.id = $1
                """,
                session_uuid,
            )
    if not row:
        return None
    transcript = row["session_transcript"] or []
    if isinstance(transcript, str):
        transcript = json.loads(transcript)

    match_analysis_json = row["match_analysis_json"] or {}
    if isinstance(match_analysis_json, str):
        match_analysis_json = json.loads(match_analysis_json)

    resume_profile = _decode_profile_row(
        profile_id=row["resume_profile_id_value"],
        document_id=row["resume_document_id_ref"],
        user_id=row["resume_user_id"],
        profile_type=row["resume_profile_type"],
        name=row["resume_name"],
        headline=row["resume_headline"],
        skills=row["resume_skills"],
        experience=row["resume_experience"],
        company=row["resume_company"],
        role=row["resume_role"],
        requirements=row["resume_requirements"],
        confidence_score=row["resume_confidence_score"],
        structured_json=row["resume_structured_json"],
        summary_text=row["resume_summary_text"],
        created_at=row["resume_created_at"],
    )
    job_profile = _decode_profile_row(
        profile_id=row["job_profile_id_value"],
        document_id=row["job_document_id_ref"],
        user_id=row["job_user_id"],
        profile_type=row["job_profile_type"],
        name=row["job_name"],
        headline=row["job_headline"],
        skills=row["job_skills"],
        experience=row["job_experience"],
        company=row["job_company"],
        role=row["job_role"],
        requirements=row["job_requirements"],
        confidence_score=row["job_confidence_score"],
        structured_json=row["job_structured_json"],
        summary_text=row["job_summary_text"],
        created_at=row["job_created_at"],
    )
    agent = _decode_agent_row(
        agent_id=row["agent_id_value"],
        name=row["agent_name"],
        description=row["agent_description"],
        prompt_template=row["agent_prompt_template"],
        behavior_settings=row["agent_behavior_settings"],
        rubric_definition=row["agent_rubric_definition"],
        version=row["agent_version"],
    )

    return {
        "session_id": str(row["session_id"]),
        "reconnect_token": str(row["session_reconnect_token"]) if row["session_reconnect_token"] else None,
        "user_id": str(row["session_user_id"]),
        "interview_context_id": str(row["session_context_id"]) if row["session_context_id"] else None,
        "agent_id": str(row["session_agent_id"]) if row["session_agent_id"] else None,
        "state": row["session_status"],
        "status": row["session_status"],
        "created_at": row["session_started_at"].isoformat() if row["session_started_at"] else None,
        "started_at": row["session_started_at"].isoformat() if row["session_started_at"] else None,
        "ended_at": row["session_ended_at"].isoformat() if row["session_ended_at"] else None,
        "transcript": transcript,
        "context": {
            "context_id": str(row["context_id"]) if row["context_id"] else None,
            "user_id": str(row["context_user_id"]) if row["context_user_id"] else None,
            "resume_profile_id": str(row["resume_profile_id"]) if row["resume_profile_id"] else None,
            "job_profile_id": str(row["job_profile_id"]) if row["job_profile_id"] else None,
            "agent_id": str(row["context_agent_id"]) if row["context_agent_id"] else None,
            "custom_instructions": row["custom_instructions"],
            "match_analysis_json": match_analysis_json,
            "created_at": row["context_created_at"].isoformat() if row["context_created_at"] else None,
            "resume_profile": resume_profile,
            "job_profile": job_profile,
            "resume_document": {
                "document_id": str(row["resume_document_id_value"]),
                "type": row["resume_document_kind"],
                "source_type": row["resume_document_source_type"],
                "filename": row["resume_document_filename"],
                "mime_type": row["resume_document_mime_type"],
                "source_url": row["resume_document_source_url"],
                "parse_status": row["resume_document_parse_status"],
                "created_at": row["resume_document_created_at"].isoformat() if row["resume_document_created_at"] else None,
            } if row["resume_document_id_value"] else None,
            "job_document": {
                "document_id": str(row["job_document_id_value"]),
                "type": row["job_document_kind"],
                "source_type": row["job_document_source_type"],
                "filename": row["job_document_filename"],
                "mime_type": row["job_document_mime_type"],
                "source_url": row["job_document_source_url"],
                "parse_status": row["job_document_parse_status"],
                "created_at": row["job_document_created_at"].isoformat() if row["job_document_created_at"] else None,
            } if row["job_document_id_value"] else None,
            "agent": agent,
        },
    }


async def get_interview_contexts_by_user(user_id: str) -> List[Dict[str, Any]]:
    """List interview contexts for a user."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id FROM interview_contexts WHERE user_id = $1 ORDER BY created_at DESC",
            _uuid(user_id),
        )
    results = []
    for row in rows:
        context = await get_interview_context_by_id(str(row["id"]))
        if context:
            results.append(context)
    return results


async def update_interview_context(
    context_id: str,
    *,
    resume_profile_id: Optional[str] = None,
    job_profile_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    match_analysis_json: Optional[Dict[str, Any]] = None,
) -> bool:
    """Update mutable interview context fields."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE interview_contexts
            SET resume_profile_id = COALESCE($2, resume_profile_id),
                job_profile_id = COALESCE($3, job_profile_id),
                agent_id = COALESCE($4, agent_id),
                custom_instructions = COALESCE($5, custom_instructions),
                match_analysis_json = COALESCE($6, match_analysis_json)
            WHERE id = $1
            """,
            _uuid(context_id),
            _uuid(resume_profile_id) if resume_profile_id else None,
            _uuid(job_profile_id) if job_profile_id else None,
            _uuid(agent_id) if agent_id else None,
            custom_instructions,
            _json_text(match_analysis_json) if match_analysis_json is not None else None,
        )
    return result == "UPDATE 1"


async def create_session(
    *,
    user_id: str,
    context_id: str,
    agent_id: Optional[str] = None,
    status: str = "pending",
) -> Dict[str, Any]:
    """Insert a session row."""
    await ensure_schema()
    pool = await get_pool()
    session_id = uuid.uuid4()
    reconnect_token = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (id, user_id, context_id, agent_id, status, reconnect_token)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            session_id,
            _uuid(user_id),
            _uuid(context_id),
            _uuid(agent_id) if agent_id else None,
            status,
            reconnect_token,
        )
    return await get_session_by_id(str(session_id))


async def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Load a session by id."""
    await ensure_schema()
    try:
        session_uuid = _uuid(session_id)
    except ValueError:
        return None
    pool = await get_pool()
    with timing_span("db.sessions.detail"):
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, context_id, agent_id, status, started_at, ended_at,
                       transcript, reconnect_token
                FROM sessions
                WHERE id = $1
                """,
                session_uuid,
            )
    if not row:
        return None
    return _session_from_row(row)


async def get_session_summaries_by_user(user_id: str, *, limit: int = 8) -> List[Dict[str, Any]]:
    """List lightweight session summaries for a user."""
    await ensure_schema()
    pool = await get_pool()
    with timing_span("db.sessions.summary"):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    s.id AS session_id,
                    s.context_id,
                    s.agent_id,
                    s.status,
                    s.started_at,
                    s.reconnect_token,
                    COALESCE(jsonb_array_length(s.transcript), 0) AS transcript_count,
                    rp.name AS candidate_name,
                    jp.role AS target_role,
                    jp.company AS company,
                    ac.name AS agent_name
                FROM sessions s
                LEFT JOIN interview_contexts ic ON ic.id = s.context_id
                LEFT JOIN profiles rp ON rp.id = ic.resume_profile_id
                LEFT JOIN profiles jp ON jp.id = ic.job_profile_id
                LEFT JOIN agent_configs ac ON ac.id = COALESCE(s.agent_id, ic.agent_id)
                WHERE s.user_id = $1
                ORDER BY s.started_at DESC
                LIMIT $2
                """,
                _uuid(user_id),
                limit,
            )
    return [
        {
            "session_id": str(row["session_id"]),
            "interview_context_id": str(row["context_id"]) if row["context_id"] else None,
            "agent_id": str(row["agent_id"]) if row["agent_id"] else None,
            "state": row["status"],
            "created_at": row["started_at"].isoformat() if row["started_at"] else None,
            "editable": row["status"] not in {"active", "paused"} and (row["transcript_count"] or 0) == 0,
            "candidate_name": row["candidate_name"],
            "target_role": row["target_role"],
            "company": row["company"],
            "agent_name": row["agent_name"],
        }
        for row in rows
    ]


async def get_session_by_reconnect_token(reconnect_token: str) -> Optional[Dict[str, Any]]:
    """Load a session by reconnect token."""
    await ensure_schema()
    try:
        reconnect_uuid = _uuid(reconnect_token)
    except ValueError:
        return None
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM sessions WHERE reconnect_token = $1", reconnect_uuid)
    if not row:
        return None
    return await get_session_by_id(str(row["id"]))


async def update_session_status(session_id: str, status: str) -> bool:
    """Update session status."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status == "ended":
            result = await conn.execute(
                "UPDATE sessions SET status = $2, ended_at = NOW() WHERE id = $1",
                _uuid(session_id),
                status,
            )
        else:
            result = await conn.execute(
                "UPDATE sessions SET status = $2 WHERE id = $1",
                _uuid(session_id),
                status,
            )
    return result == "UPDATE 1"


async def update_session_transcript(session_id: str, transcript: List[Dict[str, Any]]) -> bool:
    """Persist session transcript."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE sessions SET transcript = $2 WHERE id = $1",
            _uuid(session_id),
            _json_text(transcript),
        )
    return result == "UPDATE 1"


async def update_session_agent(session_id: str, agent_id: str) -> bool:
    """Set session agent."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE sessions SET agent_id = $2 WHERE id = $1",
            _uuid(session_id),
            _uuid(agent_id),
        )
    return result == "UPDATE 1"


async def create_agent_config(
    *,
    name: str,
    description: str,
    prompt_template: str,
    behavior_settings: Optional[Dict[str, Any]] = None,
    rubric_definition: Optional[List[Dict[str, Any]]] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    """Insert an agent config row."""
    await ensure_schema()
    pool = await get_pool()
    agent_id = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO agent_configs (
                id, name, description, prompt_template, behavior_settings,
                rubric_definition, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            agent_id,
            name,
            description,
            prompt_template,
            _json_text(behavior_settings or {}),
            _json_text(rubric_definition or []),
            is_active,
        )
    return await get_agent_by_id(str(agent_id))


async def get_active_agents() -> List[Dict[str, Any]]:
    """List active agent configs."""
    await ensure_schema()
    pool = await get_pool()
    with timing_span("db.agents.list"):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, description, prompt_template, behavior_settings,
                       rubric_definition, version
                FROM agent_configs
                WHERE is_active = TRUE
                ORDER BY created_at ASC
                """
            )
    results = []
    for row in rows:
        behavior_settings = row["behavior_settings"] or {}
        rubric_definition = row["rubric_definition"] or []
        if isinstance(behavior_settings, str):
            behavior_settings = json.loads(behavior_settings)
        if isinstance(rubric_definition, str):
            rubric_definition = json.loads(rubric_definition)
        results.append(
            {
                "id": str(row["id"]),
                "agent_id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "prompt_template": row["prompt_template"],
                "behavior_settings": behavior_settings,
                "rubric_definition": rubric_definition,
                "version": row["version"],
            }
        )
    return results


async def get_active_agent_summaries() -> List[Dict[str, Any]]:
    """List active agents with only summary fields required by setup UI."""
    await ensure_schema()
    pool = await get_pool()
    with timing_span("db.agents.list"):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, description
                FROM agent_configs
                WHERE is_active = TRUE
                ORDER BY created_at ASC
                """
            )
    return [
        {
            "agent_id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
        }
        for row in rows
    ]


async def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Load an agent config by id."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, description, prompt_template, behavior_settings,
                   rubric_definition, version
            FROM agent_configs
            WHERE id = $1
            """,
            _uuid(agent_id),
        )
    if not row:
        return None
    behavior_settings = row["behavior_settings"] or {}
    rubric_definition = row["rubric_definition"] or []
    if isinstance(behavior_settings, str):
        behavior_settings = json.loads(behavior_settings)
    if isinstance(rubric_definition, str):
        rubric_definition = json.loads(rubric_definition)
    return {
        "id": str(row["id"]),
        "agent_id": str(row["id"]),
        "name": row["name"],
        "description": row["description"],
        "prompt_template": row["prompt_template"],
        "behavior_settings": behavior_settings,
        "rubric_definition": rubric_definition,
        "version": row["version"],
    }


async def seed_default_agents():
    """Ensure the Role agent exists as the v1 active persona."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT id FROM agent_configs WHERE name = $1 LIMIT 1",
            "Career Narrative Architect",
        )
        if existing:
            return

    role_prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "frontend",
        "src",
        "prompts",
        "Role.md",
    )
    with open(role_prompt_path, "r", encoding="utf-8") as handle:
        prompt_template = handle.read()

    await create_agent_config(
        name="Career Narrative Architect",
        description="Guides the candidate through a structured career narrative aligned to the target role.",
        prompt_template=prompt_template,
        behavior_settings={"voice": "strategic", "focus": "career_narrative"},
        rubric_definition=[],
        is_active=True,
    )


async def create_debrief(
    session_id: str,
    user_id: str,
    scores: Dict[str, float],
    feedback: str,
    evidence: Optional[List[Dict[str, Any]]] = None,
    rubric_used: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Insert a debrief row."""
    await ensure_schema()
    pool = await get_pool()
    debrief_id = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO debriefs (id, session_id, user_id, scores, feedback, evidence, rubric_used)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            debrief_id,
            _uuid(session_id),
            _uuid(user_id),
            _json_text(scores),
            feedback,
            _json_text(evidence or []),
            _json_text(rubric_used or []),
        )
    return {"id": str(debrief_id), "session_id": session_id}


async def get_debrief_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Load a debrief by session id."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, session_id, user_id, scores, feedback, evidence, rubric_used, generated_at
            FROM debriefs
            WHERE session_id = $1
            """,
            _uuid(session_id),
        )
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "session_id": str(row["session_id"]),
        "user_id": str(row["user_id"]),
        "scores": row["scores"] or {},
        "feedback": row["feedback"],
        "evidence": row["evidence"] or [],
        "rubric_used": row["rubric_used"] or [],
        "generated_at": row["generated_at"].isoformat() if row["generated_at"] else None,
    }


async def get_debriefs_by_user(user_id: str) -> List[Dict[str, Any]]:
    """List debriefs for a user."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, session_id, user_id, scores, feedback, evidence, rubric_used, generated_at
            FROM debriefs
            WHERE user_id = $1
            ORDER BY generated_at DESC
            """,
            _uuid(user_id),
        )
    return [
        {
            "id": str(row["id"]),
            "session_id": str(row["session_id"]),
            "user_id": str(row["user_id"]),
            "scores": row["scores"] or {},
            "feedback": row["feedback"],
            "evidence": row["evidence"] or [],
            "rubric_used": row["rubric_used"] or [],
            "generated_at": row["generated_at"].isoformat() if row["generated_at"] else None,
        }
        for row in rows
    ]


async def delete_debrief(session_id: str) -> bool:
    """Delete debrief by session id."""
    await ensure_schema()
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM debriefs WHERE session_id = $1", _uuid(session_id))
    return result == "DELETE 1"
