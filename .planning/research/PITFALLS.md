# Domain Pitfalls: AI Interview Preparation Apps

**Domain:** Job Interview Preparation / AI Coaching
**Researched:** 2026-03-27
**Confidence:** MEDIUM (synthesized from multiple industry sources, user reviews, and technical documentation)

---

## Critical Pitfalls

Mistakes that cause rewrites, user abandonment, or legal/compliance issues.

### Pitfall 1: Generic, Non-Actionable Feedback

**What goes wrong:** AI provides vague feedback like "good job" or "speak more confidently" without specific, actionable guidance tied to actual interview performance.

**Why it happens:**
- Rubric design is an afterthought rather than a core system
- Feedback generated from transcript summary rather than evidence-backed analysis
- No grounding of scores in specific transcript turns or behavioral markers
- Rubric not versioned, making consistency impossible to validate

**Consequences:**
- Users lose trust after 1-2 sessions ("this doesn't help me improve")
- High churn rate — users don't return for repeated practice
- Word-of-mouth damage: "the feedback is useless"
- Product becomes a novelty, not a coaching tool

**Prevention:**
- Design rubric dimensions with observable behavioral markers (e.g., "uses STAR format" vs. "answers well")
- Require debrief engine to cite specific transcript turns as evidence for each score
- Version rubrics independently from agent configs to allow iteration without breaking historical comparisons
- Build "regenerate with different lens" capability to recover from bad debriefs

**Detection:**
- User feedback contains phrases like "too generic," "not specific," "could have guessed this"
- Low session repeat rate (<2 sessions per user)
- Debrief scores cluster tightly (lack of discriminative power)

---

### Pitfall 2: Voice Conversation Latency Breaks Realism

**What goes wrong:** Response delays exceed 500-800ms, causing users to interrupt, talk over the AI, or feel like they're talking to a broken system.

**Why it happens:**
- Audio buffering misconfigured (too aggressive)
- Round-trip architecture adds latency (frontend → backend → Gemini → backend → frontend)
- No optimization for time-to-first-audio-byte
- Backend acts as thin proxy rather than optimizing stream handling

**Consequences:**
- Interviews feel stilted and unnatural
- Users develop bad habits (over-articulating, pausing too long)
- Product fails its core value proposition: realistic practice
- Users abandon mid-session

**Prevention:**
- Target <300ms latency from Gemini response start to speaker output
- Stream audio chunks immediately, don't wait for full response
- Use WebSocket binary frames for audio (not base64-in-JSON)
- Consider peer-to-peer or edge proxy for Gemini connection if latency persists
- Monitor P95 latency per session; alert when >500ms

**Detection:**
- User complaints about "talking over" or "waiting too long"
- Transcript shows frequent interruptions (user speaks within 200ms of AI ending)
- Session abandonment spikes correlate with latency metrics

---

### Pitfall 3: Resume/Job Parsing Produces Garbage Profiles

**What goes wrong:** Extracted candidate profiles and job profiles are missing critical information, misparse sections, or produce unusable structured data.

**Why it happens:**
- Off-the-shelf parsers not tuned for resume formats (multi-column, creative layouts)
- No fallback when extraction quality is low
- Single-shot extraction with no human-in-the-loop correction path
- PDF/DOCX parsing loses formatting context needed for accurate extraction

**Consequences:**
- Interview context is misaligned (AI asks about wrong skills/experience)
- Coaching recommendations are irrelevant
- Users lose confidence: "it doesn't even know my background"
- Downstream systems (memory, simulation) propagate bad data

**Prevention:**
- Use multi-stage parsing: text extraction → section detection → LLM-based entity extraction
- Compute extraction quality score; flag low-confidence parses for manual review
- Provide "preview and confirm" UX before binding profile to interview session
- Store raw extraction + cleaned version for debugging and reprocessing
- Support manual field overrides (even if post-MVP)

**Detection:**
- Extraction jobs fail or timeout (>10% failure rate)
- Profile fields empty or contain parsing artifacts ("### Skills" in skills JSON)
- User-initiated re-uploads of same document

---

### Pitfall 4: Session State Loss on Reconnect

**What goes wrong:** When WebSocket drops (network blip, browser sleep), session is lost entirely. User must restart interview from beginning.

**Why it happens:**
- No session checkpointing during live interview
- Gemini Live session reference not persisted
- Transcript only saved at session end (not incrementally)
- Reconnection logic assumes fresh session, not resume

**Consequences:**
- Users lose 15-30 minutes of interview progress
- Extreme frustration; trust destroyed
- Negative reviews: "lost my entire interview"
- Support burden for manual recovery requests

**Prevention:**
- Persist transcript turns incrementally (every 10-15 seconds or after each turn)
- Store Gemini Live session ID in session record for potential reattachment
- Implement session state machine with explicit states: `created` → `started` → `paused` → `resumed` → `ended`
- Support explicit pause/resume endpoints (not just implicit reconnect)
- Queue outgoing messages during disconnect; replay on reconnect

**Detection:**
- Users report "lost my interview" in support tickets
- Session records show high ratio of `started` to `ended` without corresponding completed transcripts
- WebSocket error logs show reconnects without successful session recovery

---

### Pitfall 5: AI Hallucinates Feedback or Fabricates Evidence

**What goes wrong:** Debrief references transcript turns that don't exist, invents user statements, or scores dimensions without evidence.

**Why it happens:**
- LLM generates plausible-sounding feedback without grounding constraints
- No verification that cited evidence matches transcript
- Rubric evaluation prompt doesn't require turn-level citations
- Temperature too high for analytical tasks

**Consequences:**
- Credibility destroyed when user notices: "I never said that"
- Legal/compliance risk if fabricated feedback is negative
- Users learn to ignore feedback entirely
- Reputation damage: "the AI makes things up"

**Prevention:**
- Require debrief to include turn IDs for every evidence citation
- Build verification pass: cross-check all cited turns exist and match excerpt
- Use low temperature (0.1-0.3) for analytical/evaluation tasks
- Structure prompt to separate observation from interpretation
- Consider retrieval-augmented generation: feed specific turns as context, not full transcript

**Detection:**
- Automated checks: cited turn IDs don't exist in transcript
- User flags: "this quote is wrong" or "this didn't happen"
- Evidence excerpts don't match referenced transcript turns (checksum mismatch)

---

### Pitfall 6: Memory System Becomes Privacy Liability

**What goes wrong:** Long-term memory stores sensitive data (performance scores, weak areas, personal stories) without user controls, audit trail, or deletion mechanism.

**Why it happens:**
- Memory designed for maximum personalization, not user control
- No data retention policy implemented
- Deletion only removes surface record, not embedded memories
- GDPR/CCPA compliance retrofitted after launch

**Consequences:**
- Legal exposure under data protection regulations
- User backlash: "you're keeping everything about me"
- Enterprise customers blocked from adoption (data governance review fails)
- Costly re-engineering to add deletion/audit post-launch

**Prevention:**
- Design memory with deletion from day 1: every memory item has user_id and deletion cascade
- Provide user-facing "memory audit" UI: see what's stored, delete individual items
- Implement soft deletion with retention window (e.g., 30 days) before permanent removal
- Log all memory writes and reads for audit trail
- Separate PII from performance data in storage schema
- Document data retention policy publicly

**Detection:**
- User asks "what do you know about me?" and system cannot answer
- Deletion request leaves orphaned references
- Memory queries return data from deleted users (referential integrity failure)

---

### Pitfall 7: Agent Handoff Breaks Conversational Context

**What goes wrong:** When switching from HR Manager to Hiring Manager (or between any agents), the new agent has no context about what was already discussed. User must repeat themselves.

**Why it happens:**
- Handoff only transfers session ID, not conversation summary
- New agent system prompt doesn't include prior turns
- Context builder filters out "irrelevant" history that's actually critical
- No explicit handoff protocol with context summary generation

**Consequences:**
- User frustration: "I just told you this"
- Interview feels disjointed, not cohesive
- Reduced realism (real interviews have continuity)
- Users perceive AI as "dumb" or forgetful

**Prevention:**
- Generate handoff summary before switch: "Candidate discussed X, strengths in Y, concerns about Z"
- Inject prior transcript turns (last N turns or summarized) into new agent context
- Maintain session-level context that persists across agent boundaries
- Implement explicit handoff event type with payload: from_agent, to_agent, context_summary
- Allow new agent to acknowledge prior context: "Earlier you mentioned..."

**Detection:**
- Transcript shows new agent asking questions already answered
- Handoff events without corresponding context_summary in payload
- User comments: "you're not listening" or "I already said this"

---

## Moderate Pitfalls

Mistakes that cause friction, rework, or degraded UX but not catastrophic failure.

### Pitfall 8: No Version Pinning for Agent Configs

**What goes wrong:** Sessions reference agent by name (e.g., "HR Manager"), but agent behavior changes over time. Cannot reproduce exact interview conditions for replay or comparison.

**Why it happens:**
- Session stores `agent_id` or `agent_name`, not `agent_version_id`
- Agent configs updated in-place without versioning
- No schema for versioned prompts/policies/rubrics

**Consequences:**
- Cannot reproduce "that one great interview" for analysis
- A/B testing impossible (don't know which version ran)
- Regression when new config performs worse
- Simulation comparisons invalid

**Prevention:**
- Every agent config change creates new version; old versions immutable
- Session references `agent_version_id` (foreign key to specific version)
- Version metadata includes created_at, created_by, change_summary
- Admin can activate/deactivate versions, but historical sessions retain their version

---

### Pitfall 9: Debrief Blocked on Session End

**What goes wrong:** User must wait for debrief to complete before navigating away. Debrief takes 10-30 seconds. UX is blocked.

**Why it happens:**
- Debrief runs synchronously in session end flow
- No background job queue for async analysis
- Frontend polls/wait for debrief completion before showing results

**Consequences:**
- Poor UX: user stares at loading spinner
- Increased abandonment (users close tab before debrief renders)
- Server timeout risk for long debriefs
- No retry path if debrief fails

**Prevention:**
- Session end returns immediately; debrief triggered as background job
- Frontend shows "analyzing your interview" status; user can navigate and return
- Debriefs have status field: `pending` → `in_progress` → `completed` or `failed`
- Implement retry with exponential backoff for failed debriefs
- Notify user when debrief ready (in-app or email)

---

### Pitfall 10: Coaching Outputs Not Reusable Across Sessions

**What goes wrong:** Storytelling Architect produces great story assets, but they're session-locked. User can't build a reusable story bank.

**Why it happens:**
- Coach runs stored with FK to single session only
- No concept of "persistent artifact" separate from session
- Story outputs buried in session detail page

**Consequences:**
- Users repeat same story-building work each session
- Lost opportunity: story bank is high-value retention feature
- Coaching feels ephemeral, not cumulative

**Prevention:**
- Coach outputs have dual FK: session_id (origin) and user_id (ownership)
- Separate `story_assets` table with tags, usage_count, last_used_session_id
- UI surface: "Your Story Bank" accessible independent of sessions
- Allow manual story editing and merging post-coaching

---

### Pitfall 11: No Difficulty Adaptation During Session

**What goes wrong:** Agent asks same difficulty questions regardless of user performance. Strong candidates bored; struggling candidates overwhelmed.

**Why it happens:**
- Difficulty policy static per agent version
- No real-time performance signal fed back to question generation
- Agent prompt doesn't include adaptive difficulty logic

**Consequences:**
- One-size-fits-all experience
- Strong candidates finish thinking "that was too easy"
- Weak candidates feel discouraged
- Reduced perceived personalization

**Prevention:**
- Include difficulty_policy_json with escalation/de-escalation triggers
- Track running performance signal (e.g., answer completeness, confidence markers)
- Allow mid-session difficulty adjustment based on signals
- Surface difficulty level in session metadata for user awareness

---

## Minor Pitfalls

Nuisances that cause confusion or support tickets but not abandonment.

### Pitfall 12: Unclear Subscription/Billing Model

**What goes wrong:** Users don't realize it's a recurring charge. Feel deceived. Chargebacks and negative reviews.

**Prevention:**
- Explicit "This is a subscription. You will be charged $X/month" at checkout
- Send email confirmation with billing terms immediately after purchase
- Provide one-click cancellation with clear effective date
- Offer prorated refunds for early cancellation (MVP: manual, later: automated)

---

### Pitfall 13: No Audio/Video Device Selection

**What goes wrong:** User's default mic/camera is wrong device. Can't change without leaving session.

**Prevention:**
- Device picker before session start (list from `navigator.mediaDevices.enumerateDevices()`)
- Persist device preferences per user
- Allow mid-session device switch (with graceful re-initialization)

---

### Pitfall 14: Transcript Not Visible During Session

**What goes wrong:** User can't see what was said. Feels disoriented. Can't verify AI heard them correctly.

**Prevention:**
- Show rolling transcript in side panel or collapsible view
- Highlight current speaker
- Allow user to flag transcript errors mid-session ("that's not what I said")

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Document Ingestion | Garbage profiles from bad parsing (Pitfall 3) | Implement extraction quality scoring + manual override path |
| Live Sessions | Session loss on reconnect (Pitfall 4) | Incremental transcript persistence + explicit pause/resume |
| Interview Agents | Handoff context loss (Pitfall 7) | Generate handoff summary + inject prior context |
| Debrief Engine | Generic feedback (Pitfall 1) + Hallucination (Pitfall 5) | Evidence-backed rubric + turn ID citations + verification pass |
| Memory Integration | Privacy liability (Pitfall 6) | Design deletion + audit trail from schema inception |
| Agent Customization | No version pinning (Pitfall 8) | Versioned configs + session references version_id |
| Coaching Modes | Non-reusable outputs (Pitfall 10) | Persistent artifact model + story bank UI |

---

## Risk Mitigation Summary

| Risk | Severity | Probability | Mitigation Priority |
|------|----------|-------------|---------------------|
| Generic feedback | High | High | 1 (design rubric first) |
| Latency breaks realism | High | Medium | 2 (optimize streaming) |
| Parsing garbage profiles | High | High | 1 (quality scoring + override) |
| Session loss on reconnect | High | Medium | 2 (incremental persistence) |
| AI hallucinates evidence | High | Medium | 2 (verification pass) |
| Memory privacy liability | High | High | 1 (design deletion upfront) |
| Handoff context loss | Medium | High | 3 (handoff protocol) |
| No version pinning | Medium | High | 3 (versioned configs) |
| Debrief blocks UX | Medium | High | 3 (async job queue) |
| Coaching non-reusable | Low | Medium | 4 (artifact model) |
| Billing confusion | Medium | Low | 2 (clear terms) |

---

## Sources

- User reviews of BigInterview, InterviewBuddy, Prepladder on Trustpilot and app stores (billing issues, generic feedback complaints)
- Technical documentation on real-time voice AI latency thresholds (conversation flow UX research)
- Industry analysis of AI mock interview accuracy and hallucination risks
- WebSocket reconnection best practices from MDN and production case studies
- GDPR/CCPA compliance requirements for user data deletion and audit trails
- Document parsing accuracy benchmarks for resume/CV extraction systems
