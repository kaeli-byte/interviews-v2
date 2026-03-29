# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Gemini Live API demonstration app using the Google Gen AI Python SDK for the backend and vanilla JavaScript for the frontend. It enables real-time multimodal conversations with Gemini (audio in/out, video sharing, text chat).

## Commands

```bash
# Create virtual environment and install dependencies
uv venv && source .venv/bin/activate && uv pip install -r requirements.txt

# Start the FastAPI server
uv run main.py

# Start with custom port
PORT=8080 uv run main.py
```

The app runs at http://localhost:8000

## Architecture

```
main.py                 # FastAPI server + WebSocket endpoint (/ws)
gemini_live.py          # GeminiLive class - wraps google-genai SDK for session management
frontend/
  index.html           # Main UI
  main.js              # Application logic, UI event handling
  gemini-client.js     # WebSocket client for backend communication
  media-handler.js     # Audio/Video capture and playback
  pcm-processor.js     # AudioWorklet for PCM audio processing
```

### Backend Flow

1. Client connects to `/ws` WebSocket
2. `GeminiLive.start_session()` opens a Gemini Live session via `client.aio.live.connect()`
3. Three async tasks run concurrently:
   - `send_audio()` - streams PCM audio from frontend to Gemini
   - `send_video()` - streams JPEG frames from frontend camera
   - `send_text()` - streams text messages
   - `receive_loop()` - receives responses (audio, transcriptions, tool calls)
4. Responses are forwarded to client via WebSocket (audio as bytes, events as JSON)

### Configuration

Set `GEMINI_API_KEY` in `.env` (copy from `.env.example`). Model defaults to `gemini-3.1-flash-live-preview`.