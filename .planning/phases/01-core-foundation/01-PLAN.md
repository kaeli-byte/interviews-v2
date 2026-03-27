---
phase: 01-core-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [requirements.txt, main.py, uploads/, frontend/index.html, frontend/main.js]
autonomous: true
requirements: [DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08, DOC-09]
user_setup: []

must_haves:
  truths:
    - "User can upload a PDF resume and see it in the document list"
    - "User can upload a DOCX resume and see it in the document list"
    - "User can paste job description text and see extracted job profile"
    - "User can import job description from URL and see extracted content"
    - "User can view extracted candidate profile with confidence score"
    - "User can create interview context binding resume profile + job profile"
  artifacts:
    - path: "main.py"
      provides: "Document upload and profile extraction endpoints"
      exports: ["POST /api/documents/resume", "POST /api/documents/job-description", "GET /api/documents", "DELETE /api/documents/{id}", "POST /api/profiles/extract-from-resume", "POST /api/profiles/extract-from-jd", "POST /api/interview-contexts", "GET /api/interview-contexts"]
    - path: "requirements.txt"
      provides: "Document parsing dependencies"
      contains: "pypdf, python-docx, httpx, beautifulsoup4"
    - path: "frontend/index.html"
      provides: "Document upload UI structure"
    - path: "frontend/main.js"
      provides: "Upload handling and profile display logic"
  key_links:
    - from: "frontend/main.js"
      to: "/api/documents/resume"
      via: "FormData POST request"
      pattern: "fetch.*api/documents/resume.*POST"
    - from: "main.py"
      to: "gemini_live.py"
      via: "Gemini client for profile extraction"
      pattern: "client\\.aio\\.live\\.connect|client\\.generate_content"
---

<objective>
Enable users to upload resumes (PDF, DOCX), import job descriptions (text or URL), extract profiles using Gemini AI, and create interview contexts binding resume + job profiles.

Purpose: Document ingestion and profile extraction form the foundation for personalized interview practice. Without understanding the candidate and target role, interview sessions lack context and relevance.

Output: Working document upload system, AI-powered profile extraction, interview context creation UI and API.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-core-foundation/01-CONTEXT.md
@.planning/phases/01-core-foundation/01-UI-SPEC.md
@main.py
@gemini_live.py
@frontend/index.html
@frontend/main.js
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add document parsing dependencies and storage setup</name>
  <files>requirements.txt, uploads/</files>
  <action>
    Add the following dependencies to requirements.txt:
    - pypdf (PDF parsing per D-01)
    - python-docx (DOCX parsing per D-02)
    - httpx (async HTTP for URL import per D-03)
    - beautifulsoup4 (HTML parsing for URL import per D-03)

    Create uploads/ directory for document storage (MVP local filesystem per CONTEXT.md).

    Run: pip install -r requirements.txt to install new dependencies.
  </action>
  <verify>
    <automated>python -c "import pypdf; import docx; import httpx; from bs4 import BeautifulSoup; print('All imports OK')"</automated>
  </verify>
  <done>
    - pypdf, python-docx, httpx, beautifulsoup4 in requirements.txt and importable
    - uploads/ directory exists
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create document upload API endpoints</name>
  <files>main.py</files>
  <action>
    Add to main.py (after existing routes, before __main__ block):

    1. POST /api/documents/resume - accepts multipart form data with 'file' field
       - Validate file type (PDF or DOCX only)
       - Generate unique filename (uuid4 + original extension)
       - Save to uploads/{user_id}/ directory
       - Return: {document_id, filename, type, size, created_at}

    2. POST /api/documents/job-description - accepts JSON {text?: string, url?: string}
       - If text provided: store directly
       - If url provided: fetch with httpx, parse with BeautifulSoup (extract main text content)
       - Save to uploads/{user_id}/jd_{timestamp}.txt
       - Return: {document_id, content_preview, source_type}

    3. GET /api/documents - lists user's documents (mock user_id for MVP)
       - Return: [{document_id, filename, type, created_at}]

    4. DELETE /api/documents/{id} - deletes document file
       - Return: {success: true}

    For MVP: Use mock user_id = "demo_user" until auth is implemented in Plan 1.3.
    Add CORS origins for localhost development.
  </action>
  <verify>
    <automated>curl -X POST http://localhost:8000/api/documents/job-description -H "Content-Type: application/json" -d '{"text": "Software Engineer role"}' | python -m json.tool</automated>
  </verify>
  <done>
    - All four endpoints respond correctly
    - PDF upload returns document_id
    - JD from text stores content and returns preview
    - Document list returns stored documents
    - Delete removes file from filesystem
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create profile extraction endpoints using Gemini</name>
  <files>main.py</files>
  <action>
    Add to main.py:

    1. POST /api/profiles/extract-from-resume - accepts {document_id}
       - Read resume file content (PDF via pypdf, DOCX via python-docx)
       - Call Gemini API to extract: name, headline, skills[], experience[], education[], confidence_score (0-100)
       - Use structured output (response_format or JSON schema)
       - Store extracted profile (in-memory dict for MVP)
       - Return: {profile_id, name, headline, skills, experience, education, confidence_score}

    2. POST /api/profiles/extract-from-jd - accepts {document_id}
       - Read JD content
       - Call Gemini API to extract: company, role, requirements[], nice_to_have[], responsibilities[]
       - Store extracted job profile
       - Return: {profile_id, company, role, requirements, nice_to_have, responsibilities}

    3. GET /api/profiles/{id} - retrieve extracted profile
       - Return stored profile data

    Extraction prompts should be specific:
    - Resume: "Extract candidate information as JSON with fields: name, headline, skills (array), experience (array with title, company, duration, description), education. Also provide confidence_score 0-100 based on text clarity."
    - JD: "Extract job information as JSON: company name, role title, requirements (array), nice_to_have (array), responsibilities (array)."
  </action>
  <verify>
    <automated>curl -X POST http://localhost:8000/api/profiles/extract-from-jd -H "Content-Type: application/json" -d '{"document_id": "test123"}' 2>&1 | python -m json.tool</automated>
  </verify>
  <done>
    - Resume extraction returns structured profile with confidence_score
    - JD extraction returns structured job profile
    - Profile retrieval by ID works
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Create interview context API</name>
  <files>main.py</files>
  <action>
    Add to main.py:

    1. POST /api/interview-contexts - accepts {resume_profile_id, job_profile_id}
       - Validate both profiles exist
       - Create context binding: {context_id, resume_profile, job_profile, created_at}
       - Store in memory (upgrade to DB in Plan 1.3)
       - Return: {context_id, resume_profile, job_profile}

    2. GET /api/interview-contexts - lists user's contexts
       - Return: [{context_id, resume_profile_summary, job_profile_summary, created_at}]

    3. GET /api/interview-contexts/{id} - get full context details
       - Return: {context_id, resume_profile, job_profile, created_at}

    Context enables personalized interview questions based on resume gaps vs job requirements.
  </action>
  <verify>
    <automated>curl http://localhost:8000/api/interview-contexts | python -m json.tool</automated>
  </verify>
  <done>
    - Create context binds resume + job profiles
    - List returns all contexts
    - Get by ID returns full context with both profiles
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 5: Build document upload UI</name>
  <files>frontend/index.html, frontend/main.js</files>
  <action>
    Update frontend/index.html:

    Add new sections after auth-section:
    1. Dashboard section with:
       - Navigation tabs: Documents | Interviews | Settings
       - Upload button (opens modal)
       - Document list grid

    2. Document Upload Modal:
       - Tab interface: Upload File | Paste Text | Import from URL
       - File tab: drag-and-drop zone, file picker (accept .pdf, .docx)
       - Text tab: textarea for JD paste
       - URL tab: input field + Import button
       - Processing indicator during upload

    3. Profile View Panel:
       - Display extracted data (name, headline, skills as badges, experience as cards)
       - Confidence score badge (color: green if >80, yellow if 50-80, red if <50)

    4. Interview Context Creation:
       - Two-column layout: Resume Profile | Job Profile
       - Dropdown to select resume (if multiple)
       - Dropdown to select JD
       - "Create Interview" button

    Follow UI-SPEC.md for spacing (4px base), colors (#0ea5e9 accent), and typography.
  </action>
  <verify>
    <automated>MISSING - Wave 0 must create frontend test harness first</automated>
  </verify>
  <done>
    - Dashboard visible after auth (mock for now)
    - Upload modal has 3 tabs (File, Text, URL)
    - Document list shows uploaded files
    - Profile view displays extracted data with confidence score
    - Interview context creation form binds resume + job
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 6: Wire frontend to document APIs</name>
  <files>frontend/main.js</files>
  <action>
    Add to frontend/main.js:

    1. DocumentUpload class:
       - handleFileUpload(file): FormData POST to /api/documents/resume
       - handleTextSubmit(text): POST to /api/documents/job-description
       - handleUrlSubmit(url): POST to /api/documents/job-description with URL
       - onUploadComplete(document): callback to refresh list

    2. fetchDocuments(): GET /api/documents, render document list
       - Each document shows: filename, type icon, upload date, delete button

    3. deleteDocument(id): DELETE /api/documents/{id}, refresh list

    4. extractResumeProfile(documentId): POST /api/profiles/extract-from-resume
       - Show loading state
       - Display extracted profile in panel

    5. extractJobProfile(documentId): POST /api/profiles/extract-from-jd

    6. createInterviewContext(resumeProfileId, jobProfileId): POST /api/interview-contexts
       - On success: show context created, enable "Start Interview" button

    Update UI state management:
    - auth-section → dashboard-section → upload-modal → profile-view → context-created
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Upload button opens modal
    - File upload shows progress then document in list
    - Text/URL JD import works
    - Extract buttons trigger profile extraction
    - Profile data displays with confidence score
    - Create Interview button binds profiles
  </done>
</task>

</tasks>

<verification>
Overall phase verification:
1. Upload PDF resume → see in document list → extract profile → see extracted data with confidence score
2. Upload DOCX resume → same flow works
3. Paste JD text → extract job profile → see company, role, requirements
4. Import JD from URL → content extracted → profile created
5. Select resume + job → create interview context → context appears in list
</verification>

<success_criteria>
- All 9 requirements (DOC-01 through DOC-09) implemented
- User can complete: upload → extract → bind flow without errors
- Confidence scores visible on extracted profiles
- Interview context created successfully with both profiles bound
- Frontend UI follows UI-SPEC.md design (spacing, colors, typography)
</success_criteria>

<output>
After completion, create `.planning/phases/01-core-foundation/01-core-foundation-01-SUMMARY.md` documenting:
- Endpoints created with request/response formats
- UI components added
- Any deviations from plan
- Known issues or technical debt
</output>
