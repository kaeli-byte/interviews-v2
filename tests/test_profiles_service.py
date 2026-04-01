"""Unit tests for profile extraction normalization and repair logic."""
import asyncio
from unittest.mock import AsyncMock, patch

from backend.api.profiles import service as profile_service
from backend.api.profiles import service_extractor
from google.genai import errors as genai_errors


def test_normalize_resume_extracted_removes_empty_nested_items():
    result = profile_service._normalize_resume_extracted(
        {
            "name": " Hafid  Tazrout ",
            "headline": " Engineering Director ",
            "email": " hafid@example.com ",
            "phone": " +1 555 123 4567 ",
            "location": " Singapore ",
            "linkedin": " https://www.linkedin.com/in/hafid ",
            "summary": " Built organizations and products. ",
            "skills": [" Team Management ", "", None, "Product Design"],
            "languages": [" English ", "", "French"],
            "experience": [{}, {"title": "Director", "company": "Acme", "description": "Led org", "bullets": [" Built org ", "Mentored team"]}],
            "education": [{}, {"degree": "MBA", "school": "INSEAD"}],
        }
    )

    assert result["name"] == "Hafid Tazrout"
    assert result["headline"] == "Engineering Director"
    assert result["email"] == "hafid@example.com"
    assert result["phone"] == "+1 555 123 4567"
    assert result["location"] == "Singapore"
    assert result["linkedin"] == "https://www.linkedin.com/in/hafid"
    assert result["summary"] == "Built organizations and products."
    assert result["skills"] == ["Team Management", "Product Design"]
    assert result["languages"] == ["English", "French"]
    assert result["experience"] == [
        {
            "title": "Director",
            "company": "Acme",
            "location": "",
            "start_date": "",
            "end_date": "",
            "description": "Led org",
            "bullets": ["Built org", "Mentored team"],
        }
    ]
    assert result["education"] == [
        {
            "degree": "MBA",
            "school": "INSEAD",
            "field_of_study": "",
            "graduation_year": "",
        }
    ]


def test_normalize_resume_extracted_builds_description_from_bullets_when_missing():
    result = profile_service._normalize_resume_extracted(
        {
            "name": "Hafid Tazrout",
            "headline": "Engineering Director",
            "experience": [
                {
                    "title": "Director",
                    "company": "Acme",
                    "description": "",
                    "bullets": ["Built org", "Mentored team"],
                }
            ],
            "education": [],
        }
    )

    assert result["experience"][0]["description"] == "Built org Mentored team"
    assert result["experience"][0]["bullets"] == ["Built org", "Mentored team"]


def test_build_resume_input_includes_parser_hints():
    result = profile_service.build_resume_input(
        {
            "raw_text": "Resume raw text",
            "content": {"name": "Hafid Tazrout", "experience": [{"company": "Acme"}]},
        }
    )

    assert "Use hints as suggestions, but rely primarily on the resume text." in result
    assert "If hints conflict with the text, trust the text." in result
    assert "Hafid Tazrout" in result
    assert "Resume raw text" in result


def test_build_job_input_uses_url_context_for_url_documents():
    content, tools = service_extractor.build_job_input(
        {
            "source_type": "url",
            "source_url": "https://example.com/jobs/backend",
            "raw_text": "Fallback scraped job description text",
        }
    )

    assert "Use the URL context as the primary source when it is available." in content
    assert "https://example.com/jobs/backend" in content
    assert "Fallback scraped job description text" in content
    assert tools == [{"url_context": {}}]


def test_build_job_input_returns_plain_text_for_non_url_documents():
    content, tools = service_extractor.build_job_input(
        {
            "source_type": "text",
            "raw_text": "Senior backend engineer role",
        }
    )

    assert content == "Senior backend engineer role"
    assert tools is None


def test_extract_with_gemini_validates_response_model():
    class FakeResponse:
        text = '{"name":"Hafid Tazrout","headline":"Engineering Director","email":"","phone":"","location":"","linkedin":"","summary":"","skills":[],"languages":[],"experience":[],"education":[]}'

    with patch("backend.api.profiles.service_extractor.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = FakeResponse()
        result = asyncio.run(
            service_extractor.extract_with_gemini(
                "resume text",
                "extract",
                {"type": "object"},
                response_model=service_extractor.ResumeExtractionModel,
            )
        )

    assert result["name"] == "Hafid Tazrout"


def test_extract_with_gemini_passes_tools_to_generate_content():
    class FakeResponse:
        text = '{"company":"Acme","role":"Backend Engineer","requirements":[],"nice_to_have":[],"responsibilities":[],"summary":"Build backend systems."}'

    with patch("backend.api.profiles.service_extractor.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = FakeResponse()
        result = asyncio.run(
            service_extractor.extract_with_gemini(
                "job text",
                "extract",
                {"type": "object"},
                response_model=service_extractor.JobExtractionModel,
                tools=[{"url_context": {}}],
            )
    )

    assert result["company"] == "Acme"
    call_kwargs = mock_client.return_value.models.generate_content.call_args.kwargs
    assert len(call_kwargs["config"].tools) == 1
    assert getattr(call_kwargs["config"].tools[0], "url_context", None) is not None
    assert getattr(call_kwargs["config"], "response_mime_type", None) is None


def test_extract_with_gemini_raises_on_invalid_model_output():
    class FakeResponse:
        text = '{"headline":"Engineering Director","skills":[],"experience":[],"education":[]}'

    with patch("backend.api.profiles.service_extractor.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = FakeResponse()
        try:
            asyncio.run(
                service_extractor.extract_with_gemini(
                    "resume text",
                    "extract",
                    {"type": "object"},
                    response_model=service_extractor.ResumeExtractionModel,
                )
            )
        except ValueError as exc:
            assert "invalid structured output" in str(exc)
        else:
            raise AssertionError("Expected extract_with_gemini to raise ValueError")


def test_extract_with_gemini_maps_server_error_to_temporary_unavailable():
    with patch("backend.api.profiles.service_extractor.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.side_effect = genai_errors.ServerError(
            503,
            {"error": {"status": "UNAVAILABLE"}},
            None,
        )
        try:
            asyncio.run(
                service_extractor.extract_with_gemini(
                    "job text",
                    "extract",
                    {"type": "object"},
                    response_model=service_extractor.JobExtractionModel,
                    tools=[{"url_context": {}}],
                )
            )
        except service_extractor.LLMTemporaryUnavailableError as exc:
            assert "temporarily unavailable" in str(exc)
        else:
            raise AssertionError("Expected transient LLM error")


@patch("backend.api.profiles.service.extract_with_gemini", new_callable=AsyncMock)
def test_extract_resume_with_repair_retries_after_validation_failure(mock_extract_with_gemini):
    mock_extract_with_gemini.side_effect = [
        ValueError("Gemini returned invalid structured output: missing required field"),
        {
            "name": "Hafid Tazrout",
            "headline": "Engineering Director",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "summary": "",
            "skills": ["Leadership"],
            "languages": [],
            "experience": [],
            "education": [],
        },
    ]

    result = asyncio.run(
        profile_service._extract_resume_with_repair(
            "resume text",
            {"type": "object"},
            "extract prompt",
        )
    )

    assert result["name"] == "Hafid Tazrout"
    assert mock_extract_with_gemini.await_count == 2


@patch("backend.api.profiles.service.db.create_profile", new_callable=AsyncMock)
@patch("backend.api.profiles.service.db.update_document_parse", new_callable=AsyncMock)
@patch("backend.api.profiles.service._load_document_for_user", new_callable=AsyncMock)
@patch("backend.api.profiles.service.extract_with_gemini", new_callable=AsyncMock)
def test_extract_resume_profile_repairs_empty_nested_sections(
    mock_extract_with_gemini,
    mock_load_document,
    mock_update_document_parse,
    mock_create_profile,
):
    mock_load_document.return_value = {
        "id": "resume-doc-1",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "kind": "resume",
        "raw_text": "Hafid Tazrout\nEngineering Director\nAcme Corp\nDirector of Engineering\nINSEAD MBA",
        "content": {"name": "Hafid Tazrout", "experience": [{"company": "Acme Corp"}]},
    }
    mock_extract_with_gemini.side_effect = [
        {
            "name": "Hafid Tazrout",
            "headline": "Engineering Director",
            "email": "hafid@example.com",
            "phone": "+1 555 123 4567",
            "location": "Singapore",
            "linkedin": "https://www.linkedin.com/in/hafid",
            "summary": "Engineering leader with global product and platform experience.",
            "skills": ["Leadership", "Strategy"],
            "languages": ["English", "French"],
            "experience": [{}, {}],
            "education": [{}],
        },
        {
            "experience": [
                {
                    "title": "Director of Engineering",
                    "company": "Acme Corp",
                    "location": "",
                    "start_date": "",
                    "end_date": "",
                    "description": "Led engineering organization and delivery.",
                    "bullets": ["Owned delivery", "Built leadership team"],
                }
            ],
            "education": [
                {
                    "degree": "MBA",
                    "school": "INSEAD",
                    "field_of_study": "",
                    "graduation_year": "",
                }
            ],
        },
    ]
    mock_create_profile.return_value = {"profile_id": "resume-profile-1"}

    result = asyncio.run(
        profile_service.extract_resume_profile(
            "11111111-1111-1111-1111-111111111111",
            "resume-doc-1",
        )
    )

    assert result["profile_id"] == "resume-profile-1"
    assert mock_extract_with_gemini.await_count == 2
    stored_content = mock_update_document_parse.await_args.kwargs["content"]
    assert stored_content["email"] == "hafid@example.com"
    assert stored_content["summary"] == "Engineering leader with global product and platform experience."
    assert stored_content["languages"] == ["English", "French"]
    assert stored_content["experience"][0]["company"] == "Acme Corp"
    assert stored_content["experience"][0]["bullets"] == ["Owned delivery", "Built leadership team"]
    assert stored_content["education"][0]["school"] == "INSEAD"


@patch("backend.api.profiles.service.db.create_profile", new_callable=AsyncMock)
@patch("backend.api.profiles.service.db.update_document_parse", new_callable=AsyncMock)
@patch("backend.api.profiles.service._load_document_for_user", new_callable=AsyncMock)
@patch("backend.api.profiles.service.extract_with_gemini", new_callable=AsyncMock)
def test_extract_job_profile_uses_url_context_for_url_documents(
    mock_extract_with_gemini,
    mock_load_document,
    mock_update_document_parse,
    mock_create_profile,
):
    mock_load_document.return_value = {
        "id": "jd-doc-1",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "kind": "job_description",
        "source_type": "url",
        "source_url": "https://example.com/jobs/backend",
        "raw_text": "Fallback scraped job description text",
    }
    mock_extract_with_gemini.return_value = {
        "company": "Acme",
        "role": "Backend Engineer",
        "requirements": ["Python", "APIs"],
        "nice_to_have": ["LLM systems"],
        "responsibilities": ["Build backend systems"],
        "summary": "Backend engineering role for APIs and AI systems.",
    }
    mock_create_profile.return_value = {"profile_id": "job-profile-1"}

    result = asyncio.run(
        profile_service.extract_job_profile(
            "11111111-1111-1111-1111-111111111111",
            "jd-doc-1",
        )
    )

    assert result["profile_id"] == "job-profile-1"
    extract_kwargs = mock_extract_with_gemini.await_args.kwargs
    assert extract_kwargs["tools"] == [{"url_context": {}}]
    assert "https://example.com/jobs/backend" in mock_extract_with_gemini.await_args.args[0]
    mock_update_document_parse.assert_awaited_once()


@patch("backend.api.profiles.service._load_document_for_user", new_callable=AsyncMock)
def test_extract_job_profile_rejects_linkedin_login_page(mock_load_document):
    mock_load_document.return_value = {
        "id": "jd-doc-1",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "kind": "job_description",
        "source_type": "url",
        "source_url": "https://www.linkedin.com/jobs/collections/top-applicant/?currentJobId=4381977518",
        "raw_text": "Sign in to LinkedIn session_redirect",
    }

    try:
        asyncio.run(
            profile_service.extract_job_profile(
                "11111111-1111-1111-1111-111111111111",
                "jd-doc-1",
            )
        )
    except ValueError as exc:
        assert "LinkedIn URL redirects to a login page" in str(exc)
    else:
        raise AssertionError("Expected LinkedIn login page guard to raise")
