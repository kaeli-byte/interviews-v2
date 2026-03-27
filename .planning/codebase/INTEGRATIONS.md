# External Integrations

**Analysis Date:** 2026-03-27

## APIs & External Services

**AI/LLM:**
- Google Gemini Live API - Real-time multimodal AI conversations
  - SDK: `google-genai` Python package
  - Endpoint: `client.aio.live.connect(model=...)` (websocket-based)
  - Auth: `GEMINI_API_KEY` environment variable
  - Features: Audio in/out, video input, text chat, tool calls

## Data Storage

**None** - This is a stateless real-time demo application with no persistent storage.

## Authentication & Identity

**Auth Provider:**
- Google Gemini API Key
  - Implementation: API key passed to `genai.Client(api_key=...)`
  - Storage: `.env` file (never committed)

## Browser APIs (Frontend)

**Media Capture:**
- `navigator.mediaDevices.getUserMedia` - Microphone and camera access
- `navigator.mediaDevices.getDisplayMedia` - Screen sharing
- Used in: `frontend/media-handler.js`

**Audio Processing:**
- Web Audio API (`AudioContext`)
- AudioWorklet API - Custom PCM processing
- Used in: `frontend/media-handler.js`, `frontend/pcm-processor.js`

**Real-time Communication:**
- WebSocket API - Bidirectional communication with backend
- Used in: `frontend/gemini-client.js`

## Monitoring & Observability

**Logging:**
- Python `logging` module with DEBUG/INFO levels
- Browser `console` API for frontend logging

**Error Tracking:**
- None - No external error tracking service

## CI/CD & Deployment

**Hosting:**
- Self-hosted (run with `uv run main.py`)
- Can be deployed to any ASGI-compatible host

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY` - Google AI API key (required)

**Optional env vars:**
- `MODEL` - Gemini model name (default: `gemini-3.1-flash-live-preview`)
- `PORT` - Server port (default: `8000`)

**Secrets location:**
- `.env` file in project root (listed in `.gitignore`)

## Webhooks & Callbacks

**Incoming:**
- WebSocket endpoint at `/ws` - Handles client connections
  - Accepts: PCM audio bytes, text messages, JPEG images
  - Returns: PCM audio bytes (binary), JSON events

**Outgoing:**
- None

---

*Integration audit: 2026-03-27*