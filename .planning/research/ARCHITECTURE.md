# Architecture Patterns

**Domain:** AI Interview Preparation Platform
**Researched:** 2026-03-27

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Vanilla JS)                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │ Upload UI   │  │ Session UI   │  │ Coaching UI   │  │ Progress/Debrief│ │
│  │ (docs)      │  │ (voice/chat) │  │ (pre/post)    │  │ (analytics)     │ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  └────────┬────────┘ │
└─────────┼────────────────┼──────────────────┼───────────────────┼──────────┘
          │                │                  │                   │
          │ HTTP/REST      │ WebSocket        │ HTTP/REST         │ HTTP/REST
          ▼                ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / FastAPI Application                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Request Router / Dispatcher                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│         │                │                  │                   │           │
│         ▼                ▼                  ▼                   ▼           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │ Document    │  │ Realtime     │  │ Coaching      │  │ Analytics       │  │
│  │ API         │  │ Session API  │  │ API           │  │ API             │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  └────────┬────────┘  │
└─────────┼────────────────┼──────────────────┼───────────────────┼───────────┘
          │                │                  │                   │
          ▼                ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER (Business Logic)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │ Document    │  │ Session      │  │ Coach         │  │ Debrief         │  │
│  │ Ingestion   │  │ Orchestrator │  │ Orchestrator  │  │ Engine          │  │
│  │ Service     │  │              │  │               │  │                 │  │
│  │ - PDF parse │  │ - lifecycle  │  │ - prep coach  │  │ - rubric eval   │  │
│  │ - DOCX parse│  │ - handoff    │  │ - debrief     │  │ - trend agg     │  │
│  │ - URL fetch │  │ - state mgmt │  │    coach      │  │ - recommendation│  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  └────────┬────────┘  │
│         │                │                  │                   │           │
│         ▼                ▼                  ▼                   │           │
│  ┌──────────────────────────────────────────────────────────────┴─────────┐ │
│  │                    Interview Context Builder                           │ │
│  │         (binds candidate profile + job profile for sessions)           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌──────────────┐          ┌─────────────────┐    │
│  │ Agent       │           │ Memory       │          │ Simulation      │    │
│  │ Registry    │           │ Service      │          │ Engine          │    │
│  │ + Versioning│           │ (Supermemory)│          │ (internal)      │    │
│  └──────┬──────┘           └──────┬───────┘          └─────────────────┘    │
└─────────┼─────────────────────────┼─────────────────────────────────────────┘
          │                         │
          ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADAPTER LAYER (External Integrations)                  │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │   Gemini Live Adapter       │  │   Document Parsers / Scrapers       │   │
│  │   - session connect         │  │   - PDF extractor                   │   │
│  │   - audio/video/text stream │  │   - DOCX extractor                  │   │
│  │   - tool call handling      │  │   - URL HTML scraper                │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                         │
          ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │ PostgreSQL  │  │ Redis        │  │ Object Store  │  │ Supermemory     │  │
│  │ - users     │  │ - session    │  │ - raw docs    │  │ - long-term     │  │
│  │ - documents │  │   state      │  │ - audio       │  │   memory items  │  │
│  │ - profiles  │  │ - realtime   │  │ - exports     │  │ - embeddings    │  │
│  │ - sessions  │  │   fanout     │  │               │  │ - retrieval     │  │
│  │ - transcripts│ │              │  │               │  │                 │  │
│  │ - agents    │  │              │  │               │  │                 │  │
│  │ - coaches   │  │              │  │               │  │                 │  │
│  │ - debriefs  │  │              │  │               │  │                 │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Frontend Web App** | User interface for document upload, live interviews, coaching sessions, progress viewing | FastAPI backend via REST and WebSocket |
| **Document API** | Handles file uploads, URL imports, text imports; triggers parsing jobs | Document Ingestion Service, Object Store, PostgreSQL |
| **Document Ingestion Service** | Parses PDF/DOCX, extracts text, normalizes sections, builds candidate/job profiles | PostgreSQL (profiles), Object Store (raw files) |
| **Session Orchestrator** | Manages session lifecycle (create/start/pause/resume/end), state machine, agent binding | Gemini Live Adapter, Agent Registry, PostgreSQL (sessions/transcripts) |
| **Gemini Live Adapter** | Wraps google-genai SDK; manages audio/video/text streaming and event reception | Gemini Live API, Session Orchestrator |
| **Agent Registry** | Stores versioned agent definitions (prompts, policies, rubrics); resolves active version | PostgreSQL (agent_configs) |
| **Coach Orchestrator** | Runs pre-interview (Storytelling Architect) and post-interview (Answer Doctor) pipelines | Memory Service, PostgreSQL (coach runs/outputs) |
| **Debrief Engine** | Generates rubric scores, extracts evidence, computes trends, creates recommendations | PostgreSQL (scores/evidence), Session data |
| **Memory Service** | Synces session/coaching artifacts to Supermemory; handles retrieval queries | Supermemory, PostgreSQL (audit metadata) |
| **Interview Context Builder** | Binds candidate profile + job profile into a reusable context for sessions/coaching | PostgreSQL (profiles, contexts) |
| **Simulation Engine** | Runs offline interviews with synthetic candidate profiles for internal tuning | Agent Registry, Debrief Engine (internal admin only) |

## Data Flow

### Primary Flow: Document → Interview → Debrief

```
1. User uploads resume + job description
         │
         ▼
2. Document Ingestion Service
   - Stores raw file in Object Store
   - Extracts text, parses sections
   - Creates CandidateProfile / JobProfile in PostgreSQL
         │
         ▼
3. Interview Context Builder
   - Binds resume_profile + job_profile
   - Creates InterviewContext record
         │
         ▼
4. User starts interview session
         │
         ▼
5. Session Orchestrator
   - Creates Session record
   - Connects to Gemini Live via Adapter
   - Streams audio/video/text bidirectionally
   - Persists transcript_turns and session_events
         │
         ▼
6. Session ends → triggers Debrief Engine
         │
         ▼
7. Debrief Engine
   - Evaluates against rubric
   - Extracts evidence from transcript
   - Computes user_progress_snapshot
   - Stores debrief_scores + summaries
         │
         ▼
8. Memory Service (async)
   - Syncs transcript + debrief to Supermemory
   - Creates memory_items with metadata
```

### Secondary Flow: Coaching Pipeline

```
1. User selects coach (pre-interview or post-interview)
         │
         ▼
2. Coach Orchestrator receives request
   - Loads InterviewContext (resume + job)
   - For post-interview: loads Session transcript
         │
         ▼
3. Coach Pipeline (Storytelling or Answer Doctor)
   - Generates structured outputs (stories, rewritten answers, drills)
         │
         ▼
4. Coach outputs persisted to PostgreSQL
         │
         ▼
5. Memory Service syncs coaching artifacts to Supermemory
```

## Patterns to Follow

### Pattern 1: Backend-Owned Session Lifecycle

**What:** Backend maintains full session state machine, transcript, and event log rather than acting as a thin proxy to Gemini Live.

**When:** Always for interview sessions - this enables replay, debrief, simulation, and auditability.

**Example:**
```python
# Session state machine in backend
class SessionState(str, Enum):
    CREATED = "created"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    ENDED = "ended"

# Backend persists every transcript turn
async def on_gemini_response(response):
    if response.output_transcription:
        turn = TranscriptTurn(
            session_id=session_id,
            speaker="gemini",
            text=response.output_transcription.text,
            started_at=turn_start,
            ended_at=datetime.utcnow()
        )
        await db.transcript_turns.insert(turn)
```

### Pattern 2: Versioned Configs for Agents and Coaches

**What:** Agent and coach behavior stored as versioned database records, not hardcoded in source.

**When:** Always for configurable behavior - enables experimentation without code deploys.

**Example:**
```python
# Agent version schema
class AgentVersion(BaseModel):
    agent_id: str
    version: int
    system_prompt: str
    questioning_policy: dict  # JSON schema
    rubric: dict              # Evaluation rubric
    handoff_policy: dict      # When/how to hand off
    is_active: bool
```

### Pattern 3: Event-Sourced Session Transcripts

**What:** Sessions recorded as ordered event streams, not just final transcript text.

**When:** Always for live sessions - enables replay, analysis, and evidence extraction.

**Example:**
```python
# Event types to persist
events = [
    {"type": "session.created", "timestamp": "..."},
    {"type": "session.started", "agent_version_id": "..."},
    {"type": "turn.user", "text": "...", "transcription_confidence": 0.95},
    {"type": "turn.gemini", "text": "..."},
    {"type": "agent.handoff", "from_agent": "...", "to_agent": "..."},
    {"type": "session.ended", "duration_ms": 123456},
]
```

### Pattern 4: Interview Context as Binding Document

**What:** InterviewContext entity binds candidate profile + job profile, referenced by sessions/coaching.

**When:** Before any interview or coaching session - ensures consistent context throughout.

**Example:**
```python
# Interview Context model
class InterviewContext(BaseModel):
    id: str
    user_id: str
    resume_profile_id: str      # FK to candidate_profiles
    job_profile_id: str         # FK to job_profiles
    created_at: datetime
    active_version: int
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Frontend-Managed Session State

**What:** Letting frontend own session lifecycle with backend only storing results later.

**Why bad:** Makes replay impossible, weakens audit trail, complicates handoff and debrief.

**Instead:** Backend owns session state machine from creation through archival.

### Anti-Pattern 2: Hardcoded Agent Prompts

**What:** Agent behavior (prompts, rubrics) embedded in Python source code.

**Why bad:** Every experiment requires code deploy; impossible to reproduce past sessions.

**Instead:** Store agent configs in PostgreSQL with version numbers; resolve at session start.

### Anti-Pattern 3: Transcript-Only Storage

**What:** Storing only final transcript text without events or metadata.

**Why bad:** Loses evidence needed for debrief, timing data, and agent behavior analysis.

**Instead:** Store full event stream with timestamps, confidence scores, and agent state.

### Anti-Pattern 4: Memory Before Stable Contracts

**What:** Building Supermemory integration before session/debrief/artifact models are stable.

**Why bad:** Memory schema becomes coupled to unstable upstream models; retrofit becomes painful.

**Instead:** Build memory service after sessions, debriefs, and coaching have stable output contracts.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| **Session concurrency** | Single FastAPI instance sufficient | Load balancer + multiple workers | Regional deployment, session affinity |
| **Gemini API rate limits** | Not a concern | Implement request queuing | Multi-key rotation, enterprise quota |
| **Transcript storage** | PostgreSQL directly | PostgreSQL + partitioning by date | Hot/cold split: recent in Postgres, archived to object store |
| **Debrief generation** | Synchronous post-session | Background job queue (Celery/RQ) | Distributed workers with priority queues |
| **Memory retrieval** | Direct Supermemory calls | Cached retrieval results | Tiered caching + pre-fetched context |
| **Document parsing** | Synchronous processing | Async worker pool | Dedicated parsing service with auto-scaling |

## Build Order Implications

Based on component dependencies, recommended build sequence:

### Phase 1: Foundation
1. **Document Ingestion Service** - Required for all downstream features
2. **Interview Context Builder** - Binds profiles for sessions
3. **Session Orchestrator (hardened)** - Upgrade current prototype with PostgreSQL persistence

### Phase 2: Differentiation
4. **Agent Registry + Versioning** - Enables interviewer personas
5. **Debrief Engine** - Creates improvement loop with rubric scores

### Phase 3: Enhancement
6. **Coach Orchestrator** - Pre/post interview coaching pipelines
7. **Agent Customization** - Admin presets and runtime overrides

### Phase 4: Leverage
8. **Memory Service** - Long-term memory sync/retrieval (after artifact contracts stable)
9. **Simulation Engine** - Internal testing tool (requires all upstream components)

## Sources

- [IDEAS_HANDOFF.md - Backend architecture handoff](file:///Users/hafid/webapps/AI-CHAT-v2/gemini-live-api-examples/gemini-live-genai-python-sdk/IDEAS_HANDOFF.md)
- [PROJECT.md - Product requirements](file:///Users/hafid/webapps/AI-CHAT-v2/gemini-live-api-examples/gemini-live-genai-python-sdk/.planning/PROJECT.md)
- Current codebase analysis (main.py, gemini_live.py, frontend/)
