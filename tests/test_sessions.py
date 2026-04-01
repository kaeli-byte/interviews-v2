"""Setup flow session and context API tests."""
import asyncio
from unittest.mock import AsyncMock, patch


def _resume_profile():
    return {
        "profile_id": "resume-profile-1",
        "type": "resume",
        "document_id": "resume-doc-1",
        "name": "Jane Candidate",
        "headline": "Senior Backend Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": [{"title": "Senior Engineer", "company": "Acme"}],
        "structured_json": {},
        "summary_text": "Jane Candidate | Senior Backend Engineer",
        "created_at": "2026-03-30T00:00:00Z",
    }


def _job_profile():
    return {
        "profile_id": "job-profile-1",
        "type": "job_description",
        "document_id": "jd-doc-1",
        "company": "Example Corp",
        "role": "Staff Backend Engineer",
        "requirements": ["Python", "FastAPI", "System design"],
        "nice_to_have": ["Supabase"],
        "responsibilities": ["Own backend services"],
        "structured_json": {},
        "summary_text": "Staff backend role",
        "created_at": "2026-03-30T00:00:00Z",
    }


def _agent():
    return {
        "agent_id": "agent-1",
        "name": "Career Narrative Architect",
        "description": "Narrative role",
        "prompt_template": "You are the narrative architect.",
        "behavior_settings": {},
        "rubric_definition": [],
        "version": 1,
    }


def _context():
    return {
        "context_id": "context-1",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "resume_profile_id": "resume-profile-1",
        "job_profile_id": "job-profile-1",
        "agent_id": "agent-1",
        "custom_instructions": "Focus on impact stories",
        "match_analysis": {"match_score": 67, "matched_requirements": ["Python"]},
        "resume_profile": _resume_profile(),
        "job_profile": _job_profile(),
        "resume_document": {
            "document_id": "resume-doc-1",
            "type": "resume",
            "source_type": "file",
            "filename": "resume.pdf",
            "created_at": "2026-03-30T00:00:00Z",
        },
        "job_document": {
            "document_id": "jd-doc-1",
            "type": "job_description",
            "source_type": "url",
            "filename": "job-description-url.txt",
            "source_url": "https://example.com/jobs/backend",
            "created_at": "2026-03-30T00:00:00Z",
        },
        "agent": _agent(),
        "startup_prompt": "Prompt with context",
        "created_at": "2026-03-30T00:00:00Z",
    }


class TestSetupFlow:
    """Validate the saved setup can be created and started."""

    @patch("backend.api.profiles.service.extract_resume_profile", new_callable=AsyncMock)
    def test_extract_resume_profile(self, mock_extract_resume, client, auth_headers):
        mock_extract_resume.return_value = _resume_profile()

        response = client.post(
            "/api/profiles/extract-from-resume",
            headers=auth_headers,
            json={"document_id": "resume-doc-1"},
        )

        assert response.status_code == 200
        assert response.json()["profile_id"] == "resume-profile-1"

    @patch("backend.api.profiles.service.extract_job_profile", new_callable=AsyncMock)
    def test_extract_job_profile(self, mock_extract_job, client, auth_headers):
        mock_extract_job.return_value = _job_profile()

        response = client.post(
            "/api/profiles/extract-from-jd",
            headers=auth_headers,
            json={"document_id": "jd-doc-1"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["profile_id"] == "job-profile-1"
        assert body["role"] == "Staff Backend Engineer"

    @patch("backend.api.sessions.service.create_interview_context", new_callable=AsyncMock)
    def test_create_hydrated_interview_context(self, mock_create_context, client, auth_headers):
        mock_create_context.return_value = _context()

        response = client.post(
            "/api/interview-contexts",
            headers=auth_headers,
            json={
                "resume_profile_id": "resume-profile-1",
                "job_profile_id": "job-profile-1",
                "agent_id": "agent-1",
                "custom_instructions": "Focus on impact stories",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["context_id"] == "context-1"
        assert body["resume_profile"]["name"] == "Jane Candidate"
        assert body["job_profile"]["role"] == "Staff Backend Engineer"
        assert body["agent"]["agent_id"] == "agent-1"
        assert "startup_prompt" in body

    @patch("backend.api.sessions.service.get_interview_context", new_callable=AsyncMock)
    def test_get_hydrated_interview_context(self, mock_get_context, client, auth_headers):
        mock_get_context.return_value = _context()

        response = client.get("/api/interview-contexts/context-1", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["context_id"] == "context-1"

    @patch("backend.api.sessions.service.create_session", new_callable=AsyncMock)
    def test_create_session_from_saved_context(self, mock_create_session, client, auth_headers):
        mock_create_session.return_value = {
            "session_id": "session-1",
            "reconnect_token": "reconnect-1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "interview_context_id": "context-1",
            "agent_id": "agent-1",
            "state": "pending",
            "created_at": "2026-03-30T00:00:00Z",
            "context": _context(),
        }

        response = client.post(
            "/api/sessions",
            headers=auth_headers,
            json={"interview_context_id": "context-1", "agent_id": "agent-1"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == "session-1"
        assert body["interview_context_id"] == "context-1"
        assert body["context"]["startup_prompt"] == "Prompt with context"

    @patch("backend.api.sessions.service.get_session_summaries_by_user", new_callable=AsyncMock)
    def test_list_sessions_returns_lightweight_summaries(self, mock_get_sessions, client, auth_headers):
        mock_get_sessions.return_value = [
            {
                "session_id": "session-1",
                "interview_context_id": "context-1",
                "agent_id": "agent-1",
                "state": "pending",
                "created_at": "2026-03-30T00:00:00Z",
                "editable": True,
                "candidate_name": "Jane Candidate",
                "target_role": "Staff Backend Engineer",
                "company": "Example Corp",
                "agent_name": "Career Narrative Architect",
            }
        ]

        response = client.get("/api/sessions", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body[0]["editable"] is True
        assert body[0]["candidate_name"] == "Jane Candidate"
        assert "context" not in body[0]

    @patch("backend.api.sessions.service.update_session_setup", new_callable=AsyncMock)
    def test_update_session_setup(self, mock_update_session_setup, client, auth_headers):
        mock_update_session_setup.return_value = {
            "session_id": "session-1",
            "reconnect_token": "reconnect-1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "interview_context_id": "context-1",
            "agent_id": "agent-1",
            "state": "pending",
            "created_at": "2026-03-30T00:00:00Z",
            "editable": True,
            "context": _context(),
        }

        response = client.patch(
            "/api/sessions/session-1/setup",
            headers=auth_headers,
            json={
                "resume_profile_id": "resume-profile-1",
                "job_profile_id": "job-profile-1",
                "agent_id": "agent-1",
                "custom_instructions": "Focus on impact stories",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == "session-1"
        assert body["editable"] is True

    @patch("backend.api.sessions.service.update_session_setup", new_callable=AsyncMock)
    def test_update_session_setup_returns_conflict_for_started_session(self, mock_update_session_setup, client, auth_headers):
        mock_update_session_setup.side_effect = RuntimeError(
            "This session has already started. Create a new setup to use updated inputs."
        )

        response = client.patch(
            "/api/sessions/session-1/setup",
            headers=auth_headers,
            json={
                "resume_profile_id": "resume-profile-1",
                "job_profile_id": "job-profile-1",
                "agent_id": "agent-1",
                "custom_instructions": None,
            },
        )

        assert response.status_code == 409

    @patch("backend.api.sessions.service.get_interview_prep_for_session", new_callable=AsyncMock)
    def test_get_interview_prep_for_existing_session(self, mock_get_prep, client, auth_headers):
        mock_get_prep.return_value = {
            "session_id": "session-1",
            "context_id": "context-1",
            "startup_prompt": "Prompt with context",
            "agent": {"name": "Career Narrative Architect", "prompt_template": "You are the narrative architect."},
            "resume_profile": {"name": "Jane Candidate", "headline": "Senior Backend Engineer"},
            "job_profile": {"company": "Example Corp", "role": "Staff Backend Engineer"},
            "match_analysis": {"match_score": 67},
        }

        response = client.get("/api/interview-prep/session-1", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["session_id"] == "session-1"
        assert response.json()["agent"]["name"] == "Career Narrative Architect"

    @patch("backend.api.sessions.service.create_interview_prep_for_context", new_callable=AsyncMock)
    def test_create_interview_prep_for_context(self, mock_create_prep, client, auth_headers):
        mock_create_prep.return_value = {
            "session_id": "session-2",
            "context_id": "context-1",
            "startup_prompt": "Prompt with context",
            "agent": {"name": "Career Narrative Architect", "prompt_template": "You are the narrative architect."},
            "resume_profile": {"name": "Jane Candidate", "headline": "Senior Backend Engineer"},
            "job_profile": {"company": "Example Corp", "role": "Staff Backend Engineer"},
            "match_analysis": {"match_score": 67},
        }

        response = client.post(
            "/api/interview-prep",
            headers=auth_headers,
            json={"context_id": "context-1", "agent_id": "agent-1"},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session-2"


@patch("backend.api.sessions.service.db.get_document_by_id", new_callable=AsyncMock)
@patch("backend.api.sessions.service.db.get_agent_by_id", new_callable=AsyncMock)
@patch("backend.api.sessions.service.db.get_profile_by_id", new_callable=AsyncMock)
def test_hydrate_interview_context_parses_string_match_analysis(mock_get_profile, mock_get_agent, mock_get_document):
    mock_get_profile.side_effect = [_resume_profile(), _job_profile()]
    mock_get_document.side_effect = [
        {"document_id": "resume-doc-1", "type": "resume", "source_type": "file", "filename": "resume.pdf"},
        {"document_id": "jd-doc-1", "type": "job_description", "source_type": "url", "source_url": "https://example.com/jobs/backend"},
    ]
    mock_get_agent.return_value = {
        **_agent(),
        "behavior_settings": '{"voice":"strategic","focus":"career_narrative"}',
        "rubric_definition": '[]',
    }

    hydrated = asyncio.run(
        __import__("backend.api.sessions.service", fromlist=["hydrate_interview_context"]).hydrate_interview_context(
            {
                "context_id": "context-1",
                "resume_profile_id": "resume-profile-1",
                "job_profile_id": "job-profile-1",
                "agent_id": "agent-1",
                "custom_instructions": None,
                "match_analysis_json": '{"match_score":67,"matched_requirements":["Python"],"gap_requirements":["System design"]}',
            }
        )
    )

    assert hydrated["match_analysis"]["match_score"] == 67
    assert hydrated["agent"]["behavior_settings"]["voice"] == "strategic"
    assert hydrated["agent"]["rubric_definition"] == []
    assert "Match score: 67" in hydrated["startup_prompt"]


def test_session_is_editable_for_ending_state_without_transcript():
    session_service = __import__("backend.api.sessions.service", fromlist=["_is_session_editable"])
    assert session_service._is_session_editable({"state": "ending", "transcript": []}) is True
    assert session_service._is_session_editable({"state": "active", "transcript": []}) is False


@patch("backend.db.queries.get_pool", new_callable=AsyncMock)
def test_get_session_by_id_parses_string_transcript(mock_get_pool):
    queries = __import__("backend.db.queries", fromlist=["get_session_by_id"])

    class FakeConn:
        async def fetchrow(self, *_args, **_kwargs):
            return {
                "id": "c65a8cf0-a7c4-46de-af4c-b7d78e3e8852",
                "user_id": "5042c2a1-500d-400b-9606-e285db412584",
                "context_id": "e298bb84-2a2e-4adc-8cd2-4940ecc96aeb",
                "agent_id": "9ff70f1e-4df6-4b1f-8e26-ecbf0bc10a77",
                "status": "pending",
                "started_at": None,
                "ended_at": None,
                "transcript": "[]",
                "reconnect_token": "3f327aa0-89af-4b0b-94ce-dab97dbe93ab",
            }

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    mock_get_pool.return_value = FakePool()
    result = asyncio.run(queries.get_session_by_id("c65a8cf0-a7c4-46de-af4c-b7d78e3e8852"))

    assert result["transcript"] == []
