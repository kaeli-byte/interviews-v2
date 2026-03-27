# Context: Phase 1 - Core Foundation

**Phase:** 1 - Core Foundation
**Created:** 2026-03-27
**Mode:** Autonomous (YOLO)

## Prior Context

From PROJECT.md:
- Tech Stack: FastAPI (Python) backend, vanilla JS frontend
- AI Runtime: Gemini Live API (required)
- Key decisions already made:
  - Backend owns session lifecycle
  - Versioned database-backed agent configs
  - Postgres for metadata, Redis for ephemeral state
  - Voice-first MVP

## Decisions

### Document Ingestion

| Decision | Choice | Rationale |
|----------|--------|-----------|
| PDF parsing | pypdf | Lightweight, covers 90% of resumes |
| DOCX parsing | python-docx | Standard library |
| URL JD import | httpx + beautifulsoup4 | Simple readability extraction |
| Text input | Direct text field | No parsing needed |
| Profile extraction | AI-powered (Gemini) | Use existing Gemini API for extraction |
| Extraction quality scoring | Confidence score from Gemini | Built into extraction response |
| Storage | Local filesystem (MVP) | Simple, upgrade to Vercel Blob later |

### Interview Context

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Context binding | Resume profile + Job profile | As specified in IDEAS_HANDOFF.md |
| Profile storage | PostgreSQL | Core metadata storage |
| Multiple resumes | Support multiple, bind one active | Per IDEAS_HANDOFF.md |

### Live Interview Sessions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Session lifecycle | Backend-owned state machine | PROJECT.md decision |
| Transcript capture | Incremental (every 10-15 sec) | Prevents data loss on disconnect |
| Pause/Resume | Full state preservation | Required for MVP |
| Reconnection | Resume from last checkpoint | Per research pitfalls |
| Gemini integration | Existing gemini_live.py | Already validated in codebase |

### Authentication

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth solution | Simple email/password | Out of scope for v1: OAuth |
| Session management | JWT tokens | Standard, simple to implement |
| Password hashing | bcrypt | Standard security |
| User model | PostgreSQL | Same as other metadata |

### Database

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | SQLAlchemy 2.0 + asyncpg | Per research, async-first |
| Schema migration | Alembic | Standard for SQLAlchemy |
| Connection pooling | asyncpg built-in | Per research |

## Scope

This phase includes:
- Document upload (PDF, DOCX, text, URL)
- Profile extraction using Gemini
- Interview context creation
- Live session with Gemini Live (existing + enhancements)
- Basic authentication
- User document management

## Out of Scope (from PROJECT.md)

- Manual document field editing
- Real-time analytics during sessions
- Video in interviews
- Mobile apps
- Multi-language support

## Deferred Ideas

Noted for future phases:
- OAuth login (Phase 2+)
- Video recording (Phase 2+)
- Mobile apps (future)
- Multi-language (future)

---
*Context created: 2026-03-27 for Phase 1*