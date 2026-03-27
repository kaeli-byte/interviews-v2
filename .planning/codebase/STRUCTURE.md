# Codebase Structure

**Analysis Date:** 2026-03-27

## Directory Layout

```
/Users/hafid/webapps/AI-CHAT-v2/gemini-live-api-examples/gemini-live-genai-python-sdk/
├── main.py                 # FastAPI server + WebSocket endpoint
├── gemini_live.py          # GeminiLive class - SDK wrapper
├── requirements.txt        # Python dependencies
├── CLAUDE.md              # Project instructions
├── README.md              # Documentation
├── .env.example           # Environment template
├── .env                   # Environment (contains secrets - not committed)
├── .gitignore
├── .planning/codebase/    # Generated analysis documents
└── frontend/
    ├── index.html         # Main UI
    ├── main.js            # Application logic, UI event handling
    ├── gemini-client.js   # WebSocket client
    ├── media-handler.js   # Audio/Video capture and playback
    ├── pcm-processor.js   # AudioWorklet for PCM processing
    └── style.css          # Styling
```

## Directory Purposes

**Root (`/`):**
- Purpose: Backend application code and configuration
- Contains: Python source files, requirements, environment config

**`frontend/`:**
- Purpose: Browser-based user interface
- Contains: HTML, JavaScript, CSS files served statically

**`.planning/codebase/`:**
- Purpose: Generated architecture/analysis documents
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, etc.
- Generated: Yes (by GSD mapper)
- Committed: No (.gitignore should exclude .planning)

## Key File Locations

**Entry Points:**
- `main.py`: Backend startup - run via `uv run main.py`
- `frontend/index.html`: Frontend entry - served at `/`

**Configuration:**
- `.env`: API key configuration (GEMINI_API_KEY)
- `.env.example`: Template for environment variables

**Core Logic:**
- `main.py`: FastAPI app, WebSocket handler, session orchestration
- `gemini_live.py`: GeminiLive class, async queue management, session lifecycle

**Frontend Logic:**
- `frontend/main.js`: UI event handlers, message routing
- `frontend/gemini-client.js`: WebSocket connection abstraction
- `frontend/media-handler.js`: Audio/Video capture and playback
- `frontend/pcm-processor.js`: AudioWorklet for PCM processing

**Testing:**
- No test directory or test files detected

## Naming Conventions

**Files:**
- Python: snake_case (`gemini_live.py`, `main.py`)
- JavaScript: kebab-case with dash separators (`gemini-client.js`, `pcm-processor.js`)
- HTML: lowercase (`index.html`)
- CSS: kebab-case (`style.css`)

**Classes:**
- Python: PascalCase (`GeminiLive`)
- JavaScript: PascalCase (`MediaHandler`, `GeminiClient`, `PCMProcessor`)

**Functions/Methods:**
- Python: snake_case (`start_session`, `send_audio`)
- JavaScript: camelCase (`connect`, `sendText`, `playAudio`)

## Where to Add New Code

**New Backend Feature:**
- Primary code: `gemini_live.py` (if Gemini-related) or `main.py` (if WebSocket/server-related)
- Tests: No test directory currently exists

**New Frontend Feature:**
- JavaScript: `frontend/main.js` (for UI logic) or new file in `frontend/`
- HTML: `frontend/index.html`
- CSS: `frontend/style.css`

**New Utility:**
- Python: Root directory or create `utils/` subdirectory
- JavaScript: Create in `frontend/` or add to existing module

**Environment Variables:**
- Add to `.env.example` (template)
- Add to `.env` (local development)
- Read in `main.py`

## Special Directories

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `uv venv`)
- Committed: No (.gitignore excludes)

**`.planning/`:**
- Purpose: GSD-generated analysis documents
- Generated: Yes (by gsd-codebase-mapper)
- Committed: No (should be in .gitignore)

---

*Structure analysis: 2026-03-27*