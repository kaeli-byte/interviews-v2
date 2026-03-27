# Job Interview Prep App

## What This Is

A voice-first interview preparation application powered by Gemini Live API. Users upload resumes and job descriptions, then practice with AI interviewer agents that provide real-time conversation practice, followed by automated debriefs with structured feedback and scoring. The product serves job seekers preparing for technical and behavioral interviews.

## Core Value

Realistic interview practice with actionable feedback — the fastest way to improve interview performance through repeated practice with AI-powered feedback loops.

## Requirements

### Validated

- ✓ WebSocket-based real-time Gemini Live session — existing
- ✓ GeminiLive class with session management (start_session, send_audio, send_video, send_text, receive) — existing
- ✓ FastAPI backend with WebSocket endpoint (/ws) — existing
- ✓ Basic frontend UI for audio/video capture and chat — existing
- ✓ PCM audio processing via AudioWorklet — existing

### Active

- [ ] Document Ingestion — Upload resumes (PDF, DOCX) and job descriptions with text input
- [ ] Candidate Profile & Job Profile extraction from documents
- [ ] Interview Context Builder — bind resume profile + job profile for a session
- [ ] Live Interview Sessions — Full session lifecycle (create, start, pause, resume, end) with transcript capture
- [ ] Interview Agents — HR Manager and Hiring Manager interviewer types with versioned configs
- [ ] Session Handoff — Switch between interviewer agents during a session
- [ ] Debrief & Analysis — Auto-generated structured rubric scores and qualitative feedback after sessions
- [ ] User Progress Tracking — Historical trends across sessions
- [ ] Coaching Modes — Pre-interview (Storytelling Architect) and post-interview (Answer Doctor) coaching pipelines
- [ ] Agent Customization — Admin-configurable presets with runtime behavior knobs
- [ ] Long-term Memory — Automatic session/coaching memory sync with retrieval during live sessions

### Out of Scope

- Simulated Interviews (admin-only) — Deferred until live session infrastructure is stable
- Manual document field editing — MVP uses auto-extraction only
- Real-time live analytics during sessions — Focus on realism over dashboard density
- Mobile apps — Web-first MVP
- Multi-language support — English-only MVP

## Context

The codebase is a Gemini Live API prototype with FastAPI backend and vanilla JS frontend. The existing implementation demonstrates the core real-time audio/video/text communication with Gemini via WebSocket. The IDEAS_HANDOFF.md defines the full backend architecture required to evolve this prototype into a complete job interview prep product.

Key technical decisions already made:
- Backend owns session lifecycle, transcript, and event log (not thin proxy)
- Versioned database-backed agent configs and presets
- Postgres for metadata, Redis for ephemeral state, object storage for files
- Supermemory for long-term memory integration

## Constraints

- **Tech Stack**: FastAPI (Python) for backend, vanilla JS for frontend — existing choice
- **AI Runtime**: Gemini Live API — required for real-time voice interaction
- **Timeline**: Phased approach following the prioritized feature list in IDEAS_HANDOFF.md
- **Data Governance**: Memory system has privacy-sensitive implications — user deletion controls required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Backend-controlled session lifecycle | Better traceability, replay, debrief, simulation reuse | — Pending |
| Versioned dynamic agent configs | Faster iteration, exact reproducibility, better scaling | — Pending |
| Voice-first MVP | Gemini Live's strength; transcript captures everything needed | — Pending |
| Supermemory integration | Strong personalization but high complexity — build after stable artifact model | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state (users, feedback, metrics)

---
*Last updated: 2026-03-27 after initialization*