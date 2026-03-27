# Requirements: Job Interview Prep App

**Defined:** 2026-03-27
**Core Value:** Realistic interview practice with actionable feedback — the fastest way to improve interview performance through repeated practice with AI-powered feedback loops.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Document Ingestion

- [x] **DOC-01**: User can upload resume (PDF format)
- [x] **DOC-02**: User can upload resume (DOCX format)
- [x] **DOC-03**: User can input job description as text
- [x] **DOC-04**: User can import job description from URL
- [x] **DOC-05**: System extracts candidate profile (name, headline, skills, experience) from resume
- [x] **DOC-06**: System extracts job profile (company, role, requirements) from JD
- [x] **DOC-07**: User can view extracted profile data
- [x] **DOC-08**: Extraction includes quality confidence score
- [x] **DOC-09**: User can create interview context (bind resume + job profile)

### Live Interview Sessions

- [ ] **SESS-01**: User can start new interview session with selected interviewer agent
- [ ] **SESS-02**: Session supports real-time voice conversation via Gemini Live
- [ ] **SESS-03**: Session captures and stores transcript in real-time (incremental)
- [ ] **SESS-04**: User can pause interview session
- [ ] **SESS-05**: User can resume paused interview session
- [ ] **SESS-06**: User can end interview session
- [ ] **SESS-07**: Session state persists across reconnects
- [ ] **SESS-08**: User can view session history (past interviews)

### Interview Agents

- [ ] **AGNT-01**: System provides HR Manager interviewer persona
- [ ] **AGNT-02**: System provides Hiring Manager interviewer persona
- [ ] **AGNT-03**: Agents are configurable via versioned database configs
- [ ] **AGNT-04**: User can switch agents during session (handoff)
- [ ] **AGNT-05**: Handoff includes context summary to new agent

### Debrief & Analysis

- [ ] **DEBR-01**: Debrief auto-generates after session ends
- [ ] **DEBR-02**: Debrief provides structured rubric scores (multiple dimensions)
- [ ] **DEBR-03**: Debrief provides qualitative feedback with evidence from transcript
- [ ] **DEBR-04**: User can view own debrief history
- [ ] **DEBR-05**: System tracks progress over time (score trends)
- [ ] **DEBR-06**: User can regenerate debrief with updated rubric

### User Management

- [ ] **USER-01**: User can sign up with email/password
- [ ] **USER-02**: User session persists across browser refresh
- [ ] **USER-03**: User can view their documents
- [ ] **USER-04**: User can delete their documents

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Coaching Modes

- **COACH-01**: Pre-interview coaching pipeline (Storytelling Architect)
- **COACH-02**: Post-interview coaching pipeline (Answer Doctor)
- **COACH-03**: Coaching runs produce reusable story assets
- **COACH-04**: User can invoke coaching before or after sessions

### Agent Customization

- **CUST-01**: Admin can create agent presets
- **CUST-02**: Admin can configure agent behavior via knobs (not prompts)
- **CO3-03**: Admin can version and activate agent configs
- **CUST-04**: Per-session config overrides supported

### Long-term Memory

- **MEM-01**: Session data automatically syncs to memory after completion
- **MEM-02**: Coaching outputs sync to memory
- **MEM-03**: Live sessions can retrieve relevant memories during interview
- **MEM-04**: User can query their memory
- **MEM-05**: User can delete memory items
- **MEM-06**: Memory includes audit trail

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Simulated Interviews (admin-only) | Deferred until live session/debrief contracts stable |
| Manual document field editing | MVP uses auto-extraction only |
| Real-time analytics during session | Focus on realism over dashboard density |
| Video in interviews | Voice-first MVP |
| Mobile apps | Web-first MVP |
| Multi-language support | English-only MVP |
| Video recording/playback | Transcript-only for MVP |
| Gamification features | Anti-feature per research |
| Peer interview practice | Out of scope for v1 |
| OAuth login | Email/password sufficient for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOC-01 | Phase 1 | Complete |
| DOC-02 | Phase 1 | Complete |
| DOC-03 | Phase 1 | Complete |
| DOC-04 | Phase 1 | Complete |
| DOC-05 | Phase 1 | Complete |
| DOC-06 | Phase 1 | Complete |
| DOC-07 | Phase 1 | Complete |
| DOC-08 | Phase 1 | Complete |
| DOC-09 | Phase 1 | Complete |
| SESS-01 | Phase 1 | Pending |
| SESS-02 | Phase 1 | Pending |
| SESS-03 | Phase 1 | Pending |
| SESS-04 | Phase 1 | Pending |
| SESS-05 | Phase 1 | Pending |
| SESS-06 | Phase 1 | Pending |
| SESS-07 | Phase 1 | Pending |
| SESS-08 | Phase 1 | Pending |
| AGNT-01 | Phase 2 | Pending |
| AGNT-02 | Phase 2 | Pending |
| AGNT-03 | Phase 2 | Pending |
| AGNT-04 | Phase 2 | Pending |
| AGNT-05 | Phase 2 | Pending |
| DEBR-01 | Phase 2 | Pending |
| DEBR-02 | Phase 2 | Pending |
| DEBR-03 | Phase 2 | Pending |
| DEBR-04 | Phase 2 | Pending |
| DEBR-05 | Phase 2 | Pending |
| DEBR-06 | Phase 2 | Pending |
| USER-01 | Phase 1 | Pending |
| USER-02 | Phase 1 | Pending |
| USER-03 | Phase 1 | Pending |
| USER-04 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Complete: 9 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after initial definition*