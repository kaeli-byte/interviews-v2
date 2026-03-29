"""Backend FastAPI application entry point."""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.websockets import WebSocket
from google import genai

from backend.api.router import api_router
from backend.config import settings
from backend.websocket.handlers import handle_websocket

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("backend").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Interview Practice API",
    description="Backend for Gemini Live interview practice application",
    version="1.0.0",
)

# Add CORS middleware - be permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - serves frontend or API info."""
    if settings.frontend_dist_exists:
        frontend_path = settings.get_frontend_build_path()
        return FileResponse(f"{frontend_path}/index.html")
    # On Vercel without frontend build, serve API info
    return JSONResponse({
        "message": "Interview Practice API",
        "docs": "/docs",
        "health": "/health"
    })


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/health/gemini")
async def health_gemini():
    """Verify Gemini API connection."""
    from google import genai

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Simple models.list call to verify API key works
        models = client.models.list()
        return {
            "status": "healthy",
            "gemini_connected": True,
            "model": settings.MODEL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "gemini_connected": False,
            "error": str(e)
        }


@app.post("/api/token")
async def get_ephemeral_token():
    """Generates an ephemeral token for direct Gemini Live API connection."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})

        now = datetime.now(timezone.utc)
        expire_time = now + timedelta(minutes=30)

        # Create an ephemeral token
        token = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": expire_time.isoformat(),
                "new_session_expire_time": (now + timedelta(minutes=1)).isoformat(),
                "http_options": {"api_version": "v1alpha"},
            }
        )

        return {
            "token": token.name,
            "expires_at": expire_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating ephemeral token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Temporarily disabled - may conflict with WebSocket
# @app.get("/ws/health")
# async def ws_health():
#     """WebSocket health check and active connections."""
#     from backend.websocket.manager import manager
#     return {
#         "ws_enabled": True,
#         "active_connections": len(manager.active_connections),
#         "connection_ids": list(manager.active_connections.keys())
#     }


# @app.get("/ws/test")
# async def ws_test():
    """End-to-end WebSocket test - verifies Gemini Live connection works."""
    import asyncio
    from backend.services.gemini_live import GeminiLive

    try:
        gemini = GeminiLive(
            api_key=settings.GEMINI_API_KEY,
            model=settings.MODEL,
            input_sample_rate=16000
        )

        # Create test queues
        audio_queue = asyncio.Queue()
        video_queue = asyncio.Queue()
        text_queue = asyncio.Queue()

        # Start session and get first event to verify connection
        connection_ok = False
        error = None

        try:
            async for event in gemini.start_session(
                audio_input_queue=audio_queue,
                video_input_queue=video_queue,
                text_input_queue=text_queue,
                audio_output_callback=lambda x: None,
                session_id=None
            ):
                # Got event = connection working
                connection_ok = True
                break  # Exit after first event
        except Exception as e:
            error = str(e)
        finally:
            gemini.end_session()

        if connection_ok:
            return {
                "status": "healthy",
                "ws_e2e_test": "passed",
                "gemini_model": settings.MODEL,
                "message": "Gemini Live WebSocket connection verified"
            }
        else:
            return {
                "status": "unhealthy",
                "ws_e2e_test": "failed",
                "error": error or "No events received"
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "ws_e2e_test": "failed",
            "error": str(e)
        }


@app.websocket("/ws-test-new")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live - inline test."""
    await websocket.accept()
    logger.info("WebSocket accepted")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live."""
    await handle_websocket(websocket, None)


@app.websocket("/ws-test")
async def websocket_test(websocket: WebSocket):
    """Simple test WebSocket endpoint."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        pass


# Include API routes
app.include_router(api_router)


# TODO: Add remaining routes from main.py:
# - /api/documents/* (upload, list, delete)
# - /api/profiles/* (extract, get)
# - /api/interview-contexts/* (CRUD)
# - /api/sessions/* (CRUD, state transitions)
# - /api/agents/* (list, get, handoff)
# - /api/debrief/* (generate, get, regenerate)
# - /api/progress/trends


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)