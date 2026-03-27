import asyncio
import base64
import json
import logging
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gemini_live import GeminiLive

# Load environment variables
load_dotenv()

# Configure logging - DEBUG for our modules, INFO for everything else
logging.basicConfig(level=logging.INFO)
logging.getLogger("gemini_live").setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL", "gemini-3.1-flash-live-preview")

# Mock user ID for MVP (until auth is implemented)
MOCK_USER_ID = "demo_user"

# Uploads directory setup
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# In-memory storage for MVP (upgrade to DB in Plan 1.3)
documents_db: Dict[str, Dict[str, Any]] = {}
profiles_db: Dict[str, Dict[str, Any]] = {}
interview_contexts_db: Dict[str, Dict[str, Any]] = {}
sessions_db: Dict[str, Dict[str, Any]] = {}

# Session state machine constants
SESSION_STATE_PENDING = "pending"
SESSION_STATE_ACTIVE = "active"
SESSION_STATE_PAUSED = "paused"
SESSION_STATE_ENDED = "ended"

# Valid state transitions
VALID_TRANSITIONS = {
    SESSION_STATE_PENDING: [SESSION_STATE_ACTIVE],
    SESSION_STATE_ACTIVE: [SESSION_STATE_PAUSED, SESSION_STATE_ENDED],
    SESSION_STATE_PAUSED: [SESSION_STATE_ACTIVE, SESSION_STATE_ENDED],
    SESSION_STATE_ENDED: []
}

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for Gemini Live with session management."""

    # Validate session if session_id provided
    if session_id:
        if session_id not in sessions_db:
            logger.warning(f"WebSocket connection rejected: session {session_id} not found")
            await websocket.close(code=4004, reason="Session not found")
            return

        session = sessions_db[session_id]
        if session["state"] != SESSION_STATE_ACTIVE:
            logger.warning(f"WebSocket connection rejected: session {session_id} not active (state={session['state']})")
            await websocket.close(code=4005, reason="Session not active")
            return

        logger.info(f"WebSocket connection accepted for session {session_id}")
    else:
        logger.info("WebSocket connection accepted (no session_id - demo mode)")

    await websocket.accept()

    logger.info("WebSocket connection established")

    audio_input_queue = asyncio.Queue()
    video_input_queue = asyncio.Queue()
    text_input_queue = asyncio.Queue()

    # Transcript persistence callback
    def save_transcript_to_session(transcript_entries):
        if session_id and session_id in sessions_db:
            sessions_db[session_id]["transcript"].extend(transcript_entries)
            logger.debug(f"Saved {len(transcript_entries)} transcript entries to session {session_id}")

    async def audio_output_callback(data):
        await websocket.send_bytes(data)

    async def audio_interrupt_callback():
        pass

    gemini_client = GeminiLive(
        api_key=GEMINI_API_KEY, model=MODEL, input_sample_rate=16000
    )

    # Set transcript callback for session persistence
    gemini_client.set_transcript_callback(save_transcript_to_session)

    async def receive_from_client():
        try:
            while True:
                message = await websocket.receive()

                if message.get("bytes"):
                    await audio_input_queue.put(message["bytes"])
                elif message.get("text"):
                    text = message["text"]
                    try:
                        payload = json.loads(text)
                        # Handle session control messages
                        if isinstance(payload, dict) and payload.get("type") == "session_control":
                            action = payload.get("action")
                            if session_id and session_id in sessions_db:
                                if action == "pause":
                                    sessions_db[session_id]["state"] = SESSION_STATE_PAUSED
                                    gemini_client.pause_session()
                                    await websocket.send_json({"type": "session_paused"})
                                    logger.info(f"Session {session_id} paused via WebSocket")
                                elif action == "resume":
                                    sessions_db[session_id]["state"] = SESSION_STATE_ACTIVE
                                    gemini_client.resume_session()
                                    await websocket.send_json({"type": "session_resumed"})
                                    logger.info(f"Session {session_id} resumed via WebSocket")
                                elif action == "end":
                                    result = gemini_client.end_session()
                                    sessions_db[session_id]["state"] = SESSION_STATE_ENDED
                                    sessions_db[session_id]["transcript"] = result.get("final_transcript", [])
                                    await websocket.send_json({"type": "session_ended", "transcript": result.get("final_transcript", [])})
                                    logger.info(f"Session {session_id} ended via WebSocket")
                                    return  # Exit the receive loop
                            continue

                        if isinstance(payload, dict) and payload.get("type") == "image":
                            logger.info(f"Received image chunk from client: {len(payload['data'])} base64 chars")
                            image_data = base64.b64decode(payload["data"])
                            await video_input_queue.put(image_data)
                            continue
                    except json.JSONDecodeError:
                        pass

                    await text_input_queue.put(text)
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error receiving from client: {e}")

    receive_task = asyncio.create_task(receive_from_client())

    async def run_session():
        async for event in gemini_client.start_session(
            audio_input_queue=audio_input_queue,
            video_input_queue=video_input_queue,
            text_input_queue=text_input_queue,
            audio_output_callback=audio_output_callback,
            audio_interrupt_callback=audio_interrupt_callback,
            session_id=session_id,
        ):
            if event:
                # Forward events (transcriptions, etc) to client
                await websocket.send_json(event)

    try:
        await run_session()
    except Exception as e:
        import traceback
        logger.error(f"Error in Gemini session: {type(e).__name__}: {e}\n{traceback.format_exc()}")
    finally:
        receive_task.cancel()
        # Ensure websocket is closed if not already
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# Document Upload API Endpoints
# ============================================================================

def get_user_dir(user_id: str = MOCK_USER_ID) -> Path:
    """Get or create user's upload directory."""
    user_dir = UPLOADS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def read_pdf_content(file_path: Path) -> str:
    """Extract text from PDF file using pypdf."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")


def read_docx_content(file_path: Path) -> str:
    """Extract text from DOCX file using python-docx."""
    from docx import Document
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read DOCX: {str(e)}")


@app.post("/api/documents/resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume (PDF or DOCX format).
    Returns document_id, filename, type, size, created_at.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx"}
    file_ext = Path(file.filename or "").suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{file.filename}"

    # Save to user's upload directory
    user_dir = get_user_dir()
    file_path = user_dir / safe_filename

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Store document metadata
    doc_id = uuid.uuid4().hex
    document = {
        "document_id": doc_id,
        "filename": file.filename,
        "stored_filename": safe_filename,
        "type": "resume",
        "file_type": file_ext[1:].upper(),  # PDF or DOCX
        "size": len(content),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": MOCK_USER_ID,
        "file_path": str(file_path)
    }
    documents_db[doc_id] = document

    return JSONResponse(content=document)


@app.post("/api/documents/job-description")
async def upload_job_description(data: dict):
    """
    Upload a job description (text or URL).
    Request body: {"text"?: string, "url"?: string}
    Returns document_id, content_preview, source_type.
    """
    text = data.get("text")
    url = data.get("url")

    if not text and not url:
        raise HTTPException(status_code=400, detail="Either 'text' or 'url' must be provided")

    if text and url:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'url', not both")

    # Fetch content from URL if provided
    if url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

            # Parse HTML and extract main text
            soup = BeautifulSoup(response.text, "html.parser")
            # Remove script and style tags
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
        source_type = "url"
    else:
        source_type = "text"

    # Generate unique filename and save
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"jd_{timestamp}.txt"

    user_dir = get_user_dir()
    file_path = user_dir / safe_filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logger.error(f"Error saving JD file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Store document metadata
    doc_id = uuid.uuid4().hex
    content_preview = text[:200] + "..." if len(text) > 200 else text
    document = {
        "document_id": doc_id,
        "filename": safe_filename,
        "type": "job_description",
        "source_type": source_type,
        "content": text,
        "content_preview": content_preview,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": MOCK_USER_ID,
        "file_path": str(file_path)
    }
    documents_db[doc_id] = document

    return JSONResponse(content={
        "document_id": doc_id,
        "content_preview": content_preview,
        "source_type": source_type,
        "filename": safe_filename
    })


@app.get("/api/documents")
async def list_documents():
    """
    List all documents for the current user.
    Returns: [{document_id, filename, type, created_at}]
    """
    user_docs = [
        {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "type": doc["type"],
            "file_type": doc.get("file_type", ""),
            "created_at": doc["created_at"]
        }
        for doc in documents_db.values()
        if doc.get("user_id") == MOCK_USER_ID
    ]
    return JSONResponse(content=user_docs)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document by ID.
    Returns: {success: true}
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents_db[document_id]

    # Delete file from filesystem
    file_path = Path(doc.get("file_path", ""))
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

    # Remove from database
    del documents_db[document_id]

    return JSONResponse(content={"success": True})


# ============================================================================
# Profile Extraction API Endpoints (using Gemini AI)
# ============================================================================

async def extract_with_gemini(content: str, prompt: str, response_schema: dict) -> dict:
    """
    Extract structured data using Gemini API.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    full_prompt = f"""{prompt}

Return ONLY valid JSON matching this schema. Do not include any explanation or markdown formatting.

Content to analyze:
---
{content}
---
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        )

        if response.text:
            return json.loads(response.text)
        else:
            raise HTTPException(status_code=500, detail="Gemini returned empty response")
    except Exception as e:
        logger.error(f"Gemini extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Profile extraction failed: {str(e)}")


@app.post("/api/profiles/extract-from-resume")
async def extract_resume_profile(data: dict):
    """
    Extract candidate profile from resume using Gemini AI.
    Request body: {"document_id": str}
    Returns: {profile_id, name, headline, skills, experience, education, confidence_score}
    """
    document_id = data.get("document_id")

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents_db[document_id]

    if doc["type"] != "resume":
        raise HTTPException(status_code=400, detail="Document is not a resume")

    # Read resume content
    file_path = Path(doc["file_path"])
    if doc["file_type"] == "PDF":
        content = read_pdf_content(file_path)
    elif doc["file_type"] == "DOCX":
        content = read_docx_content(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Resume appears to be empty")

    # Define response schema for structured output
    resume_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "headline": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company": {"type": "string"},
                        "duration": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["title", "company", "duration", "description"]
                }
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": "string"},
                        "year": {"type": "string"}
                    },
                    "required": ["institution", "degree"]
                }
            },
            "confidence_score": {"type": "number"}
        },
        "required": ["name", "headline", "skills", "experience", "education", "confidence_score"]
    }

    prompt = """Extract candidate information from this resume as JSON with the following fields:
- name: Full name of the candidate
- headline: Professional headline/title (e.g., "Senior Software Engineer")
- skills: Array of technical and soft skills
- experience: Array of work experiences with title, company, duration, description
- education: Array of education entries with institution, degree, year
- confidence_score: Number 0-100 indicating how confident you are in the extraction quality based on text clarity and completeness"""

    extracted_data = await extract_with_gemini(content, prompt, resume_schema)

    # Store profile
    profile_id = uuid.uuid4().hex
    profile = {
        "profile_id": profile_id,
        "type": "resume",
        "document_id": document_id,
        "name": extracted_data.get("name", ""),
        "headline": extracted_data.get("headline", ""),
        "skills": extracted_data.get("skills", []),
        "experience": extracted_data.get("experience", []),
        "education": extracted_data.get("education", []),
        "confidence_score": extracted_data.get("confidence_score", 0),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": MOCK_USER_ID
    }
    profiles_db[profile_id] = profile

    return JSONResponse(content=profile)


@app.post("/api/profiles/extract-from-jd")
async def extract_job_profile(data: dict):
    """
    Extract job profile from job description using Gemini AI.
    Request body: {"document_id": str}
    Returns: {profile_id, company, role, requirements, nice_to_have, responsibilities}
    """
    document_id = data.get("document_id")

    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents_db[document_id]

    if doc["type"] != "job_description":
        raise HTTPException(status_code=400, detail="Document is not a job description")

    # Read JD content
    content = doc.get("content", "")
    if not content:
        file_path = Path(doc["file_path"])
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading JD file: {e}")
            raise HTTPException(status_code=500, detail="Failed to read job description")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Job description appears to be empty")

    # Define response schema for structured output
    jd_schema = {
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "role": {"type": "string"},
            "requirements": {"type": "array", "items": {"type": "string"}},
            "nice_to_have": {"type": "array", "items": {"type": "string"}},
            "responsibilities": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["company", "role", "requirements", "nice_to_have", "responsibilities"]
    }

    prompt = """Extract job information from this job description as JSON with the following fields:
- company: Name of the hiring company
- role: Job title/position
- requirements: Array of required qualifications/skills
- nice_to_have: Array of preferred qualifications/skills
- responsibilities: Array of key job responsibilities"""

    extracted_data = await extract_with_gemini(content, prompt, jd_schema)

    # Store profile
    profile_id = uuid.uuid4().hex
    profile = {
        "profile_id": profile_id,
        "type": "job_description",
        "document_id": document_id,
        "company": extracted_data.get("company", ""),
        "role": extracted_data.get("role", ""),
        "requirements": extracted_data.get("requirements", []),
        "nice_to_have": extracted_data.get("nice_to_have", []),
        "responsibilities": extracted_data.get("responsibilities", []),
        "created_at": datetime.utcnow().isoformat(),
        "user_id": MOCK_USER_ID
    }
    profiles_db[profile_id] = profile

    return JSONResponse(content=profile)


@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """
    Retrieve an extracted profile by ID.
    Returns: Profile data (resume or job_description)
    """
    if profile_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profiles_db[profile_id]
    return JSONResponse(content=profile)


# ============================================================================
# Interview Context API Endpoints
# ============================================================================

@app.post("/api/interview-contexts")
async def create_interview_context(data: dict):
    """
    Create interview context binding resume profile + job profile.
    Request body: {"resume_profile_id": str, "job_profile_id": str}
    Returns: {context_id, resume_profile, job_profile, created_at}
    """
    resume_profile_id = data.get("resume_profile_id")
    job_profile_id = data.get("job_profile_id")

    if not resume_profile_id or not job_profile_id:
        raise HTTPException(status_code=400, detail="Both resume_profile_id and job_profile_id are required")

    if resume_profile_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Resume profile not found")

    if job_profile_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Job profile not found")

    resume_profile = profiles_db[resume_profile_id]
    job_profile = profiles_db[job_profile_id]

    if resume_profile["type"] != "resume":
        raise HTTPException(status_code=400, detail="First profile must be a resume profile")

    if job_profile["type"] != "job_description":
        raise HTTPException(status_code=400, detail="Second profile must be a job description profile")

    # Create context
    context_id = uuid.uuid4().hex
    context = {
        "context_id": context_id,
        "resume_profile_id": resume_profile_id,
        "job_profile_id": job_profile_id,
        "resume_profile": {
            "name": resume_profile["name"],
            "headline": resume_profile["headline"],
            "skills": resume_profile["skills"],
            "experience": resume_profile["experience"],
            "education": resume_profile["education"],
            "confidence_score": resume_profile["confidence_score"]
        },
        "job_profile": {
            "company": job_profile["company"],
            "role": job_profile["role"],
            "requirements": job_profile["requirements"],
            "nice_to_have": job_profile["nice_to_have"],
            "responsibilities": job_profile["responsibilities"]
        },
        "created_at": datetime.utcnow().isoformat(),
        "user_id": MOCK_USER_ID
    }
    interview_contexts_db[context_id] = context

    return JSONResponse(content=context)


@app.get("/api/interview-contexts")
async def list_interview_contexts():
    """
    List all interview contexts for the current user.
    Returns: [{context_id, resume_profile_summary, job_profile_summary, created_at}]
    """
    contexts = [
        {
            "context_id": ctx["context_id"],
            "resume_profile_summary": {
                "name": ctx["resume_profile"]["name"],
                "headline": ctx["resume_profile"]["headline"]
            },
            "job_profile_summary": {
                "company": ctx["job_profile"]["company"],
                "role": ctx["job_profile"]["role"]
            },
            "created_at": ctx["created_at"]
        }
        for ctx in interview_contexts_db.values()
        if ctx.get("user_id") == MOCK_USER_ID
    ]
    return JSONResponse(content=contexts)


@app.get("/api/interview-contexts/{context_id}")
async def get_interview_context(context_id: str):
    """
    Get full interview context details by ID.
    Returns: {context_id, resume_profile, job_profile, created_at}
    """
    if context_id not in interview_contexts_db:
        raise HTTPException(status_code=404, detail="Context not found")

    context = interview_contexts_db[context_id]
    return JSONResponse(content=context)


# ============================================================================
# Interview Session Management API Endpoints
# ============================================================================

def is_valid_transition(current_state: str, new_state: str) -> bool:
    """Check if state transition is valid."""
    return new_state in VALID_TRANSITIONS.get(current_state, [])


@app.post("/api/sessions")
async def create_session(data: dict):
    """
    Create a new interview session.
    Request body: {"context_id": str, "interview_type"?: "hr" | "hiring"}
    Returns: {session_id, context, state}
    """
    context_id = data.get("context_id")
    interview_type = data.get("interview_type", "hiring")

    if not context_id:
        raise HTTPException(status_code=400, detail="context_id is required")

    if context_id not in interview_contexts_db:
        raise HTTPException(status_code=404, detail="Interview context not found")

    context = interview_contexts_db[context_id]

    # Create session
    session_id = uuid.uuid4().hex
    now = datetime.utcnow().isoformat()

    session = {
        "session_id": session_id,
        "context_id": context_id,
        "interview_type": interview_type,
        "state": SESSION_STATE_ACTIVE,
        "transcript": [],
        "started_at": now,
        "updated_at": now,
        "user_id": MOCK_USER_ID
    }
    sessions_db[session_id] = session

    return JSONResponse(content={
        "session_id": session_id,
        "context": {
            "context_id": context_id,
            "resume_profile": context["resume_profile"],
            "job_profile": context["job_profile"]
        },
        "state": SESSION_STATE_ACTIVE
    })


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve session details by ID.
    Returns: {session_id, context_id, state, transcript[], started_at, updated_at}
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[session_id]
    return JSONResponse(content={
        "session_id": session["session_id"],
        "context_id": session["context_id"],
        "state": session["state"],
        "transcript": session["transcript"],
        "started_at": session["started_at"],
        "updated_at": session["updated_at"]
    })


@app.patch("/api/sessions/{session_id}")
async def update_session(session_id: str, data: dict):
    """
    Update session state.
    Request body: {"action": "pause" | "resume" | "end"}
    Returns: {session_id, state, previous_state}
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[session_id]
    current_state = session["state"]
    action = data.get("action")

    if not action:
        raise HTTPException(status_code=400, detail="action is required")

    # Map action to target state
    action_to_state = {
        "pause": SESSION_STATE_PAUSED,
        "resume": SESSION_STATE_ACTIVE,
        "end": SESSION_STATE_ENDED
    }

    if action not in action_to_state:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    target_state = action_to_state[action]

    # Validate state transition
    if not is_valid_transition(current_state, target_state):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition from {current_state} to {target_state}"
        )

    previous_state = current_state
    session["state"] = target_state
    session["updated_at"] = datetime.utcnow().isoformat()

    return JSONResponse(content={
        "session_id": session_id,
        "state": target_state,
        "previous_state": previous_state
    })


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    End and cleanup session.
    Returns: {success: true}
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[session_id]
    session["state"] = SESSION_STATE_ENDED
    session["updated_at"] = datetime.utcnow().isoformat()

    return JSONResponse(content={"success": True})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="localhost", port=port)
