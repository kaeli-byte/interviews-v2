"""Deterministic document parsing helpers."""
import re
from io import BytesIO
from pathlib import Path

SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "LANGUAGES"}

MONTH_RE = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
EMAIL_RE = r"[\w.\-+]+@[\w.\-]+\.\w+"
PHONE_RE = r"(\+\d[\d\s\-()]{7,}\d)"
LINKEDIN_RE = r"https?://(?:www\.)?linkedin\.com/in/[^\s]+"

def normalize_extracted_text(text: str) -> str:
    """Preserve useful line boundaries while cleaning noisy whitespace."""
    lines = []
    blank_streak = 0

    for raw_line in text.splitlines():
        line = " ".join(raw_line.replace("\xa0", " ").split()).strip()

        if re.fullmatch(r"page \d+ of \d+", line, flags=re.IGNORECASE):
            continue

        if not line:
            blank_streak += 1
            if blank_streak <= 1:
                lines.append("")
            continue

        blank_streak = 0
        lines.append(line)

    return "\n".join(lines).strip()


def read_pdf_content(file_bytes: bytes) -> str:
    """Extract text from a PDF byte payload."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    return normalize_extracted_text("\n".join(page.extract_text() or "" for page in reader.pages))


def read_docx_content(file_bytes: bytes) -> str:
    """Extract text from a DOCX byte payload."""
    from docx import Document

    document = Document(BytesIO(file_bytes))
    return normalize_extracted_text("\n".join(paragraph.text for paragraph in document.paragraphs))


def parse_document_content(filename: str, content: bytes) -> str:
    """Extract text from PDF or DOCX uploads."""
    if not filename:
        raise ValueError("Filename is required")

    file_ext = Path(filename).suffix.lower()
    try:
        if file_ext == ".pdf":
            parsed_text = read_pdf_content(content)
        elif file_ext == ".docx":
            parsed_text = read_docx_content(content)
        else:
            raise ValueError("Unsupported file type")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not parse {file_ext[1:].upper()} file") from exc

    if not parsed_text:
        raise ValueError(f"{file_ext[1:].upper()} file did not contain readable text")
    return parsed_text


def split_resume_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"HEADER": []}
    current = "HEADER"

    for line in text.splitlines():
        upper = line.strip().upper()
        if upper in SECTION_HEADERS:
            current = upper
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return sections


def extract_header_hints(lines: list[str]) -> dict:
    non_empty = [line for line in lines if line.strip()]
    text = "\n".join(non_empty)

    return {
        "possible_names": non_empty[:1],
        "possible_headlines": non_empty[1:2],
        "emails_found": re.findall(EMAIL_RE, text),
        "phones_found": re.findall(PHONE_RE, text),
        "links_found": re.findall(r"https?://\S+", text),
        "header_lines": non_empty[:8],
    }


def extract_resume_hints(raw_text: str) -> dict:
    sections = split_resume_sections(raw_text)
    non_empty_sections = {
        name: [line for line in lines if line.strip()]
        for name, lines in sections.items()
        if any(line.strip() for line in lines)
    }
    return {
        **extract_header_hints(sections.get("HEADER", [])),
        "detected_sections": [name for name in non_empty_sections.keys() if name != "HEADER"],
        "section_preview": {
            name: lines[:5]
            for name, lines in non_empty_sections.items()
        },
    }
