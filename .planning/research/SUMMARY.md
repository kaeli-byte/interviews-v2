# Project Research Summary

**Project:** AI-Powered Job Interview Preparation App
**Domain:** AI Interview Preparation / Voice-First Coaching Platform
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

This is a voice-first AI interview preparation platform that enables users to practice job interviews with realistic AI interviewer agents. Based on research, the recommended approach uses FastAPI with async WebSocket handling for real-time Gemini Live sessions, PostgreSQL for persistent data (profiles, sessions, transcripts, agent configs), Redis for ephemeral session state, and Supermemory for long-term user memory. The architecture follows a service-layer pattern with clear component boundaries: Document Ingestion for resume/JD parsing, Session Orchestrator for interview lifecycle, Agent Registry for versioned interviewer configs, and Debrief Engine for rubric-based feedback.

The key differentiators from existing products are: multiple interviewer personas with mid-session handoff, pre/post-interview coaching pipelines (Storytelling Architect, Answer Doctor), and long-term memory that remembers user progress across sessions. The MVP focuses on the core practice loop: resume upload → job description input → live voice interview → transcript capture → structured debrief with rubric scores.

Key risks include: (1) generic feedback that destroys user trust—mitigated by evidence-backed rubric design with turn-level citations; (2) voice latency breaking realism—mitigated by streaming audio chunks immediately and targeting <300ms latency; (3) session loss on reconnect—mitigated by incremental transcript persistence and explicit pause/resume state machine; (4) memory becoming a privacy liability—mitigated by designing deletion and audit trails from schema inception.

## Key Findings

### Recommended Stack

**Core technologies:**
- **FastAPI 0.115+**: Web framework with WebSocket handling—excellent async support, automatic OpenAPI docs, dependency injection
- **PostgreSQL 16+**: Primary data store—ACID compliance, JSONB for flexible agent configs, full-text search for memory retrieval
- **SQLAlchemy 2.0+**: ORM with modern `Mapped[]` syntax and full async support—industry standard with mature ecosystem
- **asyncpg 0.30+**: PostgreSQL async driver—fastest async driver, 20-30% faster than psycopg3
- **Redis 7.4+**: Session state, caching, pub/sub—sub-millisecond latency for live session state and agent handoff coordination
- **google-genai 1.68.0**: Gemini SDK—`client.aio.live.connect()` for async live sessions with audio/video/text streaming
- **pypdf 6.9.2 + python-docx 1.2.0**: Document parsing—lightweight, covers 90% of resumes; add pdfplumber only if layout analysis needed
- **Supermemory 1.2+**: Long-term memory API—three context methods (Memory API, User Profiles, RAG) for personalized coaching
- **orjson 3.11.7**: Fast JSON serialization—5-10x faster than stdlib for WebSocket JSON and API responses

**Critical version requirements:**
- Pydantic 2.12.5+ (v2 uses Rust-based core for 5-50x performance improvement)
- SQLAlchemy 2.0.37+ (modern syntax with `mapped_column()`)
- Redis-py 5.0+ with `redis[hiredis]` for 2-3x performance

### Expected Features

**Must have (table stakes):**
- Resume Upload & Parsing (PDF auto-extract) — users expect seamless profile creation
- Job Description Input (text paste) — enables tailored questions for specific roles
- AI Mock Interviews (Voice) — core product promise, must feel natural with low latency
- Instant Feedback After Session — structured rubric scores + actionable insights
- Session Transcript Capture — users want to review what they said
- Scoring/Rubric Results — concrete 1-5 scores across dimensions (clarity, confidence, relevance, structure, technical accuracy)
- Basic Progress Dashboard — score trends over time

**Should have (differentiators):**
- Multiple Interviewer Agents (HR Manager, Hiring Manager, Technical) — distinct styles and priorities
- Agent Handoff Mid-Session — simulates real interview loop with multiple interviewers
- Pre-Interview Coaching (Storytelling Architect) — helps users craft STAR stories before interviewing
- Post-Interview Coaching (Answer Doctor) — deep-dive into specific answers after sessions
- JD-Resume Match Scoring — ATS-style analysis to show alignment gaps
- Long-Term Memory Integration — AI remembers user's past stories and weaknesses

**Defer (v2+):**
- Mobile apps — web-first is correct
- Multi-language support — English-only for MVP
- Video recording of user — privacy concerns outweigh value
- Peer mock interviews — scheduling nightmare, quality variance
- Gamification (badges, leaderboards) — tone-deaf for serious interview prep

### Architecture Approach

The architecture follows a layered service pattern with clear component boundaries. The backend owns session lifecycle completely (not a thin proxy to Gemini), maintaining full state machine, transcript, and event log for replay, debrief, and auditability. Agent and coach configs are versioned database records, not hardcoded—enabling experimentation without code deploys. Sessions are event-sourced as ordered event streams, not just final transcript text. The Interview Context entity binds candidate profile + job profile, referenced consistently by sessions and coaching pipelines.

**Major components:**
1. **Document Ingestion Service** — parses PDF/DOCX, extracts text, builds candidate/job profiles
2. **Interview Context Builder** — binds resume + job profiles into reusable context for sessions/coaching
3. **Session Orchestrator** — manages session lifecycle (create/start/pause/resume/end), state machine, agent binding
4. **Gemini Live Adapter** — wraps google-genai SDK for audio/video/text streaming and event reception
5. **Agent Registry** — stores versioned agent definitions (prompts, policies, rubrics)
6. **Debrief Engine** — generates rubric scores, extracts evidence from transcripts, computes trends
7. **Coach Orchestrator** — runs pre-interview (Storytelling Architect) and post-interview (Answer Doctor) pipelines
8. **Memory Service** — synces session/coaching artifacts to Supermemory with retrieval queries

### Critical Pitfalls

1. **Generic, Non-Actionable Feedback** — Design rubric with observable behavioral markers (e.g., "uses STAR format" vs. "answers well"); require debrief to cite specific transcript turns as evidence for each score; version rubrics independently from agent configs.

2. **Voice Latency Breaks Realism** — Target <300ms latency from Gemini response start to speaker output; stream audio chunks immediately (don't wait for full response); use WebSocket binary frames for audio (not base64-in-JSON); monitor P95 latency and alert when >500ms.

3. **Session Loss on Reconnect** — Persist transcript turns incrementally (every 10-15 seconds or after each turn); store Gemini Live session ID for potential reattachment; implement explicit pause/resume endpoints; queue outgoing messages during disconnect and replay on reconnect.

4. **Resume/Job Parsing Produces Garbage Profiles** — Use multi-stage parsing (text extraction → section detection → LLM entity extraction); compute extraction quality score and flag low-confidence parses for manual review; provide "preview and confirm" UX before binding profile to session.

5. **AI Hallucinates Feedback or Fabricates Evidence** — Require debrief to include turn IDs for every evidence citation; build verification pass to cross-check cited turns exist and match excerpt; use low temperature (0.1-0.3) for analytical tasks; separate observation from interpretation in prompts.

6. **Memory System Becomes Privacy Liability** — Design memory with deletion from day 1 (every memory item has user_id and deletion cascade); provide user-facing "memory audit" UI; implement soft deletion with retention window; log all memory writes/reads for audit trail.

7. **Agent Handoff Breaks Conversational Context** — Generate handoff summary before switch ("Candidate discussed X, strengths in Y, concerns about Z"); inject prior transcript turns into new agent context; maintain session-level context that persists across agent boundaries.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Practice Loop
**Rationale:** Foundation layer—document ingestion and live sessions are prerequisites for all downstream features (debrief, coaching, memory). Session Orchestrator must be hardened with proper state persistence before adding complexity.

**Delivers:**
- Resume Upload & Parsing (PDF only, auto-extract with quality scoring)
- Job Description Input (text paste)
- Live Interview Sessions (voice-first via Gemini Live)
- Single Interviewer Agent (Hiring Manager preset)
- Session Transcript Capture (incremental persistence)
- Post-Session Debrief (structured rubric scores + evidence citations)
- Progress Dashboard (score history chart)

**Addresses Features:** Resume Upload, JD Input, Voice Interviews, Transcript, Scoring, Progress Dashboard

**Avoids Pitfalls:** Session loss (incremental persistence + pause/resume), Generic feedback (evidence-backed rubric design), Parsing garbage (quality scoring + manual override path)

**Stack Used:** FastAPI, PostgreSQL, SQLAlchemy/asyncpg, pypdf, python-docx, google-genai

### Phase 2: Differentiation Layer
**Rationale:** Builds on stable session foundation. Agent Registry with versioning enables multiple interviewer personas and handoff. Debrief Engine refinement creates improvement loop. These features differentiate from basic mock interview products.

**Delivers:**
- Multiple Interviewer Agents (HR Manager + Hiring Manager + Technical)
- Agent Handoff Mid-Session (with context summary generation)
- Answer Framework Support (STAR toggle with evaluation criteria)
- JD-Resume Match Scoring (ATS-style analysis)
- Agent Config Versioning (immutable versions, session references version_id)

**Addresses Features:** Multiple Agents, Agent Handoff, JD-Resume Match, Framework Support

**Avoids Pitfalls:** Handoff context loss (handoff summary + prior context injection), No version pinning (versioned configs with session FK to version_id)

**Architecture Implemented:** Agent Registry + Versioning, Interview Context Builder enhancement

### Phase 3: Coaching & Memory
**Rationale:** Coaching pipelines require stable session artifacts (transcripts, debriefs). Memory integration must wait until artifact contracts are stable to avoid costly retrofitting. These features create long-term user retention and personalization moat.

**Delivers:**
- Pre-Interview Coaching (Storytelling Architect pipeline)
- Post-Interview Coaching (Answer Doctor pipeline)
- Long-Term Memory Integration (Supermemory sync + retrieval)
- Story Bank UI (reusable coaching artifacts)
- Customizable Agent Presets (admin dashboard)

**Addresses Features:** Pre/Post Coaching, Long-Term Memory, Customizable Agents

**Avoids Pitfalls:** Memory privacy liability (deletion + audit from inception), Coaching non-reusable (persistent artifact model + story bank), Hallucinated feedback (verification pass already in Phase 1)

**Stack Used:** Supermemory API integration, Coach Orchestrator, Memory Service

### Phase Ordering Rationale

- **Document Ingestion before Live Sessions:** Cannot conduct contextual interviews without candidate/job profiles. Research shows garbage profiles destroy user trust immediately.
- **Session Orchestrator (hardened) before Agents:** Must have reliable session persistence, transcript capture, and state machine before adding agent complexity.
- **Single Agent before Handoff:** Handoff requires two stable agents and context transfer protocol—cannot work if base agent is unstable.
- **Stable Artifacts before Memory:** Memory schema becomes coupled to unstable upstream models if integrated too early. Research explicitly warns against this anti-pattern.
- **Coaching after Debrief:** Coaching pipelines need access to session transcripts and debrief scores as input.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3 (Memory Integration):** Supermemory Python examples are limited; REST API integration patterns need validation. Privacy/deletion implementation details require careful design.
- **Phase 2 (Agent Handoff):** Mid-session context transfer protocol is complex; needs experimentation with context summarization strategies.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Core Practice Loop):** FastAPI + WebSocket + PostgreSQL + asyncpg are well-documented with established patterns. Document parsing (pypdf, python-docx) has mature ecosystems.
- **Phase 1 (Debrief Engine):** Rubric-based evaluation with evidence citation follows established AI analysis patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified via official docs, PyPI, and Context7. FastAPI, SQLAlchemy, asyncpg, google-genai have excellent documentation. |
| Features | HIGH | Synthesized from 9+ competitor products (Yoodli, Big Interview, FinalRound, etc.) with consistent patterns across table stakes. |
| Architecture | HIGH | Based on existing codebase analysis (main.py, gemini_live.py) plus IDEAS_HANDOFF.md. Service-layer pattern is well-established. |
| Pitfalls | MEDIUM | Synthesized from user reviews, industry analysis, and technical documentation. Some probability estimates are inferred rather than empirically measured. |

**Overall confidence:** HIGH

### Gaps to Address

- **Supermemory Integration:** Limited Python SDK examples; will need to validate REST API patterns during Phase 3 planning. Recommend starting with simple Memory API writes before complex retrieval.
- **Extraction Quality Scoring:** No specific algorithm defined for resume parsing quality—will need experimentation during Phase 1 to determine thresholds for "flag for review."
- **Latency Optimization:** Target <300ms is based on industry research, but actual Gemini Live latency needs measurement in production-like conditions. May require edge proxy or connection optimization.
- **Rubric Design:** Behavioral markers for each rubric dimension need detailed design before Phase 1 debrief implementation—this is critical for avoiding generic feedback pitfall.

## Sources

### Primary (HIGH confidence)
- **Context7: fastapi** — WebSocket handling, dependency injection, async patterns
- **Context7: sqlalchemy** — ORM 2.0 syntax, async session management, mapped_column()
- **Context7: google-genai** — Live API connection, streaming audio/video/text
- **Official FastAPI Docs** — https://fastapi.tiangolo.com/
- **Official SQLAlchemy 2.0 Docs** — https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- **Official Redis Docs** — https://redis.io/docs/
- **Official Google Gen AI SDK** — https://github.com/googleapis/python-genai

### Secondary (MEDIUM confidence)
- **PyPI package documentation** — pypdf 6.9.2, python-docx 1.2.0, asyncpg 0.30, orjson 3.11.7
- **Supermemory Documentation** — https://supermemory.ai/docs/ (limited Python examples)
- **Competitor analysis** — Yoodli AI, Big Interview, FinalRound AI, Interview Warmup, Interviews.chat
- **User reviews** — Trustpilot and app store reviews for billing issues, feedback quality complaints

### Tertiary (LOW confidence)
- **marker-ai** — OCR for scanned PDFs (not verified with Context7, deferred until needed)
- **Latency thresholds** — Industry research on conversation flow UX (needs production validation)

---

*Research completed: 2026-03-27*
*Ready for roadmap: yes*
