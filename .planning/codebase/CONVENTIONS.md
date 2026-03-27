# Coding Conventions

**Analysis Date:** 2026-03-27

## Naming Patterns

**Files (Python):**
- Snake case: `main.py`, `gemini_live.py`

**Files (JavaScript):**
- Lowercase with hyphens: `gemini-client.js`, `media-handler.js`, `pcm-processor.js`

**Classes:**
- PascalCase for both Python and JavaScript
- Examples: `GeminiLive`, `GeminiClient`, `MediaHandler`, `PCMProcessor`

**Functions/Methods:**
- Snake case in Python
- camelCase in JavaScript
- Examples: `start_session()`, `send_audio()`, `connect()`, `sendText()`

**Variables:**
- Snake case in Python
- camelCase in JavaScript
- Examples: `audio_input_queue`, `videoStream`, `gemini_client`

**Constants:**
- UPPER_SNAKE_CASE in Python
- Examples: `GEMINI_API_KEY`, `MODEL`, `PORT`

**Types (Python):**
- PascalCase with descriptive names
- Examples: `types.LiveConnectConfig`, `types.SpeechConfig`

## Code Style

**Formatting:**
- No explicit formatter configured (no Black, no Ruff, no Prettier)
- Python: 4-space indentation
- JavaScript: 2-space indentation

**Linting:**
- No linting configuration detected
- No .pylintrc, pyproject.toml with linting rules, or ESLint config

**Import Organization (Python):**
```
# Standard library first
import asyncio
import json
import logging
import os

# Third-party imports
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket

# Local imports
from gemini_live import GeminiLive
```

**JavaScript Module Pattern:**
- ES6 classes with constructor
- No module system (vanilla JS in single HTML file)
- Global class definitions

## Error Handling

**Python Patterns:**

1. **Try/except with logging:**
```python
try:
    # operation
except Exception as e:
    logger.error(f"Error: {e}\n{traceback.format_exc()}")
```

2. **Bare except (anti-pattern present):**
```python
# Line 118 in main.py - should specify exception type
try:
    await websocket.close()
except:
    pass
```

3. **Async task cancellation:**
```python
except asyncio.CancelledError:
    logger.debug("send_audio task cancelled")
```

4. **Error propagation:**
```python
except Exception as e:
    logger.error(...)
    raise
```

**JavaScript Patterns:**

1. **Try/catch for async:**
```javascript
try {
    await mediaHandler.startAudio((data) => {...});
} catch (e) {
    alert("Could not start audio capture");
}
```

2. **Console error logging:**
```javascript
console.error("Error starting audio:", e);
```

3. **Error event handlers:**
```javascript
this.websocket.onerror = (event) => {
    if (this.onError) this.onError(event);
};
```

## Logging

**Framework:** Python `logging` module

**Configuration (main.py):**
```python
logging.basicConfig(level=logging.INFO)
logging.getLogger("gemini_live").setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
```

**Log Levels Used:**
- `logger.debug()` - Detailed debug info
- `logger.info()` - Connection events, message summaries
- `logger.warning()` - Non-critical issues (GoAway, session updates)
- `logger.error()` - Errors with full traceback

**JavaScript:**
- `console.log()` - General info
- `console.error()` - Errors
- No structured logging framework

## Comments

**Python Docstrings:**

Google-style docstrings in `gemini_live.py`:
```python
def __init__(self, api_key, model, input_sample_rate, tools=None, tool_mapping=None):
    """
    Initializes the GeminiLive client.

    Args:
        api_key (str): The Gemini API Key.
        model (str): The model name to use.
        input_sample_rate (int): The sample rate for audio input.
        tools (list, optional): List of tools to enable. Defaults to None.
        tool_mapping (dict, optional): Mapping of tool names to functions. Defaults to None.
    """
```

**Inline Comments:**
- Used to explain complex logic
- Example: `# Mute local feedback` in media-handler.js

**JSDoc Comments:**
- Present in gemini-client.js and media-handler.js
- Documents class and method purposes

## Function Design

**Size:** Moderate - functions tend to be focused on single responsibility

**Parameters:**
- Type hints in Python
- Config objects in JavaScript constructors
- Callbacks for async operations

**Return Values:**
- Python: `async generators` for streaming events (`yield event`)
- JavaScript: void for event handlers, promises for async methods

**Async Patterns:**
```python
# Python: async generator
async def start_session(self, ...):
    ...
    yield event

# Python: concurrent tasks
async def run_session():
    async for event in gemini_client.start_session(...):
        ...
```

## Module Design

**Python Exports:**
- Classes as main exports
- Example: `from gemini_live import GeminiLive`

**JavaScript Class Pattern:**
```javascript
class GeminiClient {
  constructor(config) {
    // Instance properties
  }

  connect() {
    // Method implementation
  }
}
```

**No Barrel Files:**
- Each file is self-contained
- No index.js or __init__.py for re-exports

## Configuration Management

**Environment Variables:**
- Loaded via `python-dotenv`
- Pattern: `os.getenv("VAR_NAME", default_value)`
- Example: `MODEL = os.getenv("MODEL", "gemini-3.1-flash-live-preview")`

**Required Config:**
- `GEMINI_API_KEY` - Must be set in `.env`
- `MODEL` - Optional, defaults to `gemini-3.1-flash-live-preview`
- `PORT` - Optional, defaults to `8000`

**Security Note:**
- `.env` file exists but is git-ignored
- No validation for missing API key (will fail at runtime)

---

*Convention analysis: 2026-03-27*