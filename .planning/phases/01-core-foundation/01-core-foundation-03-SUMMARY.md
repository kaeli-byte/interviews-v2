---
phase: 01-core-foundation
plan: 03
subsystem: authentication
tags: [auth, jwt, bcrypt, user-management]
requires: []
provides: [user-auth, jwt-tokens, user-scoped-documents]
affects: [main.py, frontend/main.js, frontend/index.html, frontend/document-upload.js, frontend/interview-session.js]
tech_stack:
  added: [bcrypt, python-jose]
  patterns: [JWT auth, password hashing, token-based sessions]
key_files:
  created: [.env.example]
  modified: [main.py, frontend/main.js, frontend/index.html, frontend/style.css, frontend/document-upload.js, frontend/interview-session.js, requirements.txt]
decisions:
  - Use bcrypt directly instead of passlib due to bcrypt 5.0+ compatibility issues
  - JWT tokens stored in localStorage for session persistence
  - 7-day token expiration for MVP
  - User-scoped document storage in uploads/{user_id}/resumes and uploads/{user_id}/job-descriptions
metrics:
  duration: ~2 hours
  completed: 2026-03-27
---

# Phase 1 Plan 3: Authentication + User Management Summary

**One-liner:** Complete authentication system with email/password signup, JWT-based session persistence, and user-scoped document management using bcrypt for password hashing and python-jose for JWT handling.

## What Was Built

### Backend Authentication (main.py)

**Dependencies added:**
- `bcrypt` - Password hashing (used directly due to passlib compatibility issues)
- `python-jose[cryptography]` - JWT token generation and validation

**Configuration:**
- `SECRET_KEY` - JWT signing key (from env, defaults to "dev-secret-change-in-prod")
- `ALGORITHM` - "HS256"
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 10080 (7 days)

**Auth Endpoints:**
| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/signup` | POST | No | Create account with email/password |
| `/api/auth/login` | POST | No | Login and receive JWT token |
| `/api/auth/logout` | POST | Yes | Blacklist token (logout) |
| `/api/auth/me` | GET | Yes | Get current user info |

**Request/Response Formats:**

Signup/Login Request:
```json
{"email": "user@example.com", "password": "password123"}
```

Signup/Login Response:
```json
{
  "user": {"id": "uuid", "email": "user@example.com"},
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2026-04-03T05:40:35.690173"
}
```

### User-Scoped Document Management

All document and profile endpoints now require authentication:
- `GET /api/documents` - List user's documents
- `POST /api/documents/resume` - Upload resume (PDF/DOCX)
- `POST /api/documents/job-description` - Upload JD (text/URL)
- `DELETE /api/documents/{id}` - Delete user's document
- `POST /api/profiles/extract-from-resume` - Extract resume profile
- `POST /api/profiles/extract-from-jd` - Extract job profile
- `POST /api/interview-contexts` - Create interview context
- `POST /api/sessions` - Create interview session

**Storage Structure:**
```
uploads/
  {user_id}/
    resumes/
    job-descriptions/
```

### Frontend Authentication (frontend/main.js)

**Auth Class:**
- `signup(email, password)` - Create account
- `login(email, password)` - Login
- `logout()` - Clear session
- `checkAuth()` - Validate token on page load
- `getToken()` - Get current token
- `isAuthenticated()` - Check auth state
- `fetch(url, options)` - Authenticated fetch wrapper

**LocalStorage Keys:**
- `auth_token` - JWT token string
- `auth_user` - JSON stringified user object

### UI Components (frontend/index.html)

**Auth Modal:**
- Tabbed interface (Sign In / Sign Up)
- Email and password fields
- Password minimum 8 characters
- Error message display

**User Menu:**
- Displays user email
- Logout button
- Shown only when authenticated

**Welcome Bar:**
- Shows "Welcome, {email}" message
- Gradient background styling

### Styles (frontend/style.css)

Added auth-specific styles:
- `.auth-section` - Centered auth modal
- `.auth-modal` - Card styling
- `.auth-tabs` and `.auth-tab-btn` - Tab interface
- `.form-group` - Form field styling
- `.error-message` - Error display
- `.user-menu` - User menu styling
- `.welcome-bar` - Welcome message bar

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] passlib/bcrypt compatibility issue**
- **Found during:** Task 2 - Testing signup endpoint
- **Issue:** passlib 1.7.4 is incompatible with bcrypt 5.0.0+ (installed by `passlib[bcrypt]`). Error: "password cannot be longer than 72 bytes" and "module 'bcrypt' has no attribute '__about__'"
- **Fix:** Removed passlib dependency, use bcrypt directly with `bcrypt.hashpw()` and `bcrypt.checkpw()`
- **Files modified:** main.py
- **Commit:** 7b6c2b6

## Technical Debt

1. **In-memory storage** - Users, documents, and sessions stored in memory. Will be migrated to PostgreSQL in Plan 1.3.

2. **Token blacklist in memory** - Logout blacklists tokens in memory only. Tokens will persist until server restart. Production should use Redis for token blacklist.

3. **Development JWT secret** - Default secret key "dev-secret-change-in-prod" should be replaced with strong random key in production via `JWT_SECRET_KEY` environment variable.

4. **Datetime deprecation warnings** - Using `datetime.utcnow()` which is deprecated. Should migrate to `datetime.now(datetime.UTC)` in future cleanup.

## Verification Results

Tested successfully:
- Signup creates user and returns JWT token
- Login validates credentials and returns JWT token
- Protected endpoints return 401 without valid token
- Protected endpoints work with valid JWT token
- Token persists in localStorage across page refresh

## Commits

| Hash | Description |
|------|-------------|
| f24d36a | feat(01-core-foundation-03): add authentication system backend |
| 2718b8e | feat(01-core-foundation-03): add frontend authentication handling |
| f25974b | feat(01-core-foundation-03): add authentication UI components |
| 7b6c2b6 | fix(01-core-foundation-03): use bcrypt directly instead of passlib |
