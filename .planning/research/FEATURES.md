# Feature Landscape

**Domain:** AI-Powered Job Interview Preparation App
**Researched:** 2026-03-27

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Resume Upload & Parsing** | Users expect to upload their resume (PDF/DOCX) and have it automatically parsed into a structured profile | Medium | Auto-extraction expected; manual editing is nice-to-have but not MVP |
| **Job Description Input** | Users want to practice for specific roles; JD input enables tailored questions | Low | Text paste is sufficient; URL parsing is bonus |
| **AI Mock Interviews (Voice)** | Core product promise — users expect realistic voice conversation practice | Medium | Gemini Live API handles this; must feel natural with low latency |
| **Behavioral Question Bank** | Standard interview prep includes common behavioral questions (STAR method) | Low | Need 50+ questions across categories (leadership, conflict, achievement, failure) |
| **Technical Question Bank** | For technical roles — coding concepts, system design, problem-solving | Medium | Questions must match role level (junior vs senior) |
| **Instant Feedback After Session** | Users expect immediate actionable insights, not waiting | High | Requires structured rubric + AI analysis pipeline |
| **Session Recording/Transcript** | Users want to review what they said and how they said it | Medium | Transcript capture is essential; audio playback is bonus |
| **Scoring/Rubric Results** | Users need concrete scores to track improvement (1-5 scale across dimensions) | Medium | Dimensions: clarity, confidence, relevance, structure, technical accuracy |
| **Question Types Matching Interview Stages** | Users expect HR screening, hiring manager, technical rounds to feel different | Medium | Requires interviewer agent differentiation |
| **Basic Progress Dashboard** | Users want to see "X sessions completed" and score trends | Low | Simple chart showing scores over time |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multiple Interviewer Agents** | HR Manager vs Hiring Manager vs Technical Interviewer — each has distinct style, priorities, question patterns | High | Requires versioned agent configs; enables realistic "loop" simulation |
| **Agent Handoff Mid-Session** | Simulate real interview loop where candidate meets multiple interviewers sequentially | High | Backend must manage session state, context transfer between agents |
| **Pre-Interview Coaching (Storytelling Architect)** | Help users craft compelling stories BEFORE the interview — extract, structure, refine their STAR stories | High | Separate pipeline from live interviews; requires interactive story-building UX |
| **Post-Interview Coaching (Answer Doctor)** | Deep-dive into specific answers after session — rewrite together, practice improved version | High | Requires session artifact access + interactive coaching flow |
| **Long-Term Memory Integration** | AI remembers user's past stories, weaknesses, improvements — references them naturally during sessions | Very High | Supermemory integration; privacy controls critical; high complexity but strong moat |
| **JD-Resume Match Scoring** | Show users how well their resume matches the job description before practicing | Medium | ATS-style analysis; helps users understand gaps |
| **Customizable Agent Presets** | Users/admins can configure interviewer strictness, focus areas, question style | Medium | Admin dashboard + versioned presets in database |
| **Structured Feedback with Rubric Breakdown** | Not just "you did well" — specific scores on communication, technical depth, cultural fit, etc. | Medium | Requires well-designed rubric + AI prompt engineering |
| **Answer Framework Support** | STAR, CAR, PBR, CIRCLES frameworks available for different question types | Low-Medium | Framework selection + AI evaluation against framework criteria |
| **Session Pause/Resume** | Real interviews have breaks; users appreciate flexibility during practice | Medium | Requires session state persistence |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Text-Only Chat Interviews** | Defeats the purpose of voice-first realism; users need spoken practice | Voice-first with transcript as artifact; text chat for support only |
| **Gamification (Badges, Leaderboards)** | Interview prep is serious/stressful; game mechanics feel tone-deaf | Use progress tracking, streaks (if any) sparingly; focus on improvement metrics |
| **Real-Time Analytics Dashboard During Session** | Distracts from realism; users should feel like they're in an interview, not a dashboard | Show minimal UI during session; full debrief after |
| **Simulated/Admin-Only Interviews** | High complexity, low value — live AI sessions are the product | Focus on user-driven live sessions; recorded sessions for demo only |
| **Manual Resume Field Editing** | Users expect auto-extraction to work; manual editing is tedious and signals broken automation | Invest in better parsing; provide "regenerate from resume" option |
| **Multi-Language Support (MVP)** | Dilutes focus; English-only is sufficient for initial launch | Add languages after PMF is proven; Gemini supports many languages already |
| **Mobile Apps (MVP)** | Web-first is correct; native apps are expensive distraction | Responsive web design; PWA if needed later |
| **Peer Mock Interviews** | Scheduling nightmare; quality variance; Pramp tried this and shifted to Exponent | AI-only for consistency, availability, scalability |
| **Video Recording of User** | Privacy concerns outweigh value; audio + transcript is sufficient | Focus on audio quality; video sharing (user's camera feed to AI) is optional |
| **Automated Job Application Submission** | Scope creep; not interview prep; high liability | Stay focused on interview practice only |

## Feature Dependencies

```
Resume Upload → Candidate Profile → Interview Context Builder → Live Session
Job Description → Job Profile ────────────────────────────────┘

Live Session → Transcript Capture → Debrief & Analysis → Progress Tracking
                              ↓
                    Coaching Modes (Pre/Post)

Interview Agents → Agent Handoff → Multi-Round Simulation

Long-Term Memory ← Session Artifacts (transcripts, scores, feedback)
```

**Hard Dependencies:**
- Document Ingestion must precede Live Sessions (need profile context)
- Live Sessions must precede Debrief (need transcript/data)
- Debrief must precede Progress Tracking (need structured scores)
- Interview Agents must exist before Agent Handoff

**Soft Dependencies:**
- Coaching Modes work best after users have session history
- Long-Term Memory requires stable artifact model first

## MVP Recommendation

**Phase 1 (Core Practice Loop):**
1. Resume Upload & Parsing (PDF only, auto-extract)
2. Job Description Input (text paste)
3. Live Interview Sessions (voice-first, Gemini Live)
4. Basic Interview Agent (Hiring Manager preset)
5. Session Transcript Capture
6. Post-Session Debrief (structured rubric scores + 2-3 key insights)
7. Progress Dashboard (score history chart)

**Phase 2 (Differentiation):**
1. Multiple Interviewer Agents (HR + Hiring Manager)
2. Agent Handoff (2-interviewer minimum)
3. Answer Framework Support (STAR toggle)
4. JD-Resume Match Scoring

**Phase 3 (Coaching & Memory):**
1. Pre-Interview Coaching (Storytelling Architect)
2. Post-Interview Coaching (Answer Doctor)
3. Long-Term Memory Integration
4. Customizable Agent Presets

**Defer:**
- Mobile apps (web-first)
- Multi-language (English MVP)
- Video recording of user
- Peer interviews

## Sources

- [Yoodli AI](https://www.yoodli.ai/) — AI roleplay platform, enterprise-focused
- [Pramp](https://www.pramp.com/) — Peer mock interviews (now on Exponent)
- [Big Interview](https://biginterview.com/) — AI mock interviews with video feedback
- [Interviews.chat](https://interviews.chat/) — AI interview helper with framework support
- [FinalRound AI](https://www.finalroundai.com/) — AI interview platform
- [Google Interview Warmup](https://interviewwarmup.withgoogle.com/) — Free AI interview practice
- [FACE Prep](https://www.faceprep.in/) — Campus placement prep platform
- Market research on interview prep app features and user expectations (2025-2026)
