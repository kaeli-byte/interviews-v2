"""Database queries using Drizzle ORM with Supabase."""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Use DIRECT_URL to bypass pgbouncer (works with asyncpg pool)
DATABASE_URL = os.getenv("DIRECT_URL") or os.getenv("SUPABASE_DB_URL", os.getenv("DATABASE_URL"))

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise ValueError("SUPABASE_DB_URL not set in environment")
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ============================================================================
# User Queries
# ============================================================================

async def create_user(email: str, password_hash: str) -> Dict[str, Any]:
    """Create a new user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
            email, password_hash
        )
        return {"id": str(user_id), "email": email}


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = $1",
            email
        )
        if row:
            return {
                "id": str(row["id"]),
                "email": row["email"],
                "password_hash": row["password_hash"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
        return None


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, created_at FROM users WHERE id = $1",
            uuid.UUID(user_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "email": row["email"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
        return None


# ============================================================================
# Document Queries
# ============================================================================

async def create_document(
    user_id: str,
    doc_type: str,
    filename: Optional[str] = None,
    content: Optional[str] = None,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new document."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        doc_id = await conn.fetchval(
            """INSERT INTO documents (user_id, type, filename, content, file_path)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            uuid.UUID(user_id), doc_type, filename, content, file_path
        )
        return {"id": str(doc_id), "user_id": user_id, "type": doc_type}


async def get_documents_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all documents for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, user_id, type, filename, content, file_path, created_at
               FROM documents WHERE user_id = $1 ORDER BY created_at DESC""",
            uuid.UUID(user_id)
        )
        return [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "type": r["type"],
                "filename": r["filename"],
                "content": r["content"],
                "file_path": r["file_path"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]


async def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Get document by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, user_id, type, filename, content, file_path, created_at
               FROM documents WHERE id = $1""",
            uuid.UUID(document_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]),
                "type": row["type"],
                "filename": row["filename"],
                "content": row["content"],
                "file_path": row["file_path"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
        return None


async def delete_document(document_id: str) -> bool:
    """Delete a document."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM documents WHERE id = $1",
            uuid.UUID(document_id)
        )
        return result == "DELETE 1"


# ============================================================================
# Profile Queries
# ============================================================================

async def create_profile(
    user_id: str,
    profile_type: str,
    document_id: Optional[str] = None,
    name: Optional[str] = None,
    headline: Optional[str] = None,
    skills: Optional[str] = None,
    experience: Optional[str] = None,
    company: Optional[str] = None,
    role: Optional[str] = None,
    requirements: Optional[str] = None,
    confidence_score: Optional[float] = None
) -> Dict[str, Any]:
    """Create a new profile."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        profile_id = await conn.fetchval(
            """INSERT INTO profiles (user_id, profile_type, document_id, name, headline,
               skills, experience, company, role, requirements, confidence_score)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id""",
            uuid.UUID(user_id), profile_type,
            uuid.UUID(document_id) if document_id else None,
            name, headline, skills, experience, company, role, requirements, confidence_score
        )
        return {"id": str(profile_id), "user_id": user_id, "profile_type": profile_type}


async def get_profiles_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all profiles for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, document_id, user_id, profile_type, name, headline, skills,
               experience, company, role, requirements, confidence_score, created_at
               FROM profiles WHERE user_id = $1 ORDER BY created_at DESC""",
            uuid.UUID(user_id)
        )
        return [
            {
                "id": str(r["id"]),
                "document_id": str(r["document_id"]) if r["document_id"] else None,
                "user_id": str(r["user_id"]),
                "profile_type": r["profile_type"],
                "name": r["name"],
                "headline": r["headline"],
                "skills": r["skills"],
                "experience": r["experience"],
                "company": r["company"],
                "role": r["role"],
                "requirements": r["requirements"],
                "confidence_score": r["confidence_score"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]


async def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """Get profile by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, document_id, user_id, profile_type, name, headline, skills,
               experience, company, role, requirements, confidence_score, created_at
               FROM profiles WHERE id = $1""",
            uuid.UUID(profile_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "document_id": str(row["document_id"]) if row["document_id"] else None,
                "user_id": str(row["user_id"]),
                "profile_type": row["profile_type"],
                "name": row["name"],
                "headline": row["headline"],
                "skills": row["skills"],
                "experience": row["experience"],
                "company": row["company"],
                "role": row["role"],
                "requirements": row["requirements"],
                "confidence_score": row["confidence_score"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
        return None


# ============================================================================
# Interview Context Queries
# ============================================================================

async def create_interview_context(
    user_id: str,
    resume_profile_id: Optional[str] = None,
    job_profile_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new interview context."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        context_id = await conn.fetchval(
            """INSERT INTO interview_contexts (user_id, resume_profile_id, job_profile_id)
               VALUES ($1, $2, $3) RETURNING id""",
            uuid.UUID(user_id),
            uuid.UUID(resume_profile_id) if resume_profile_id else None,
            uuid.UUID(job_profile_id) if job_profile_id else None
        )
        return {"id": str(context_id), "user_id": user_id}


async def get_interview_contexts_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all interview contexts for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, user_id, resume_profile_id, job_profile_id, created_at
               FROM interview_contexts WHERE user_id = $1 ORDER BY created_at DESC""",
            uuid.UUID(user_id)
        )
        return [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "resume_profile_id": str(r["resume_profile_id"]) if r["resume_profile_id"] else None,
                "job_profile_id": str(r["job_profile_id"]) if r["job_profile_id"] else None,
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]


async def get_interview_context_by_id(context_id: str) -> Optional[Dict[str, Any]]:
    """Get interview context by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, user_id, resume_profile_id, job_profile_id, created_at
               FROM interview_contexts WHERE id = $1""",
            uuid.UUID(context_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]),
                "resume_profile_id": str(row["resume_profile_id"]) if row["resume_profile_id"] else None,
                "job_profile_id": str(row["job_profile_id"]) if row["job_profile_id"] else None,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
        return None


# ============================================================================
# Session Queries
# ============================================================================

async def create_session(
    user_id: str,
    context_id: Optional[str] = None,
    status: str = "pending"
) -> Dict[str, Any]:
    """Create a new session."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        session_id = await conn.fetchval(
            """INSERT INTO sessions (user_id, context_id, status)
               VALUES ($1, $2, $3) RETURNING id""",
            uuid.UUID(user_id),
            uuid.UUID(context_id) if context_id else None,
            status
        )
        return {"id": str(session_id), "user_id": user_id, "status": status}


async def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, user_id, context_id, status, started_at, ended_at, transcript
               FROM sessions WHERE id = $1""",
            uuid.UUID(session_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]),
                "context_id": str(row["context_id"]) if row["context_id"] else None,
                "status": row["status"],
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
                "transcript": row["transcript"] or []
            }
        return None


async def update_session_status(session_id: str, status: str) -> bool:
    """Update session status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status == "ended":
            result = await conn.execute(
                "UPDATE sessions SET status = $1, ended_at = NOW() WHERE id = $2",
                status, uuid.UUID(session_id)
            )
        else:
            result = await conn.execute(
                "UPDATE sessions SET status = $1 WHERE id = $2",
                status, uuid.UUID(session_id)
            )
        return result == "UPDATE 1"


async def update_session_transcript(session_id: str, transcript: List[Dict[str, Any]]) -> bool:
    """Update session transcript."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE sessions SET transcript = $1 WHERE id = $2",
            transcript, uuid.UUID(session_id)
        )
        return result == "UPDATE 1"


async def get_sessions_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all sessions for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, user_id, context_id, agent_id, status, started_at, ended_at, transcript, reconnect_token
               FROM sessions WHERE user_id = $1 ORDER BY started_at DESC""",
            uuid.UUID(user_id)
        )
        return [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "context_id": str(r["context_id"]) if r["context_id"] else None,
                "agent_id": str(r["agent_id"]) if r["agent_id"] else None,
                "status": r["status"],
                "started_at": r["started_at"].isoformat() if r["started_at"] else None,
                "ended_at": r["ended_at"].isoformat() if r["ended_at"] else None,
                "transcript": r["transcript"] or [],
                "reconnect_token": str(r["reconnect_token"]) if r["reconnect_token"] else None
            }
            for r in rows
        ]


async def get_session_by_reconnect_token(reconnect_token: str) -> Optional[Dict[str, Any]]:
    """Get session by reconnect token for persistence."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, user_id, context_id, agent_id, status, started_at, ended_at, transcript
               FROM sessions WHERE reconnect_token = $1""",
            uuid.UUID(reconnect_token)
        )
        if row:
            return {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]),
                "context_id": str(row["context_id"]) if row["context_id"] else None,
                "agent_id": str(row["agent_id"]) if row["agent_id"] else None,
                "status": row["status"],
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
                "transcript": row["transcript"] or []
            }
        return None


async def update_session_agent(session_id: str, agent_id: str) -> bool:
    """Update session's current agent."""
    pool = await get_pool()
    result = await pool.execute(
        "UPDATE sessions SET agent_id = $1 WHERE id = $2",
        uuid.UUID(agent_id), uuid.UUID(session_id)
    )
    return result == "UPDATE 1"


# ============================================================================
# Agent Config Queries
# ============================================================================

async def create_agent_config(
    name: str,
    description: str,
    prompt_template: str,
    behavior_settings: Optional[Dict] = None,
    rubric_definition: Optional[List] = None,
    is_active: bool = True
) -> Dict[str, Any]:
    """Create a new agent config."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        agent_id = await conn.fetchval(
            """INSERT INTO agent_configs (name, description, prompt_template, behavior_settings, rubric_definition, is_active)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            name, description, prompt_template, behavior_settings or {}, rubric_definition or [], is_active
        )
        return {"id": str(agent_id), "name": name}


async def get_active_agents() -> List[Dict[str, Any]]:
    """Get all active agent configs."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, name, description, prompt_template, behavior_settings, rubric_definition, version
               FROM agent_configs WHERE is_active = true ORDER BY name"""
        )
        return [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "description": r["description"],
                "prompt_template": r["prompt_template"],
                "behavior_settings": r["behavior_settings"] or {},
                "rubric_definition": r["rubric_definition"] or [],
                "version": r["version"]
            }
            for r in rows
        ]


async def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent config by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, name, description, prompt_template, behavior_settings, rubric_definition, version
               FROM agent_configs WHERE id = $1""",
            uuid.UUID(agent_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "prompt_template": row["prompt_template"],
                "behavior_settings": row["behavior_settings"] or {},
                "rubric_definition": row["rubric_definition"] or [],
                "version": row["version"]
            }
        return None


async def seed_default_agents():
    """Seed default interview agents if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval("SELECT COUNT(*) FROM agent_configs WHERE is_active = true")
        if existing > 0:
            return  # Already seeded

        # HR Manager agent
        await conn.execute(
            """INSERT INTO agent_configs (name, description, prompt_template, behavior_settings, rubric_definition, is_active)
               VALUES ($1, $2, $3, $4, $5, true)""",
            "HR Manager",
            "Focuses on cultural fit, soft skills, and general qualifications",
            """You are an HR Manager conducting a job interview. Be professional, friendly, and focus on:
- Candidate's background and experience
- Cultural fit and team dynamics
- Communication skills
- Career goals and motivation
- Leadership and collaboration

Ask thoughtful questions and provide a comfortable atmosphere.""",
            {"tone": "professional", "focus": "cultural_fit"},
            [
                {"dimension": "Communication", "description": "Clarity, articulation, and professionalism"},
                {"dimension": "Cultural Fit", "description": "Alignment with company values and team dynamics"},
                {"dimension": "Leadership", "description": "Ability to lead and collaborate"},
                {"dimension": "Motivation", "description": "Career goals and alignment with role"}
            ]
        )

        # Hiring Manager agent
        await conn.execute(
            """INSERT INTO agent_configs (name, description, prompt_template, behavior_settings, rubric_definition, is_active)
               VALUES ($1, $2, $3, $4, $5, true)""",
            "Hiring Manager",
            "Focuses on technical skills, problem-solving, and role-specific competencies",
            """You are a Hiring Manager conducting a technical job interview. Be thorough, analytical, and focus on:
- Technical skills and expertise
- Problem-solving abilities
- Project experience and achievements
- Technical depth and breadth
- Decision-making process

Ask challenging questions that test real-world knowledge and problem-solving approach.""",
            {"tone": "technical", "focus": "technical_skills"},
            [
                {"dimension": "Technical Knowledge", "description": "Depth of technical expertise"},
                {"dimension": "Problem Solving", "description": "Analytical thinking and approach"},
                {"dimension": "Experience", "description": "Relevant project experience"},
                {"dimension": "Decision Making", "description": "Technical judgment and reasoning"}
            ]
        )


# ============================================================================
# Debrief Queries
# ============================================================================

async def create_debrief(
    session_id: str,
    user_id: str,
    scores: Dict[str, float],
    feedback: str,
    evidence: Optional[List[Dict]] = None,
    rubric_used: Optional[List] = None
) -> Dict[str, Any]:
    """Create a new debrief."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        debrief_id = await conn.fetchval(
            """INSERT INTO debriefs (session_id, user_id, scores, feedback, evidence, rubric_used)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            uuid.UUID(session_id), uuid.UUID(user_id), scores, feedback, evidence or [], rubric_used or []
        )
        return {"id": str(debrief_id), "session_id": session_id}


async def get_debrief_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get debrief for a session."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, session_id, user_id, scores, feedback, evidence, rubric_used, generated_at
               FROM debriefs WHERE session_id = $1""",
            uuid.UUID(session_id)
        )
        if row:
            return {
                "id": str(row["id"]),
                "session_id": str(row["session_id"]),
                "user_id": str(row["user_id"]),
                "scores": row["scores"] or {},
                "feedback": row["feedback"],
                "evidence": row["evidence"] or [],
                "rubric_used": row["rubric_used"] or [],
                "generated_at": row["generated_at"].isoformat() if row["generated_at"] else None
            }
        return None


async def get_debriefs_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all debriefs for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT d.id, d.session_id, d.user_id, d.scores, d.feedback, d.generated_at,
                      s.started_at, s.agent_id
               FROM debriefs d
               JOIN sessions s ON d.session_id = s.id
               WHERE d.user_id = $1
               ORDER BY d.generated_at DESC""",
            uuid.UUID(user_id)
        )
        return [
            {
                "id": str(r["id"]),
                "session_id": str(r["session_id"]),
                "user_id": str(r["user_id"]),
                "scores": r["scores"] or {},
                "feedback": r["feedback"],
                "generated_at": r["generated_at"].isoformat() if r["generated_at"] else None,
                "session_date": r["started_at"].isoformat() if r["started_at"] else None,
                "agent_id": str(r["agent_id"]) if r["agent_id"] else None
            }
            for r in rows
        ]


async def delete_debrief(session_id: str) -> bool:
    """Delete debrief for a session (for regeneration)."""
    pool = await get_pool()
    result = await pool.execute("DELETE FROM debriefs WHERE session_id = $1", uuid.UUID(session_id))
    return result == "DELETE 1"