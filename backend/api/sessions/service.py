"""Sessions service - Supabase-backed context and session management."""
import json
from time import monotonic
from typing import Optional

from backend.api.profiles import service as profile_service
from backend.db import queries as db
from backend.perf import timing_span

SESSION_STATE_PENDING = "pending"
SESSION_STATE_ACTIVE = "active"
SESSION_STATE_PAUSED = "paused"
SESSION_STATE_ENDED = "ended"

VALID_TRANSITIONS = {
    SESSION_STATE_PENDING: [SESSION_STATE_ACTIVE, SESSION_STATE_ENDED],
    SESSION_STATE_ACTIVE: [SESSION_STATE_PAUSED, SESSION_STATE_ENDED],
    SESSION_STATE_PAUSED: [SESSION_STATE_ACTIVE, SESSION_STATE_ENDED],
    SESSION_STATE_ENDED: [],
}

sessions_db = {}
_session_summaries_cache: dict[tuple[str, int], tuple[float, list]] = {}
_SESSION_SUMMARIES_CACHE_TTL_SECONDS = 60.0
_session_detail_cache: dict[tuple[str, str], tuple[float, dict]] = {}
_interview_prep_cache: dict[tuple[str, str, Optional[str]], tuple[float, dict]] = {}
_SESSION_DETAIL_CACHE_TTL_SECONDS = 60.0
_INTERVIEW_PREP_CACHE_TTL_SECONDS = 60.0


def is_valid_transition(current_state: str, new_state: str) -> bool:
    """Check if a session state transition is valid."""
    return new_state in VALID_TRANSITIONS.get(current_state, [])


def _list_from_job_field(job_profile: dict, key: str) -> list[str]:
    data = job_profile.get("structured_json", {})
    value = data.get(key)
    return value if isinstance(value, list) else []


def _document_snapshot(document: Optional[dict]) -> Optional[dict]:
    if not document:
        return None
    return {
        "document_id": document.get("document_id") or document.get("id"),
        "type": document.get("type") or document.get("kind"),
        "source_type": document.get("source_type"),
        "filename": document.get("filename"),
        "mime_type": document.get("mime_type"),
        "source_url": document.get("source_url"),
        "parse_status": document.get("parse_status"),
        "created_at": document.get("created_at"),
    }


def _is_session_editable(session: dict) -> bool:
    transcript = session.get("transcript") or []
    state = session.get("state")
    return state not in {SESSION_STATE_ACTIVE, SESSION_STATE_PAUSED} and not transcript


def build_startup_prompt(context: dict) -> str:
    """Build the context payload used to kick off the live session."""
    agent = context["agent"]
    resume = context["resume_profile"]
    job = context["job_profile"]
    match = context.get("match_analysis", {})
    if isinstance(match, str):
        try:
            match = json.loads(match)
        except json.JSONDecodeError:
            match = {}

    return (
        f"{agent['prompt_template']}\n\n"
        "Interview setup context:\n"
        f"- Candidate name: {resume.get('name') or 'Unknown'}\n"
        f"- Candidate headline: {resume.get('headline') or 'Unknown'}\n"
        f"- Candidate skills: {', '.join(resume.get('skills', [])[:12])}\n"
        f"- Target company: {job.get('company') or 'Unknown'}\n"
        f"- Target role: {job.get('role') or 'Unknown'}\n"
        f"- Requirements: {', '.join(_list_from_job_field(job, 'requirements')[:12])}\n"
        f"- Responsibilities: {', '.join(_list_from_job_field(job, 'responsibilities')[:12])}\n"
        f"- Match score: {match.get('match_score', 0)}\n"
        f"- Matched requirements: {', '.join(match.get('matched_requirements', [])[:10])}\n"
        f"- Gaps: {', '.join(match.get('gap_requirements', [])[:10])}\n"
        f"- Custom instructions: {context.get('custom_instructions') or 'None'}\n\n"
        "Begin with a short greeting, confirm the target role, and guide the candidate through their career story."
    )


async def hydrate_interview_context(context: dict) -> dict:
    """Expand an interview context with linked profiles and agent config."""
    with timing_span("db.profiles.resume"):
        resume_profile = await db.get_profile_by_id(context["resume_profile_id"])
    with timing_span("db.profiles.job"):
        job_profile = await db.get_profile_by_id(context["job_profile_id"])
    with timing_span("db.agent.detail"):
        agent = await db.get_agent_by_id(context["agent_id"])
    if not resume_profile or not job_profile or not agent:
        raise ValueError("Interview context is incomplete")
    resume_document = None
    if resume_profile.get("document_id"):
        with timing_span("db.documents.resume"):
            resume_document = _document_snapshot(await db.get_document_by_id(resume_profile["document_id"]))
    job_document = None
    if job_profile.get("document_id"):
        with timing_span("db.documents.job"):
            job_document = _document_snapshot(await db.get_document_by_id(job_profile["document_id"]))

    behavior_settings = agent.get("behavior_settings", {})
    if isinstance(behavior_settings, str):
        try:
            behavior_settings = json.loads(behavior_settings)
        except json.JSONDecodeError:
            behavior_settings = {}

    rubric_definition = agent.get("rubric_definition", [])
    if isinstance(rubric_definition, str):
        try:
            rubric_definition = json.loads(rubric_definition)
        except json.JSONDecodeError:
            rubric_definition = []

    match_analysis = context.get("match_analysis_json", {})
    if isinstance(match_analysis, str):
        try:
            match_analysis = json.loads(match_analysis)
        except json.JSONDecodeError:
            match_analysis = {}

    with timing_span("service.sessions.serialize"):
        hydrated = {
            **context,
            "resume_profile": resume_profile,
            "job_profile": job_profile,
            "resume_document": resume_document,
            "job_document": job_document,
            "agent": {
                **agent,
                "behavior_settings": behavior_settings,
                "rubric_definition": rubric_definition,
            },
            "match_analysis": match_analysis,
        }
        with timing_span("service.startup_prompt.build"):
            hydrated["startup_prompt"] = build_startup_prompt(hydrated)
    return hydrated


def _serialize_hydrated_context(context: dict) -> dict:
    """Normalize a joined hydrated context into the public response shape."""
    normalized = {
        "context_id": context.get("context_id"),
        "user_id": context.get("user_id"),
        "resume_profile_id": context.get("resume_profile_id"),
        "job_profile_id": context.get("job_profile_id"),
        "agent_id": context.get("agent_id"),
        "custom_instructions": context.get("custom_instructions"),
        "match_analysis": context.get("match_analysis_json") or context.get("match_analysis") or {},
        "resume_profile": context.get("resume_profile"),
        "job_profile": context.get("job_profile"),
        "resume_document": context.get("resume_document"),
        "job_document": context.get("job_document"),
        "agent": context.get("agent"),
        "created_at": context.get("created_at"),
    }
    with timing_span("service.startup_prompt.build"):
        normalized["startup_prompt"] = build_startup_prompt(normalized)
    return normalized


async def create_interview_context(
    user_id: str,
    resume_profile_id: str,
    job_profile_id: str,
    agent_id: str,
    custom_instructions: Optional[str] = None,
) -> dict:
    """Create a persisted interview context."""
    resume_profile = await db.get_profile_by_id(resume_profile_id)
    job_profile = await db.get_profile_by_id(job_profile_id)
    agent = await db.get_agent_by_id(agent_id)
    if not resume_profile or resume_profile["user_id"] != user_id:
        raise ValueError("Resume profile not found")
    if not job_profile or job_profile["user_id"] != user_id:
        raise ValueError("Job profile not found")
    if not agent:
        raise ValueError("Agent not found")

    match_analysis = await profile_service.build_match_analysis(resume_profile_id, job_profile_id)
    context = await db.create_interview_context(
        user_id=user_id,
        resume_profile_id=resume_profile_id,
        job_profile_id=job_profile_id,
        agent_id=agent_id,
        custom_instructions=custom_instructions,
        match_analysis_json=match_analysis,
    )
    return await hydrate_interview_context(context)


async def get_interview_context(context_id: str) -> Optional[dict]:
    """Get an interview context by id."""
    context = await db.get_interview_context_by_id(context_id)
    if not context:
        return None
    return await hydrate_interview_context(context)


async def get_interview_contexts_by_user(user_id: str) -> list:
    """List hydrated contexts for a user."""
    contexts = await db.get_interview_contexts_by_user(user_id)
    hydrated = []
    for context in contexts:
        hydrated.append(await hydrate_interview_context(context))
    return hydrated


async def create_session(user_id: str, interview_context_id: str, agent_id: Optional[str] = None) -> dict:
    """Create a persisted interview session."""
    context = await db.get_interview_context_by_id(interview_context_id)
    if not context or context["user_id"] != user_id:
        raise ValueError("Interview context not found")

    chosen_agent_id = agent_id or context["agent_id"]
    if not chosen_agent_id:
        raise ValueError("Agent is required")

    session = await db.create_session(
        user_id=user_id,
        context_id=interview_context_id,
        agent_id=chosen_agent_id,
        status=SESSION_STATE_PENDING,
    )
    invalidate_session_summaries_cache(user_id)
    session["context"] = await hydrate_interview_context(context)
    return session


async def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    detail = await db.get_hydrated_session_detail(session_id)
    if not detail:
        return None

    with timing_span("service.sessions.detail_serialize"):
        session = {
            "session_id": detail["session_id"],
            "reconnect_token": detail["reconnect_token"],
            "user_id": detail["user_id"],
            "interview_context_id": detail["interview_context_id"],
            "agent_id": detail["agent_id"],
            "state": detail["state"],
            "status": detail["status"],
            "created_at": detail["created_at"],
            "started_at": detail["started_at"],
            "ended_at": detail["ended_at"],
            "transcript": detail["transcript"],
        }
        if detail.get("context"):
            session["context"] = _serialize_hydrated_context(detail["context"])
        session["editable"] = _is_session_editable(session)
    return session


def _build_interview_prep(session: dict) -> dict:
    context = session["context"]
    return {
        "session_id": session["session_id"],
        "context_id": session.get("interview_context_id"),
        "agent": {
            "name": context["agent"]["name"],
            "prompt_template": context["agent"]["prompt_template"],
        },
        "startup_prompt": context["startup_prompt"],
        "resume_profile": {
            "name": context["resume_profile"].get("name"),
            "headline": context["resume_profile"].get("headline"),
        },
        "job_profile": {
            "company": context["job_profile"].get("company"),
            "role": context["job_profile"].get("role"),
        },
        "match_analysis": {
            "match_score": (context.get("match_analysis") or {}).get("match_score"),
        },
    }


async def get_interview_prep_for_session(session_id: str, user_id: str) -> Optional[dict]:
    """Get cached interview prep payload for an existing session."""
    cache_key = (user_id, session_id)
    cached = _session_detail_cache.get(cache_key)
    now = monotonic()
    if cached and now - cached[0] < _SESSION_DETAIL_CACHE_TTL_SECONDS:
        return cached[1]

    session = await get_session(session_id)
    if not session or session.get("user_id") != user_id or not session.get("context"):
        return None
    prep = _build_interview_prep(session)
    _session_detail_cache[cache_key] = (now, prep)
    return prep


async def create_interview_prep_for_context(user_id: str, context_id: str, agent_id: Optional[str] = None) -> dict:
    """Create a session and return the lightweight interview prep payload."""
    cache_key = (user_id, context_id, agent_id)
    cached = _interview_prep_cache.get(cache_key)
    now = monotonic()
    if cached and now - cached[0] < _INTERVIEW_PREP_CACHE_TTL_SECONDS:
        return cached[1]

    session = await create_session(user_id, context_id, agent_id)
    if not session.get("context"):
        raise ValueError("Interview context not found")
    prep = _build_interview_prep(session)
    _interview_prep_cache[cache_key] = (now, prep)
    return prep


async def get_session_summaries_by_user(user_id: str, *, limit: int = 8) -> list:
    """Get lightweight session summaries for a user."""
    cache_key = (user_id, limit)
    cached = _session_summaries_cache.get(cache_key)
    now = monotonic()
    if cached and now - cached[0] < _SESSION_SUMMARIES_CACHE_TTL_SECONDS:
        return cached[1]

    sessions = await db.get_session_summaries_by_user(user_id, limit=limit)
    _session_summaries_cache[cache_key] = (now, sessions)
    return sessions


def invalidate_session_summaries_cache(user_id: Optional[str] = None) -> None:
    """Invalidate cached session summaries for one user or all users."""
    if user_id is None:
        _session_summaries_cache.clear()
        return

    keys_to_remove = [key for key in _session_summaries_cache if key[0] == user_id]
    for key in keys_to_remove:
        _session_summaries_cache.pop(key, None)
    detail_keys = [key for key in _session_detail_cache if key[0] == user_id]
    for key in detail_keys:
        _session_detail_cache.pop(key, None)
    prep_keys = [key for key in _interview_prep_cache if key[0] == user_id]
    for key in prep_keys:
        _interview_prep_cache.pop(key, None)


async def update_session_setup(
    session_id: str,
    user_id: str,
    *,
    resume_profile_id: str,
    job_profile_id: str,
    agent_id: str,
    custom_instructions: Optional[str] = None,
) -> dict:
    """Update the setup for a pending session without changing session identity."""
    session = await db.get_session_by_id(session_id)
    if not session or session["user_id"] != user_id:
        raise ValueError("Session not found")
    if not _is_session_editable(session):
        raise RuntimeError("This session has already started. Create a new setup to use updated inputs.")

    context_id = session.get("interview_context_id")
    if not context_id:
        raise ValueError("Session is missing interview context")
    context = await db.get_interview_context_by_id(context_id)
    if not context or context["user_id"] != user_id:
        raise ValueError("Interview context not found")

    resume_profile = await db.get_profile_by_id(resume_profile_id)
    job_profile = await db.get_profile_by_id(job_profile_id)
    agent = await db.get_agent_by_id(agent_id)
    if not resume_profile or resume_profile["user_id"] != user_id:
        raise ValueError("Resume profile not found")
    if not job_profile or job_profile["user_id"] != user_id:
        raise ValueError("Job profile not found")
    if not agent:
        raise ValueError("Agent not found")

    match_analysis = await profile_service.build_match_analysis(resume_profile_id, job_profile_id)
    updated = await db.update_interview_context(
        context_id,
        resume_profile_id=resume_profile_id,
        job_profile_id=job_profile_id,
        agent_id=agent_id,
        custom_instructions=custom_instructions,
        match_analysis_json=match_analysis,
    )
    if not updated:
        raise ValueError("Failed to update interview context")

    await db.update_session_agent(session_id, agent_id)
    invalidate_session_summaries_cache(user_id)
    refreshed = await get_session(session_id)
    if not refreshed:
        raise ValueError("Updated session not found")
    return refreshed


async def update_session_state(session_id: str, new_state: str, user_id: str) -> Optional[dict]:
    """Update the session status with transition validation."""
    session = await db.get_session_by_id(session_id)
    if not session or session["user_id"] != user_id:
        return None
    if not is_valid_transition(session["status"], new_state):
        return None
    success = await db.update_session_status(session_id, new_state)
    if not success:
        return None
    invalidate_session_summaries_cache(user_id)
    return await db.get_session_by_id(session_id)


async def update_session(session_id: str, user_id: str, **updates) -> Optional[dict]:
    """Update mutable session fields."""
    session = await db.get_session_by_id(session_id)
    if not session or session["user_id"] != user_id:
        return None

    if updates.get("agent_id"):
        await db.update_session_agent(session_id, updates["agent_id"])
        invalidate_session_summaries_cache(user_id)
    if updates.get("status") and updates["status"] != session["status"]:
        await update_session_state(session_id, updates["status"], user_id)
    return await db.get_session_by_id(session_id)


async def update_session_agent(session_id: str, agent_id: str) -> Optional[dict]:
    """Update only the session agent."""
    success = await db.update_session_agent(session_id, agent_id)
    if not success:
        return None
    return await db.get_session_by_id(session_id)


async def delete_session(session_id: str, user_id: str) -> bool:
    """End a session instead of hard-deleting it."""
    session = await db.get_session_by_id(session_id)
    if not session or session["user_id"] != user_id:
        return False
    success = await db.update_session_status(session_id, SESSION_STATE_ENDED)
    if success:
        invalidate_session_summaries_cache(user_id)
    return success
