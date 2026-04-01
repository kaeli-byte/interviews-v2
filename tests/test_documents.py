"""Document API tests for setup interview flow."""
import asyncio
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

from docx import Document

from backend.api.documents import service as document_service


class TestDocuments:
    """Validate document ingestion routes used by `/setup`."""

    @patch("backend.api.documents.service.upload_resume", new_callable=AsyncMock)
    def test_upload_resume_file(self, mock_upload_resume, client, auth_headers):
        mock_upload_resume.return_value = {
            "document_id": "resume-doc-1",
            "filename": "resume.pdf",
            "type": "resume",
            "file_type": "PDF",
            "size": 128,
            "source_type": "file",
            "mime_type": "application/pdf",
            "storage_path": "resumes/user/resume.pdf",
            "parse_status": "parsed",
            "created_at": "2026-03-30T00:00:00Z",
        }

        response = client.post(
            "/api/documents/resume",
            headers=auth_headers,
            files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["document_id"] == "resume-doc-1"
        assert body["type"] == "resume"
        assert body["parse_status"] == "parsed"
        mock_upload_resume.assert_awaited_once()

    @patch("backend.api.documents.service.upload_job_description_file", new_callable=AsyncMock)
    def test_upload_job_description_file(self, mock_upload_jd, client, auth_headers):
        mock_upload_jd.return_value = {
            "document_id": "jd-doc-1",
            "filename": "jd.docx",
            "type": "job_description",
            "source_type": "file",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "storage_path": "job-descriptions/user/jd.docx",
            "parse_status": "parsed",
            "content_preview": "Senior engineer role...",
            "created_at": "2026-03-30T00:00:00Z",
        }

        response = client.post(
            "/api/documents/job-description/file",
            headers=auth_headers,
            files={"file": ("jd.docx", b"fake-docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["document_id"] == "jd-doc-1"
        assert body["source_type"] == "file"
        mock_upload_jd.assert_awaited_once()

    @patch("backend.api.documents.service.upload_job_description_text", new_callable=AsyncMock)
    def test_upload_job_description_text(self, mock_upload_text, client, auth_headers):
        mock_upload_text.return_value = {
            "document_id": "jd-text-1",
            "filename": "job-description.txt",
            "type": "job_description",
            "source_type": "text",
            "mime_type": "text/plain",
            "storage_path": None,
            "parse_status": "parsed",
            "content_preview": "We are hiring...",
            "created_at": "2026-03-30T00:00:00Z",
        }

        response = client.post(
            "/api/documents/job-description/text",
            headers=auth_headers,
            json={"text": "We are hiring a backend engineer"},
        )

        assert response.status_code == 200
        assert response.json()["source_type"] == "text"
        mock_upload_text.assert_awaited_once()

    @patch("backend.api.documents.service.upload_job_description_url", new_callable=AsyncMock)
    def test_upload_job_description_url(self, mock_upload_url, client, auth_headers):
        mock_upload_url.return_value = {
            "document_id": "jd-url-1",
            "filename": "job-description-url.txt",
            "type": "job_description",
            "source_type": "url",
            "mime_type": "text/plain",
            "storage_path": None,
            "parse_status": "parsed",
            "content_preview": "Role fetched from URL...",
            "created_at": "2026-03-30T00:00:00Z",
        }

        response = client.post(
            "/api/documents/job-description/url",
            headers=auth_headers,
            json={"url": "https://example.com/jobs/backend"},
        )

        assert response.status_code == 200
        assert response.json()["source_type"] == "url"
        mock_upload_url.assert_awaited_once()


def build_docx_bytes(*paragraphs: str) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@patch("backend.api.documents.service.db.create_document", new_callable=AsyncMock)
@patch("backend.api.documents.service.upload_bytes_to_storage", new_callable=AsyncMock)
def test_upload_resume_parses_normalizes_and_persists(mock_upload_storage, mock_create_document):
    mock_create_document.return_value = {
        "id": "00000000-0000-0000-0000-000000000001",
        "filename": "resume.docx",
        "kind": "resume",
        "source_type": "file",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "storage_path": "resumes/user/file.docx",
        "parse_status": "parsed",
        "created_at": "2026-03-30T00:00:00Z",
    }

    content = build_docx_bytes("Hafid Tazrout", " Senior   Product Designer ", "", "Built interview systems")
    result = asyncio.run(document_service.upload_resume("11111111-1111-1111-1111-111111111111", "resume.docx", content))

    assert result["document_id"] == "00000000-0000-0000-0000-000000000001"
    create_kwargs = mock_create_document.await_args.kwargs
    assert create_kwargs["kind"] == "resume"
    assert create_kwargs["source_type"] == "file"
    assert create_kwargs["raw_text"] == "Hafid Tazrout\nSenior Product Designer\n\nBuilt interview systems"
    assert create_kwargs["content"]["possible_names"] == ["Hafid Tazrout"]
    assert UUID(create_kwargs["user_id"])
    assert create_kwargs["storage_path"].startswith("resumes/11111111-1111-1111-1111-111111111111/")
    mock_upload_storage.assert_awaited_once()


def test_extract_resume_hints_returns_weak_signals():
    raw_text = """Hafid Tazrout
Engineering Director
hafid@example.com
+1 555 123 4567
Singapore
https://www.linkedin.com/in/hafid

SUMMARY
Leader building high-performing product and engineering teams.

SKILLS
Leadership, Product Strategy, DFM

EXPERIENCE
Acme Corp (Singapore) Jan 2020 - Present
Director of Engineering
- Led platform and hiring strategy
- Built cross-functional delivery processes

EDUCATION
INSEAD, Business Administration 2021
MBA

LANGUAGES
English, French
"""

    result = document_service.extract_resume_hints(raw_text)

    assert result["possible_names"] == ["Hafid Tazrout"]
    assert result["possible_headlines"] == ["Engineering Director"]
    assert result["emails_found"] == ["hafid@example.com"]
    assert result["phones_found"] == ["+1 555 123 4567"]
    assert result["links_found"] == ["https://www.linkedin.com/in/hafid"]
    assert result["detected_sections"] == ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION", "LANGUAGES"]
    assert result["section_preview"]["EXPERIENCE"][0] == "Acme Corp (Singapore) Jan 2020 - Present"
    assert result["section_preview"]["EDUCATION"][0] == "INSEAD, Business Administration 2021"


def test_parse_document_content_rejects_invalid_docx():
    try:
        document_service.parse_document_content("resume.docx", b"not-a-real-docx")
    except ValueError as exc:
        assert str(exc) == "Could not parse DOCX file"
    else:
        raise AssertionError("Expected parse_document_content to raise ValueError")


@patch("backend.api.documents.service.db.create_document", new_callable=AsyncMock)
def test_upload_job_description_text_trims_and_persists(mock_create_document):
    mock_create_document.return_value = {
        "id": "00000000-0000-0000-0000-000000000002",
        "filename": "job-description.txt",
        "kind": "job_description",
        "source_type": "text",
        "mime_type": "text/plain",
        "storage_path": None,
        "parse_status": "parsed",
        "created_at": "2026-03-30T00:00:00Z",
    }

    result = asyncio.run(
        document_service.upload_job_description_text(
            "11111111-1111-1111-1111-111111111111",
            "  Senior engineer role\n\n  Build   AI systems  ",
        )
    )

    assert result["document_id"] == "00000000-0000-0000-0000-000000000002"
    assert mock_create_document.await_args.kwargs["raw_text"] == "Senior engineer role\n\nBuild AI systems"


@patch("backend.api.documents.service.db.create_document", new_callable=AsyncMock)
@patch("backend.api.documents.service.httpx.AsyncClient")
def test_upload_job_description_url_extracts_readable_text(mock_httpx_client, mock_create_document):
    response = AsyncMock()
    response.text = """
        <html>
          <body>
            <nav>Ignore me</nav>
            <main>
              <h1>Senior Product Designer</h1>
              <p>Lead candidate experience.</p>
            </main>
            <script>console.log('ignore')</script>
          </body>
        </html>
    """
    response.raise_for_status = Mock()

    client_context = AsyncMock()
    client_context.get.return_value = response
    mock_httpx_client.return_value.__aenter__.return_value = client_context

    mock_create_document.return_value = {
        "id": "00000000-0000-0000-0000-000000000003",
        "filename": "job-description-url.txt",
        "kind": "job_description",
        "source_type": "url",
        "mime_type": "text/plain",
        "storage_path": None,
        "parse_status": "parsed",
        "created_at": "2026-03-30T00:00:00Z",
    }

    result = asyncio.run(
        document_service.upload_job_description_url(
            "11111111-1111-1111-1111-111111111111",
            "https://example.com/jobs/designer",
        )
    )

    assert result["document_id"] == "00000000-0000-0000-0000-000000000003"
    create_kwargs = mock_create_document.await_args.kwargs
    assert create_kwargs["source_url"] == "https://example.com/jobs/designer"
    assert create_kwargs["raw_text"] == "Senior Product Designer\nLead candidate experience."
