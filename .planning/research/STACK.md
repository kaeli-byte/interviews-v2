# Technology Stack

**Project:** AI Interview Preparation App (Job Interview Prep)
**Researched:** 2026-03-27

This stack recommendation is for evolving the existing Gemini Live prototype into a production-ready interview preparation platform with document ingestion, interview agents, live sessions, debrief analysis, coaching modes, and long-term memory.

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.115+ (via `fastapi[standard]`) | Web framework, WebSocket handling | Existing choice; excellent async support, automatic OpenAPI docs, dependency injection for clean architecture. The `standard` extras include uvicorn, pydantic, httpx, and python-multipart. |
| **Pydantic** | 2.12.5 | Data validation, settings management | Required by FastAPI; v2 uses Rust-based core for 5-50x performance improvement over v1. Type-safe request/response models. |
| **uvicorn** | 0.42.0 | ASGI server | High-performance server with `uvloop`. Use `uvicorn[standard]` for production workers. |
| **python-dotenv** | 1.2.2 | Environment variable management | Load `.env` files for secrets (GEMINI_API_KEY, DATABASE_URL). Use `python-dotenv[cli]` for CLI access. |

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PostgreSQL** | 16+ | Primary data store | Project requirement. ACID compliance, JSONB for flexible agent configs, excellent full-text search for memory retrieval. |
| **SQLAlchemy** | 2.0.37+ | ORM, database abstraction | Modern 2.0 syntax with `Mapped[]` type annotations, `mapped_column()`, full async support. Industry standard with mature ecosystem. |
| **asyncpg** | 0.30+ | PostgreSQL async driver | Fastest async PostgreSQL driver for Python. Use connection string: `postgresql+asyncpg://user:pass@host/db`. |
| **Alembic** | 1.18.4 | Database migrations | Official SQLAlchemy migration tool. Auto-generates migrations from model changes. Critical for versioned agent configs. |

### Caching & Ephemeral State

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Redis** | 7.4+ (server) | Session state, caching, pub/sub | Project requirement. Sub-millisecond latency for live session state, agent handoff coordination, broadcast to multiple WebSocket connections. |
| **redis-py** | 5.0+ | Redis client | Full async support with `redis.asyncio`. Use `redis[hiredis]` for 2-3x performance with C parser. |

### Document Processing

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **pypdf** | 6.9.2 | PDF text extraction | Lightweight, pure Python, actively maintained. Handles text extraction from machine-generated PDFs (resumes). Add `[crypto]` for encrypted PDFs. |
| **pdfplumber** | 0.11.9 | PDF text extraction (alternative) | More detailed layout analysis than pypdf. Built on `pdfminer.six`. Better for PDFs with complex formatting/tables. |
| **python-docx** | 1.2.0 | DOCX text extraction | Standard library for Word documents. Synchronous API (wrap in `asyncio.to_thread()` for non-blocking). |
| **marker-ai** | N/A | OCR for scanned PDFs | Use when resumes are scanned images. Higher accuracy than pypdf for OCR but requires model download. |

**Recommendation:** Start with **pypdf** for PDFs (covers 90% of resumes) + **python-docx**. Add **pdfplumber** only if layout analysis needed. Add **marker-ai** only if scanned PDFs are common.

### AI Runtime

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **google-genai** | 1.68.0 | Gemini SDK, Live API | Official Google SDK. `client.aio.live.connect()` for async live sessions. Supports audio/video/text streaming, tool calling, real-time function responses. |
| **Gemini 2.5 Flash** | N/A | Primary model | Best latency/cost balance for interview practice. Use `gemini-2.5-flash` or `gemini-2.5-flash-preview` for Live API. |

### Long-Term Memory

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Supermemory** | 1.2+ (API) | Long-term memory, user profiles | Project requirement. Three context methods: Memory API (evolving facts), User Profiles (static+dynamic), RAG (semantic search). Shared context pool per user. |

**Integration:** REST API at `https://api.supermemory.ai/v3/`. Use `httpx` async client. Authentication via API key in `X-API-Key` header.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pydantic-settings** | 2.18.4 | Settings management | Use `Settings(BaseSettings)` class for type-safe config from env vars. Better than raw `os.environ`. |
| **orjson** | 3.11.7 | Fast JSON serialization | 5-10x faster than stdlib json. Drop-in replacement for WebSocket JSON, API responses. Requires Python 3.10+. |
| **httpx** | 0.28+ | Async HTTP client | Included in `fastapi[standard]`. Use for Supermemory API calls, external webhooks. |
| **websockets** | 13+ | WebSocket client | For backend-to-Gemini Live connections. Included with FastAPI. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| **ORM** | SQLAlchemy 2.0+ | SQLModel | SQLModel is simpler but less flexible for complex queries needed for agent configs and memory retrieval. |
| **ORM** | SQLAlchemy 2.0+ | Tortoise ORM | Less mature ecosystem, fewer contributors. SQLAlchemy has 15+ years of stability. |
| **PostgreSQL Driver** | asyncpg | psycopg3 async | asyncpg is 20-30% faster in benchmarks. psycopg3 has better PostgreSQL feature coverage but slower. |
| **PDF Parsing** | pypdf | PyMuPDF (fitz) | PyMuPDF is faster but has GPL-compatible (not pure MIT/Apache) license and C extensions complicate deployment. |
| **PDF Parsing** | pypdf | pdfplumber (default) | pdfplumber is heavier and slower. Only use when layout analysis (tables, positioning) is required. |
| **Redis Client** | redis-py | aioredis | aioredis was merged into redis-py 4.0+. No reason to use separate package. |
| **Settings** | pydantic-settings | dynaconf | pydantic-settings integrates natively with Pydantic v2 models. Dynaconf adds complexity for multi-env configs not needed here. |

## Installation

```bash
# Core FastAPI stack
pip install "fastapi[standard]"  # includes uvicorn, pydantic, httpx, python-multipart

# Database
pip install sqlalchemy alembic asyncpg

# Redis
pip install "redis[hiredis]"

# Document processing
pip install pypdf python-docx

# AI runtime
pip install google-genai

# Long-term memory (API client - no SDK needed)
# Use httpx (already included in fastapi[standard])

# Performance & settings
pip install orjson pydantic-settings python-dotenv

# Optional: for scanned PDFs (OCR)
# pip install marker-ai  # deferred until needed

# Development dependencies
pip install pytest httpx  # for testing
```

**requirements.txt structure:**

```txt
# Runtime
fastapi[standard]==0.115.0
uvicorn[standard]==0.42.0
pydantic==2.12.5
pydantic-settings==2.18.4
python-dotenv==1.2.2
sqlalchemy==2.0.37
alembic==1.18.4
asyncpg==0.30.0
redis[hiredis]==5.0.0
pypdf==6.9.2
python-docx==1.2.0
google-genai==1.68.0
orjson==3.11.7
httpx==0.28.0

# Optional (uncomment if needed)
# marker-ai  # for OCR
# pdfplumber==0.11.9  # for layout analysis
```

## Architecture Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket Handler (/ws)                                        │
│    │                                                             │
│    ├── GeminiLive Session Manager                               │
│    │   └── google-genai SDK → Gemini Live API                   │
│    │                                                             │
│    ├── Document Ingestion Service                               │
│    │   ├── pypdf → PDF → text                                   │
│    │   └── python-docx → DOCX → text                            │
│    │                                                             │
│    ├── Agent Configuration Service                              │
│    │   └── SQLAlchemy → PostgreSQL (versioned configs)          │
│    │                                                             │
│    ├── Session State Manager                                    │
│    │   └── redis-py async → Redis (ephemeral state)             │
│    │                                                             │
│    ├── Memory Integration                                       │
│    │   └── httpx async → Supermemory API                        │
│    │                                                             │
│    └── Debrief/Analytics Service                                │
│        └── SQLAlchemy → PostgreSQL (session history, scores)    │
└─────────────────────────────────────────────────────────────────┘
```

## Confidence Assessment

| Component | Confidence | Source |
|-----------|------------|--------|
| FastAPI + Pydantic v2 | HIGH | Official FastAPI docs, PyPI |
| SQLAlchemy 2.0 async | HIGH | Official SQLAlchemy docs |
| asyncpg | HIGH | Official docs, PyPI |
| Redis + redis-py 5.x | HIGH | Official Redis docs, PyPI |
| pypdf | HIGH | Official docs, PyPI |
| python-docx | HIGH | Official docs, PyPI |
| google-genai SDK | HIGH | Official Google docs, PyPI |
| Supermemory | MEDIUM | Official docs (limited Python examples) |
| marker-ai | MEDIUM | Community sources, not verified with Context7 |

## Sources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [PyPI: pydantic 2.12.5](https://pypi.org/project/pydantic/)
- [PyPI: sqlalchemy](https://pypi.org/project/sqlalchemy/)
- [PyPI: asyncpg](https://pypi.org/project/asyncpg/)
- [PyPI: alembic 1.18.4](https://pypi.org/project/alembic/)
- [PyPI: redis 7.4.0](https://pypi.org/project/redis/)
- [PyPI: pypdf 6.9.2](https://pypi.org/project/pypdf/)
- [PyPI: python-docx 1.2.0](https://pypi.org/project/python-docx/)
- [PyPI: google-genai 1.68.0](https://pypi.org/project/google-genai/)
- [PyPI: pydantic-settings 2.13.1](https://pypi.org/project/pydantic-settings/)
- [PyPI: orjson 3.11.7](https://pypi.org/project/orjson/)
- [PyPI: uvicorn 0.42.0](https://pypi.org/project/uvicorn/)
- [PyPI: python-dotenv 1.2.2](https://pypi.org/project/python-dotenv/)
- [Supermemory Documentation](https://supermemory.ai/docs/)
- [pdfplumber PyPI](https://pypi.org/project/pdfplumber/)
