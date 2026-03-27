# Codebase Concerns

**Analysis Date:** 2026-03-27

## Security Considerations

**Critical: Overly Permissive CORS**
- Issue: CORS allows all origins (`allow_origins=["*"]`) with credentials enabled
- Files: `main.py` (lines 30-36)
- Risk: Any website can make requests to this API, potentially consuming API quota
- Recommendation: Restrict to known frontend origins or use token-based auth

**Critical: No Authentication**
- Issue: WebSocket endpoint has no authentication - anyone with the URL can connect
- Files: `main.py` (lines 47-119)
- Risk: Unauthorized API usage, quota exhaustion, potential abuse
- Recommendation: Add API key validation, JWT tokens, or session-based auth

**High: Missing API Key Handling**
- Issue: App crashes with unclear error if `GEMINI_API_KEY` is not set
- Files: `main.py` (line 24), `gemini_live.py` (line 28)
- Risk: Poor UX, silent failures
- Recommendation: Add validation at startup with clear error message

**Medium: No Rate Limiting**
- Issue: No limits on WebSocket connections or message rates
- Files: `main.py`
- Risk: API quota exhaustion from abuse
- Recommendation: Implement connection limits and message throttling

## Tech Debt

**High: Unbounded Queues**
- Issue: Audio, video, and text input queues can grow without limit
- Files: `main.py` (lines 54-56), `gemini_live.py` (lines 59, 71, 84)
- Impact: Memory exhaustion under load
- Fix approach: Add max queue size with backpressure

**Medium: Hardcoded Configuration**
- Issue: Voice config hardcoded to "Puck", system instruction hardcoded
- Files: `gemini_live.py` (lines 38, 42)
- Impact: Requires code changes to customize
- Fix approach: Move to environment variables or config file

**Medium: Bare Exception Handling**
- Issue: Multiple `except: pass` patterns swallow errors
- Files: `main.py` (line 118), `gemini_live.py` (lines 63-66, 76-79, 88-90)
- Impact: Silent failures make debugging difficult
- Fix approach: Log errors appropriately

## Performance Bottlenecks

**Low Video Frame Rate**
- Issue: Video capture at only 1 FPS
- Files: `frontend/media-handler.js` (lines 91-93, 113-115)
- Impact: Poor user experience, limited visual interaction
- Improvement path: Increase to 5-10 FPS with configurable rate

**No Connection Reuse**
- Issue: Each WebSocket creates a new Gemini client instance
- Files: `main.py` (lines 65-67)
- Impact: Session overhead, no connection pooling
- Improvement path: Consider connection pooling for multi-user deployments

**Image Quality Settings**
- Issue: JPEG compression hardcoded at 0.7 quality, fixed 640x480 resolution
- Files: `frontend/media-handler.js` (lines 138-141)
- Impact: Suboptimal balance of quality vs bandwidth
- Improvement path: Make configurable via environment

## Missing Critical Features

**No Health Check Endpoint**
- Problem: No way to verify service is running
- Blocks: Load balancer health checks, deployment verification
- Fix: Add `/health` endpoint returning 200 OK

**No Automatic Reconnection**
- Problem: WebSocket disconnects require manual page refresh
- Files: `frontend/main.js`, `frontend/gemini-client.js`
- Fix: Add exponential backoff reconnection logic

**No Tests**
- Problem: No test suite exists
- Risk: Breaking changes go undetected
- Priority: High - critical for production

**No Request Logging/Metrics**
- Problem: No visibility into API usage, latency, errors
- Blocks: Monitoring, capacity planning
- Fix: Add structured logging, integrate with observability

## Configuration Gaps

**Limited Environment Options**
- Current: Only `GEMINI_API_KEY`, `MODEL`, `PORT` supported
- Missing: Log level, CORS origins, queue sizes, video FPS
- Recommendation: Document all env vars, add `.env.example` with all options

**No Type Safety**
- Issue: Python code has no type hints
- Impact: Reduced maintainability, harder refactoring
- Recommendation: Add type annotations, use mypy

## Fragile Areas

**Frontend Message Handling**
- Why fragile: No validation of incoming JSON messages, could crash on malformed data
- Files: `frontend/main.js` (lines 38-47)
- Safe modification: Add try/catch and schema validation
- Test coverage: None

**WebSocket Disconnect Handling**
- Why fragile: Task cancellation may not complete before websocket.close()
- Files: `main.py` (lines 113-119)
- Risk: Connection leaks, zombie connections

## Scaling Limits

**Single Instance Design**
- Current: One process, no horizontal scaling
- Limit: Single user session per instance (one WebSocket)
- Scaling path: Add Redis for session state, multiple workers with sticky sessions

---

*Concerns audit: 2026-03-27*