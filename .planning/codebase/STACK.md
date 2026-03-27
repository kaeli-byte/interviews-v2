# Technology Stack

**Analysis Date:** 2026-03-27

## Languages

**Primary:**
- Python 3.x - Backend server, API endpoints, Gemini integration

**Secondary:**
- JavaScript (ES6+) - Frontend client, browser-based audio/video handling
- HTML5 - UI markup

## Runtime

**Environment:**
- Python 3.9+ (based on type hints and asyncio usage)
- Modern browser with WebSocket and Web Audio API support

**Package Manager:**
- uv - Modern Python package manager
- Lockfile: Not present in repository

## Frameworks

**Core:**
- FastAPI 0.x - Web framework for REST endpoints and WebSocket handling
  - Used in: `main.py`

**Server:**
- uvicorn 0.x - ASGI server to run FastAPI application
  - Used in: `main.py`

**AI SDK:**
- google-genai - Official Google Gemini Python SDK
  - Used in: `gemini_live.py`
  - Provides async live.connect() for real-time sessions

## Key Dependencies

**Critical:**
- google-genai - Gemini Live API client with async support
  - Provides `client.aio.live.connect()` for real-time bidirectional communication
- fastapi - Web framework with WebSocket support
- websockets - Underlying WebSocket library (transitive from fastapi)

**Infrastructure:**
- uvicorn - ASGI server
- python-dotenv - Environment variable loading from `.env` files
- python-multipart - Multipart form data support (for future file uploads)

## Configuration

**Environment:**
- Uses `python-dotenv` to load `.env` file
- Required: `GEMINI_API_KEY` - Google AI API key
- Optional: `MODEL` - defaults to `gemini-3.1-flash-live-preview`
- Optional: `PORT` - defaults to `8000`

**Build:**
- No build tools required for Python
- Frontend uses vanilla JS (no transpilation)

## Platform Requirements

**Development:**
- Python 3.9+
- uv package manager
- Modern browser (Chrome, Firefox, Edge, Safari)

**Production:**
- ASGI-compatible server (uvicorn recommended)
- Gemini API access with valid API key

---

*Stack analysis: 2026-03-27*