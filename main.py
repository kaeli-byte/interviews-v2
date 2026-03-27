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
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live."""
    await websocket.accept()

    logger.info("WebSocket connection accepted")

    audio_input_queue = asyncio.Queue()
    video_input_queue = asyncio.Queue()
    text_input_queue = asyncio.Queue()

    async def audio_output_callback(data):
        await websocket.send_bytes(data)

    async def audio_interrupt_callback():
        # The event queue handles the JSON message, but we might want to do something else here
        pass

    gemini_client = GeminiLive(
        api_key=GEMINI_API_KEY, model=MODEL, input_sample_rate=16000
    )

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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="localhost", port=port)
