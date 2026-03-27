---
phase: 01-core-foundation
plan: 02
type: execute
wave: 1
depends_on: []
files_modified: [main.py, gemini_live.py, frontend/index.html, frontend/main.js]
autonomous: true
requirements: [SESS-01, SESS-02, SESS-03, SESS-04, SESS-05, SESS-06]
user_setup: []

must_haves:
  truths:
    - "User can start a new interview session from dashboard"
    - "Voice interaction works via Gemini Live API"
    - "Transcript appears incrementally in chat log during session"
    - "User can pause interview and see paused state"
    - "User can resume paused interview from same state"
    - "User can end interview and see session end screen"
  artifacts:
    - path: "main.py"
      provides: "Session management endpoints"
      exports: ["POST /api/sessions", "GET /api/sessions/{id}", "PATCH /api/sessions/{id}", "DELETE /api/sessions/{id}"]
    - path: "gemini_live.py"
      provides: "Enhanced session control with pause/resume"
      contains: "pause_session, resume_session, session state machine"
    - path: "frontend/index.html"
      provides: "Interview session UI with controls"
    - path: "frontend/main.js"
      provides: "Session lifecycle management"
  key_links:
    - from: "frontend/main.js"
      to: "/api/sessions"
      via: "fetch POST to start session"
      pattern: "fetch.*api/sessions.*POST"
    - from: "main.py"
      to: "gemini_live.py"
      via: "GeminiLive.start_session()"
      pattern: "gemini_client\\.start_session"
    - from: "gemini_live.py"
      to: "/ws"
      via: "WebSocket for real-time audio"
      pattern: "websocket.*send.*receive"
---

<objective>
Build the live interview session foundation: start new sessions, real-time voice via Gemini Live, incremental transcript capture, and pause/resume/end controls.

Purpose: Voice-based interview practice is the core product. Users need full session control with state preservation for realistic practice that accommodates interruptions.

Output: Working interview sessions with full lifecycle management (start, pause, resume, end) and incremental transcript capture.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-core-foundation/01-CONTEXT.md
@.planning/phases/01-core-foundation/01-UI-SPEC.md
@main.py
@gemini_live.py
@frontend/index.html
@frontend/main.js
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create session management API endpoints</name>
  <files>main.py</files>
  <action>
    Add to main.py (in-memory storage for MVP, upgrade to PostgreSQL in Plan 1.3):

    Session state machine:
    - States: "pending" → "active" → "paused" → "active" → "ended"
    - Valid transitions:
      - pending → active (start)
      - active → paused (pause)
      - paused → active (resume)
      - active → ended (end)
      - paused → ended (end)

    Endpoints:
    1. POST /api/sessions - accepts {context_id, interview_type?: "hr" | "hiring"}
       - Validate context exists (from Plan 1.1)
       - Create session: {session_id, context_id, state: "active", transcript: [], started_at}
       - Return: {session_id, context, state}

    2. GET /api/sessions/{id} - retrieve session
       - Return: {session_id, context_id, state, transcript[], started_at, updated_at}

    3. PATCH /api/sessions/{id} - update session state
       - Accept: {action: "pause" | "resume" | "end"}
       - Validate state transition
       - Update state, record timestamp
       - Return: {session_id, state, previous_state}

    4. DELETE /api/sessions/{id} - end and cleanup session
       - Set state to "ended"
       - Return: {success: true}

    In-memory session store: sessions = {} (upgrade to DB in Plan 1.3)
  </action>
  <verify>
    <automated>curl -X POST http://localhost:8000/api/sessions -H "Content-Type: application/json" -d '{"context_id": "test"}' | python -m json.tool</automated>
  </verify>
  <done>
    - Create session returns session_id with active state
    - Get session returns full session data
    - Pause changes state from active → paused
    - Resume changes state from paused → active
    - End changes state to ended
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Enhance gemini_live.py for session control</name>
  <files>gemini_live.py</files>
  <action>
    Modify gemini_live.py to support pause/resume:

    1. Add session state tracking:
       - self.session_state = "active" | "paused" | "ended"
       - self.transcript_buffer = [] (accumulates transcripts)
       - self.last_checkpoint = None (for resume)

    2. Add pause_session() method:
       - Set session_state = "paused"
       - Stop processing audio input (queue but don't send)
       - Flush transcript_buffer to session store
       - Return: {state: "paused", transcript_snapshot: [...]}

    3. Add resume_session() method:
       - Set session_state = "active"
       - Resume sending queued audio
       - Return: {state: "active"}

    4. Add end_session() method:
       - Set session_state = "ended"
       - Final transcript flush
       - Cleanup queues
       - Return: {state: "ended", final_transcript: [...]}

    5. Modify start_session() to:
       - Accept session_id parameter
       - Incrementally save transcript every 10-15 seconds (checkpoint)
       - Check session_state before processing audio (skip if paused)
       - Use asyncio.Event for pause signaling

    Key insight: Audio queue continues buffering during pause, but sending to Gemini stops.
  </action>
  <verify>
    <automated>python -c "from gemini_live import GeminiLive; print('Module imports successfully')"</automated>
  </verify>
  <done>
    - GeminiLive class has pause_session, resume_session, end_session methods
    - Session state machine implemented
    - Transcript checkpoints every 10-15 seconds
    - Pause stops audio sending but buffers input
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Wire WebSocket to session management</name>
  <files>main.py</files>
  <action>
    Modify /ws endpoint in main.py:

    1. Accept session_id as query parameter: /ws?session_id={id}
       - Validate session exists and is in "active" state
       - Return WebSocket close if session not found or not active

    2. Integrate session state checks:
       - Before forwarding audio to Gemini: check session_state
       - On pause: send WS message {type: "session_paused"}
       - On resume: send WS message {type: "session_resumed"}
       - On end: send WS message {type: "session_ended", transcript: [...]}

    3. Add transcript persistence:
       - Every 10-15 seconds: save accumulated transcript to session store
       - On turn_complete: append to session.transcript
       - Format: {speaker: "user" | "gemini", text: string, timestamp: ISO string}

    4. Handle disconnection:
       - On WS close: don't end session automatically (allow reconnect)
       - Session ends only via explicit end action
       - Log disconnect timestamp for audit
  </action>
  <verify>
    <automated>python -c "import main; print('main.py imports successfully')"</automated>
  </verify>
  <done>
    - /ws accepts session_id query param
    - Session state validated on connection
    - Transcript saved incrementally to session store
    - Pause/resume/end events sent via WebSocket
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Build interview session UI</name>
  <files>frontend/index.html, frontend/main.js</files>
  <action>
    Update frontend/index.html:

    1. Add Interview Session section (separate from existing demo UI):
       - Session header: "Interview Session" + status indicator
       - Status states: Connecting | Active | Paused | Ended

    2. Add control panel (replaces existing controls for interview mode):
       - Start Interview button (from dashboard)
       - During session: Pause | End buttons
       - When paused: Resume | End buttons
       - When ended: Close button (returns to dashboard)

    3. Transcript panel enhancements:
       - Real-time transcript display (existing chat-log)
       - Speaker labels: "You" vs "Interviewer"
       - Timestamps on each message
       - Auto-scroll to latest

    4. Session end summary (when session ends):
       - "Interview Complete" heading
       - Transcript count: "You exchanged N messages"
       - Button: "View Full Transcript" | "Back to Dashboard"

    Preserve existing demo UI for testing - add interview UI as separate section.
    Use UI-SPEC.md colors: status Active=green (#22c55e), Paused=yellow (#eab308), Ended=gray (#6b7280).
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Interview section exists with status indicator
    - Control panel has Pause/Resume/End based on state
    - Transcript shows speaker labels and timestamps
    - Session end summary displays
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 5: Wire frontend session lifecycle</name>
  <files>frontend/main.js</files>
  <action>
    Add to frontend/main.js:

    1. InterviewSession class:
       - startSession(contextId): POST /api/sessions, then connect WebSocket
       - pauseSession(): PATCH /api/sessions/{id} with action=pause
       - resumeSession(): PATCH /api/sessions/{id} with action=resume
       - endSession(): PATCH /api/sessions/{id} with action=end

    2. WebSocket integration:
       - Extend GeminiClient to accept session_id
       - Handle new message types:
         - session_paused: update UI to paused state
         - session_resumed: update UI to active state
         - session_ended: show end summary

    3. UI state management:
       - updateSessionState(state): switch statement
         - "active": show Pause + End buttons, green status
         - "paused": show Resume + End buttons, yellow status
         - "ended": show summary, gray status

    4. Transcript handling:
       - Append incoming transcripts with speaker label
       - Add timestamp: new Date().toLocaleTimeString()
       - Auto-scroll chat log

    5. Connection flow:
       - User clicks "Start Interview" → create session → connect WS with session_id
       - On WS open → send initial prompt (interviewer introduction)
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Start Interview creates session and connects
    - Pause button sends pause request, UI updates
    - Resume button sends resume request, UI updates
    - End button ends session, shows summary
    - Transcript updates in real-time with timestamps
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 6: Implement incremental transcript checkpoints</name>
  <files>main.py, gemini_live.py</files>
  <action>
    Implement checkpoint system for transcript persistence:

    1. In gemini_live.py:
       - Add checkpoint_interval = 15 (seconds)
       - Add last_checkpoint_time tracking
       - In receive_loop: after each transcription, check if checkpoint due
       - Add flush_transcript() method to send accumulated transcripts

    2. In main.py /ws handler:
       - Add background task: every checkpoint_interval seconds
       - Call session.update_transcript(transcript_buffer)
       - Clear buffer after flush
       - On pause/resume/end: force flush before state change

    3. Session transcript format:
       ```
       [
         {"speaker": "user", "text": "Hello", "timestamp": "2026-03-27T10:00:00Z"},
         {"speaker": "gemini", "text": "Hi there!", "timestamp": "2026-03-27T10:00:05Z"}
       ]
       ```

    4. On session end: ensure final flush completes before returning
  </action>
  <verify>
    <automated>python -c "
import asyncio
import time
# Simulate checkpoint timing test
start = time.time()
checkpoints = []
for i in range(3):
    checkpoints.append(time.time() - start)
    time.sleep(15)
print('Checkpoints at:', [round(t, 1) for t in checkpoints])
assert checkpoints[1] - checkpoints[0] >= 14, 'Checkpoint interval too short'
print('Checkpoint timing OK')
"</automated>
  </verify>
  <done>
    - Transcript saved every 15 seconds during active session
    - Pause triggers immediate flush
    - Resume continues checkpointing
    - End triggers final flush
    - Session store contains complete transcript
  </done>
</task>

</tasks>

<verification>
Overall phase verification:
1. Start interview → session created → WebSocket connects → transcript appears
2. During interview → pause → status changes to paused → audio buffered
3. Resume → status changes to active → buffered audio processed
4. End → transcript saved → session end summary shown
5. Verify transcript persisted with timestamps and speaker labels
</verification>

<success_criteria>
- All 6 requirements (SESS-01 through SESS-06) implemented
- Session state machine works correctly (active ↔ paused → ended)
- Transcript captured incrementally every 15 seconds
- Pause preserves state, resume continues from checkpoint
- End saves final transcript and shows summary
- Frontend UI reflects session state accurately
</success_criteria>

<output>
After completion, create `.planning/phases/01-core-foundation/01-core-foundation-02-SUMMARY.md` documenting:
- Session state machine implementation
- Checkpoint mechanism details
- WebSocket message formats
- Any deviations from plan
- Known issues or technical debt
</output>
