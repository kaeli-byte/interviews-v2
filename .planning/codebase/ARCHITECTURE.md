# Architecture

**Analysis Date:** 2026-03-27

## Pattern Overview

**Overall:** Simple Monolith (FastAPI + Vanilla JS)

**Key Characteristics:**
- Single Python backend process serving both API and static frontend files
- WebSocket-based real-time communication between frontend and backend
- Bi-directional streaming for audio, video, and text
- No build tools or framework dependencies on frontend

## Layers

**Web Server Layer:**
- Purpose: HTTP server and WebSocket endpoint
- Location: `main.py`
- Contains: FastAPI app, WebSocket handler (`/ws`), static file serving
- Depends on: `gemini_live.py`, `google-genai` SDK
- Used by: Frontend WebSocket client

**Gemini Client Layer:**
- Purpose: Wraps Google Gen AI Python SDK for session management
- Location: `gemini_live.py`
- Contains: `GeminiLive` class with async queue-based I/O
- Depends on: `google-genai` SDK
- Used by: `main.py`

**Frontend Application Layer:**
- Purpose: User interface and media handling
- Location: `frontend/`
- Contains: UI logic (`main.js`), WebSocket client (`gemini-client.js`), media capture/playback (`media-handler.js`, `pcm-processor.js`)
- Depends on: Browser WebSocket API, MediaDevices API, AudioContext API
- Used by: End user browser

## Data Flow

**Connection Flow:**

```
User clicks Connect
    |
    v
main.js: geminiClient.connect() --WebSocket--> main.py: /ws endpoint
    |
    v
main.py creates GeminiLive instance
    |
    v
gemini_live.py: start_session() ---> Google Gen AI Live API (via google-genai SDK)
    |
    v
Bidirectional streaming begins
```

**Audio Input Flow:**

```
Browser: MediaHandler.startAudio() captures microphone
    |
    v
pcm-processor.js: AudioWorklet processes PCM chunks
    |
    v
main.js sends bytes via WebSocket
    |
    v
main.py receives bytes, puts in audio_input_queue
    |
    v
gemini_live.py: send_audio() task reads queue, sends to Gemini
```

**Audio Output Flow:**

```
Gemini Live API sends audio response
    |
    v
gemini_live.py: receive_loop() processes server_content.model_turn.parts
    |
    v
audio_output_callback(data) sends bytes via WebSocket
    |
    v
main.js receives bytes, MediaHandler.playAudio() plays sound
```

**Event/Text Flow:**

```
User sends text message
    |
    v
main.js: geminiClient.sendText(text)
    |
    v
main.py receives text, puts in text_input_queue
    |
    v
gemini_live.py: send_text() task sends to Gemini
    |
    v
Gemini response --> receive_loop() --> event_queue --> main.py --> WebSocket JSON --> main.js
```

## Key Abstractions

**GeminiLive Class:**
- Purpose: Manages Gemini Live API session lifecycle
- Examples: `gemini_live.py`
- Pattern: Async generator yielding events; uses asyncio queues for I/O buffering

**WebSocket Protocol:**
- Binary: PCM audio data (Int16Array from frontend, raw bytes to frontend)
- JSON: Text messages, image frames (base64), event notifications
- Events: `user`, `gemini`, `interrupted`, `turn_complete`, `tool_call`, `error`

**MediaHandler Class:**
- Purpose: Browser-side audio/video capture and playback
- Examples: `frontend/media-handler.js`
- Pattern: Wraps Web Audio API, MediaDevices API

**GeminiClient Class:**
- Purpose: Frontend WebSocket communication abstraction
- Examples: `frontend/gemini-client.js`
- Pattern: Event-driven with callback configuration

## Entry Points

**Backend Entry Point:**
- Location: `main.py`
- Triggers: `uv run main.py` or `python main.py`
- Responsibilities: Initialize FastAPI, configure CORS, mount static files, start uvicorn server

**WebSocket Endpoint:**
- Location: `main.py:websocket_endpoint()`
- Triggers: Frontend connects to `ws://host:8000/ws`
- Responsibilities: Accept connection, create queues, instantiate GeminiLive, bridge client and Gemini

**Frontend Entry Point:**
- Location: `frontend/index.html`
- Triggers: User navigates to `http://localhost:8000`
- Responsibilities: Load scripts, initialize UI, handle user interactions

## Error Handling

**Strategy:** Log and propagate; session cleanup via task cancellation

**Patterns:**
- Python: `try/except` blocks with logging; `asyncio.CancelledError` handling for cleanup
- JavaScript: Event callbacks for `onError`, `onClose`; UI shows connection error status
- WebSocket disconnect: Task cancellation triggers queue empty signals, session gracefully terminates

## Cross-Cutting Concerns

**Logging:** Python `logging` module with DEBUG level for `gemini_live` module, INFO for others

**Validation:** None explicit; relies on FastAPI for basic request validation

**Authentication:** API key via `GEMINI_API_KEY` environment variable; no per-user auth

---

*Architecture analysis: 2026-03-27*