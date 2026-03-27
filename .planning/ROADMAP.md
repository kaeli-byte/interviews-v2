# Roadmap: Job Interview Prep App

**Project:** Job Interview Prep App
**Granularity:** Coarse (3 phases, 2-3 plans each)
**Parallelization:** Enabled

## Phase 1: Core Foundation

**Goal:** Users can upload documents, create interview context, and conduct voice-based interview sessions with basic authentication.

**Rationale:** Document ingestion is foundational for interview context. Live sessions are the core product. Auth is required for user management.

### Plans

**Plans:** 3 plans

- [x] 01-core-foundation-01-PLAN.md — Document ingestion, profile extraction, interview context creation
- [x] 01-core-foundation-02-PLAN.md — Live interview sessions with pause/resume/end controls
- [ ] 01-core-foundation-03-PLAN.md — Authentication and user-scoped document management

#### Plan 1.1: Document Ingestion + Interview Context (01-PLAN.md)
- [x] DOC-01: User can upload resume (PDF format)
- [x] DOC-02: User can upload resume (DOCX format)
- [x] DOC-03: User can input job description as text
- [x] DOC-04: User can import job description from URL
- [x] DOC-05: System extracts candidate profile from resume
- [x] DOC-06: System extracts job profile from JD
- [x] DOC-07: User can view extracted profile data
- [x] DOC-08: Extraction includes quality confidence score
- [x] DOC-09: User can create interview context (resume + job bind)

**Verification:** User can upload resume and JD, see extracted profiles, create interview context. **DONE**

#### Plan 1.2: Live Interview Sessions Foundation (02-PLAN.md)
- [x] SESS-01: User can start new interview session
- [x] SESS-02: Session supports real-time voice via Gemini Live
- [x] SESS-03: Session captures transcript incrementally
- [x] SESS-04: User can pause interview session
- [x] SESS-05: User can resume paused interview
- [x] SESS-06: User can end interview session

**Verification:** User can conduct complete voice interview with pause/resume. **DONE**

#### Plan 1.3: Authentication + User Management (03-PLAN.md)
- USER-01: User can sign up with email/password
- USER-02: User session persists across browser refresh
- USER-03: User can view their documents
- USER-04: User can delete their documents

**Verification:** User can sign up, log in, manage their documents.

---

## Phase 2: Differentiation Layer

**Goal:** Users can conduct structured interviews with different interviewer agents and receive detailed post-session debriefs with scoring.

**Rationale:** Multiple interviewer personas and post-session feedback create competitive advantage.

### Plans

#### Plan 2.1: Interview Agents + Handoff
- AGNT-01: System provides HR Manager interviewer persona
- AGNT-02: System provides Hiring Manager interviewer persona
- AGNT-03: Agents are configurable via versioned database configs
- AGNT-04: User can switch agents during session (handoff)
- AGNT-05: Handoff includes context summary to new agent

**Verification:** User can select interviewer type, conduct session with that persona, switch mid-session.

#### Plan 2.2: Debrief & Analysis
- DEBR-01: Debrief auto-generates after session ends
- DEBR-02: Debrief provides structured rubric scores
- DEBR-03: Debrief provides qualitative feedback with evidence
- DEBR-04: User can view debrief history
- DEBR-06: User can regenerate debrief with updated rubric

**Verification:** After session ends, user sees rubric scores and feedback with transcript evidence.

#### Plan 2.3: Session Improvements
- SESS-07: Session state persists across reconnects
- SESS-08: User can view session history (past interviews)

**Verification:** User can reconnect after network drop and resume. User sees list of past sessions.

---

## Phase 3: Polish & Preparation

**Goal:** Users can track progress over time and system is prepared for coaching/memory features in future releases.

**Rationale:** Progress tracking extends value. Architecture prep for future phases.

### Plans

#### Plan 3.1: Progress Tracking
- DEBR-05: System tracks progress over time (score trends)

**Verification:** User can view score trends across sessions.

#### Plan 3.2: Architecture Preparation
- Document data models for future coaching pipelines
- Define memory sync contracts for future Supermemory integration

**Verification:** Architecture supports future phases without retrofit.

---

## Phase Dependencies

```
Phase 1 ─────────────────────────────────────────► Phase 2 ──────────────────────► Phase 3
    │                                           │                                 │
    ├─ Plan 1.1 (DOC) ─────┐                    │                                 │
    │                      │                    │                                 │
    ├─ Plan 1.2 (SESS) ────┼──► Session infra ──┤                                 │
    │                      │                    │                                 │
    └─ Plan 1.3 (USER) ────┘                    │                                 │
                                                 │                                 │
                              Agent configs ─────┼─► Plan 2.1 (AGNT)               │
                                                 │                                 │
                              Transcript/data ───┼─► Plan 2.2 (DEBR) ─────────────► Plan 3.1
                                                 │                                 │
                              Session polish ───► Plan 2.3 ────────────────────────► Plan 3.2
```

---

## Coverage

| Phase | Requirements | Status |
|-------|--------------|--------|
| Phase 1 | 15 requirements | 15 complete, 4 pending |
| Phase 2 | 12 requirements | Pending |
| Phase 3 | 7 requirements | Pending |

**Total:** 39 requirements mapped ✓ (15 complete)

---

*Roadmap created: 2026-03-27*
*Granularity: coarse | Parallel execution enabled*
*Phase 1 plans created: 2026-03-27*
*Plan 1.2 completed: 2026-03-27*
