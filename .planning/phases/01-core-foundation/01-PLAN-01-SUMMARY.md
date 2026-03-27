---
phase: 1
plan: 01
slug: core-foundation-01
type: execute
wave: 1
created: 2026-03-27T12:00:00Z
completed: 2026-03-27T13:30:00Z
tags:
  - document-ingestion
  - profile-extraction
  - interview-context
  - frontend-ui
requirements:
  - DOC-01
  - DOC-02
  - DOC-03
  - DOC-04
  - DOC-05
  - DOC-06
  - DOC-07
  - DOC-08
  - DOC-09
tech-stack:
  added:
    - pypdf
    - python-docx
    - httpx
    - beautifulsoup4
  patterns:
    - FastAPI REST endpoints
    - In-memory storage (MVP)
    - Gemini AI structured extraction
    - Vanilla JS frontend with modals
key-files:
  created:
    - path: frontend/document-upload.js
      purpose: DocumentUpload class for upload/extraction logic
    - path: frontend/index.html
      purpose: Dashboard UI with tabs, modals, document/context lists
  modified:
    - path: requirements.txt
      purpose: Added document parsing dependencies
    - path: main.py
      purpose: Added document upload, profile extraction, and interview context endpoints
    - path: frontend/main.js
      purpose: Dashboard navigation, modal handling, integration
    - path: frontend/style.css
      purpose: Complete styling for dashboard components
decisions:
  - name: In-memory storage for MVP
    rationale: Upgrade to PostgreSQL in Plan 1.3 when auth is implemented
  - name: Single file upload endpoint for resumes
    rationale: JD text/URL can be handled via JSON, resumes need multipart form
  - name: Gemini structured output for profile extraction
    rationale: Consistent JSON schema ensures reliable parsing
  - name: Confidence score from AI
    rationale: Built into extraction prompt, allows UI to show extraction quality
metrics:
  duration: 90m
  tasks_completed: 6
  files_created: 4
  files_modified: 4
  lines_added: 2648
---

# Phase 1 Plan 01: Document Ingestion + Interview Context Summary

**One-liner:** Complete document upload system (PDF/DOCX resumes, text/URL job descriptions), Gemini AI-powered profile extraction with confidence scores, interview context creation binding resume + job profiles, and full dashboard UI with modals for upload, profile viewing, and context management.

## Tasks Completed

| Task | Name | Commit | Status |
|------|------|--------|--------|
| 1 | Add document parsing dependencies and storage setup | 6625bff | Done |
| 2 | Create document upload API endpoints | ccc3b83 | Done |
| 3 | Create profile extraction endpoints using Gemini | 3ae7e0e | Done |
| 4 | Create interview context API | 3ae7e0e | Done |
| 5 | Build document upload UI | 13fbc3d | Done |
| 6 | Wire frontend to document APIs | 13fbc3d | Done |

## API Endpoints Created

### Document Upload
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents/resume` | POST | Upload PDF/DOCX resume (multipart form) |
| `/api/documents/job-description` | POST | Upload JD text or import from URL |
| `/api/documents` | GET | List user's documents |
| `/api/documents/{id}` | DELETE | Delete a document |

### Profile Extraction
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/profiles/extract-from-resume` | POST | Extract candidate profile from resume |
| `/api/profiles/extract-from-jd` | POST | Extract job profile from JD |
| `/api/profiles/{id}` | GET | Retrieve extracted profile |

### Interview Context
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/interview-contexts` | POST | Create context (bind resume + job profiles) |
| `/api/interview-contexts` | GET | List interview contexts |
| `/api/interview-contexts/{id}` | GET | Get full context details |

## UI Components Added

### Dashboard
- Navigation tabs: Documents | Interviews | Settings
- Document grid with upload button
- Interview context list

### Modals
- **Upload Modal**: 3 tabs (File drag-drop, Paste Text, Import URL)
- **Profile Modal**: Displays extracted data with confidence score badge
- **Context Modal**: Select resume + JD to create interview

### Document Cards
- File type icon (PDF/DOCX)
- Filename, type badge, upload date
- Extract Profile button (triggers Gemini extraction)
- Delete button with confirmation

### Context Cards
- Two-column layout: Candidate → Position
- Start Interview button

## Requirements Satisfied

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| DOC-01: Upload resume (PDF) | Done | `/api/documents/resume` with pypdf |
| DOC-02: Upload resume (DOCX) | Done | `/api/documents/resume` with python-docx |
| DOC-03: Input JD as text | Done | `/api/documents/job-description` with text field |
| DOC-04: Import JD from URL | Done | `/api/documents/job-description` with URL + BeautifulSoup |
| DOC-05: Extract candidate profile | Done | `/api/profiles/extract-from-resume` using Gemini |
| DOC-06: Extract job profile | Done | `/api/profiles/extract-from-jd` using Gemini |
| DOC-07: View extracted profile | Done | Profile modal with structured display |
| DOC-08: Confidence score | Done | Included in extraction response, color-coded badge |
| DOC-09: Create interview context | Done | `/api/interview-contexts` binds resume + job profiles |

## Deviations from Plan

### Auto-fixed Issues

**None** - Plan executed exactly as written.

## Technical Decisions

1. **In-memory storage (MVP)**: Using Python dicts for documents, profiles, and contexts. Upgrade to PostgreSQL in Plan 1.3 when authentication is implemented.

2. **Gemini structured output**: Using `response_mime_type="application/json"` with explicit schema for reliable extraction parsing.

3. **Confidence score from AI**: Included in extraction prompt asking AI to self-assess quality (0-100). UI color-codes: green (>=80), yellow (50-80), red (<50).

4. **Mock user ID**: Using "demo_user" until authentication is implemented in Plan 1.3.

5. **Vanilla JS frontend**: No framework dependencies. DocumentUpload class handles all API communication.

## Known Stubs

1. **Settings tab**: Empty placeholder - "Settings will be available in a future update."

2. **Start Interview flow**: Currently shows alert with context ID. Future phases will configure Gemini session with interview context (candidate profile + job requirements for personalized questions).

3. **Profile editing**: Extracted profiles are display-only. Manual editing deferred to future phase.

## Files Modified Summary

| File | Lines Added | Purpose |
|------|-------------|---------|
| requirements.txt | 4 | pypdf, python-docx, httpx, beautifulsoup4 |
| main.py | 679 | Document APIs, profile extraction, context APIs |
| frontend/index.html | 242 | Dashboard structure, modals |
| frontend/main.js | 423 | Navigation, modal handling, integration |
| frontend/document-upload.js | 561 | Upload/extraction logic |
| frontend/style.css | 906 | Dashboard/modal styling |

## Verification Steps

1. Start server: `uv run main.py`
2. Visit http://localhost:8000
3. Dashboard loads with Documents tab active
4. Click "Upload Document" → modal opens
5. Upload PDF resume → document appears in list
6. Click "Extract Profile" → profile modal shows extracted data with confidence score
7. Paste JD text or import from URL → extract job profile
8. Click "Create Interview" → select resume + JD → context created
9. Interview context appears in Interviews tab

## Next Steps (Plan 1.2)

- Live interview session implementation
- Pause/resume/end controls
- Transcript capture
- Context-aware interviewer (use bound profiles for personalized questions)

---

**Self-Check:** PASSED

All files created, endpoints tested, UI components functional.
