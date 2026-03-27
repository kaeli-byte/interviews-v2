---
phase: 01-core-foundation
plan: 03
type: execute
wave: 2
depends_on: [01, 02]
files_modified: [requirements.txt, main.py, frontend/index.html, frontend/main.js]
autonomous: true
requirements: [USER-01, USER-02, USER-03, USER-04]
user_setup: []

must_haves:
  truths:
    - "User can sign up with email and password"
    - "User session persists after browser refresh"
    - "User can see their uploaded documents in dashboard"
    - "User can delete their documents"
  artifacts:
    - path: "requirements.txt"
      provides: "Auth dependencies"
      contains: "passlib[bcrypt], python-jose[cryptography]"
    - path: "main.py"
      provides: "Authentication endpoints and user management"
      exports: ["POST /api/auth/signup", "POST /api/auth/login", "POST /api/auth/logout", "GET /api/auth/me", "GET /api/users/{id}/documents"]
    - path: "frontend/index.html"
      provides: "Auth forms and user-aware dashboard"
    - path: "frontend/main.js"
      provides: "Auth state management and JWT handling"
  key_links:
    - from: "frontend/main.js"
      to: "/api/auth/signup"
      via: "fetch POST with credentials"
      pattern: "fetch.*api/auth/signup"
    - from: "main.py"
      to: "JWT token"
      via: "token validation on protected routes"
      pattern: "jwt\\.decode|get_current_user"
    - from: "main.py"
      to: "uploads/{user_id}/"
      via: "user-scoped document storage"
      pattern: "uploads.*user_id"
---

<objective>
Implement user authentication with email/password signup, JWT-based session persistence, and user-scoped document management.

Purpose: Multi-user support requires authentication to isolate documents and sessions. JWT tokens enable persistent sessions across browser refresh without requiring re-login.

Output: Working auth system with signup/login, JWT token management, user-scoped documents.
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
@frontend/index.html
@frontend/main.js
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add auth dependencies and database setup</name>
  <files>requirements.txt, main.py</files>
  <action>
    Add to requirements.txt:
    - passlib[bcrypt] (password hashing per D-04)
    - python-jose[cryptography] (JWT token handling per D-04)

    Run: pip install -r requirements.txt

    In main.py, add:
    - In-memory user store for MVP: users = {} (email → user dict)
    - Token blacklist for logout: blacklisted_tokens = set()
    - JWT configuration:
      - SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
      - ALGORITHM = "HS256"
      - ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 (7 days for MVP)

    Add .env.example entry:
      JWT_SECRET_KEY=your-secret-key-here

    Note: MVP uses in-memory storage. Plan 1.3 upgrade to PostgreSQL will migrate to database.
  </action>
  <verify>
    <automated>python -c "from passlib.context import CryptContext; from jose import jwt; print('Auth imports OK')"</automated>
  </verify>
  <done>
    - passlib and python-jose in requirements.txt and importable
    - JWT configuration constants defined
    - In-memory stores initialized
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create authentication API endpoints</name>
  <files>main.py</files>
  <action>
    Add to main.py:

    1. POST /api/auth/signup - accepts {email, password}
       - Validate email format (basic regex)
       - Validate password length >= 8
       - Check if email already exists → return 409 Conflict
       - Hash password with bcrypt (passlib)
       - Create user: {id: uuid, email, hashed_password, created_at}
       - Generate JWT token (include user_id, email, exp)
       - Return: {user: {id, email}, token, expires_at}

    2. POST /api/auth/login - accepts {email, password}
       - Find user by email
       - Verify password with bcrypt (passlib.verify)
       - Generate JWT token
       - Return: {user: {id, email}, token, expires_at}
       - Return 401 if invalid credentials

    3. POST /api/auth/logout - accepts auth header
       - Extract token from Authorization: Bearer {token}
       - Add token to blacklist
       - Return: {success: true}

    4. GET /api/auth/me - accepts auth header
       - Validate token (not expired, not blacklisted)
       - Return: {user: {id, email}}
       - Return 401 if invalid

    Helper functions:
    - create_access_token(data: dict, expires_delta: timedelta) → str
    - get_current_user(token: str) → dict (raises 401 if invalid)
    - verify_password(plain, hashed) → bool
    - hash_password(password) → str
  </action>
  <verify>
    <automated>curl -X POST http://localhost:8000/api/auth/signup -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123"}' | python -m json.tool</automated>
  </verify>
  <done>
    - Signup creates user and returns JWT token
    - Login validates credentials and returns JWT token
    - Logout blacklists token
    - GET /api/auth/me returns current user from valid token
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Add user-scoped document endpoints</name>
  <files>main.py</files>
  <action>
    Modify existing document endpoints to be user-scoped:

    Update in main.py:

    1. GET /api/documents (protected)
       - Require valid JWT token (get_current_user dependency)
       - List only current user's documents from uploads/{user_id}/
       - Return: [{document_id, filename, type, size, created_at}]

    2. POST /api/documents/resume (protected)
       - Require valid JWT token
       - Save to uploads/{user_id}/resumes/
       - Return: {document_id, filename, type, size}

    3. POST /api/documents/job-description (protected)
       - Require valid JWT token
       - Save to uploads/{user_id}/job-descriptions/
       - Return: {document_id, content_preview}

    4. DELETE /api/documents/{id} (protected)
       - Require valid JWT token
       - Verify document belongs to user
       - Delete file
       - Return: {success: true}

    Directory structure:
    uploads/
      {user_id}/
        resumes/
        job-descriptions/

    Migration: Move existing demo_user files to new structure on first auth request.
  </action>
  <verify>
    <automated>curl -X GET http://localhost:8000/api/documents -H "Authorization: Bearer INVALID_TOKEN" 2>&1 | grep -i "401\|unauthorized"</automated>
  </verify>
  <done>
    - Document endpoints require authentication
    - Invalid token returns 401
    - Users see only their own documents
    - Documents stored in user-scoped directories
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Build auth UI forms</name>
  <files>frontend/index.html</files>
  <action>
    Update frontend/index.html:

    1. Replace existing auth-section with tabbed auth modal:
       - Tab interface: Sign Up | Login
       - Sign Up form:
         - Email input (type=email, required)
         - Password input (type=password, minlength=8, required)
         - Submit button: "Create Account"
       - Login form:
         - Email input (type=email, required)
         - Password input (type=password, required)
         - Submit button: "Sign In"
       - Error message area below forms

    2. Add user menu to dashboard header:
       - User email display
       - Logout button
       - Hidden when not authenticated

    3. Dashboard section (new):
       - Welcome message: "Welcome, {email}"
       - Navigation: Documents | Interviews | Settings
       - Document list area (populated by API)
       - Upload button

    4. State-based visibility:
       - auth-section: visible when !authenticated
       - dashboard-section: visible when authenticated
       - Use .hidden class for toggling

    Follow UI-SPEC.md: spacing (md=16px between form fields), colors (accent=#0ea5e9 for buttons).
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Auth modal has Sign Up and Login tabs
    - Forms have email and password fields
    - Dashboard shows user email after login
    - Logout button visible in dashboard
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 5: Wire frontend auth and JWT handling</name>
  <files>frontend/main.js</files>
  <action>
    Add to frontend/main.js:

    1. Auth class:
       - signup(email, password): POST /api/auth/signup
         - Store token in localStorage
         - Store user in state
       - login(email, password): POST /api/auth/login
         - Store token in localStorage
         - Store user in state
       - logout(): POST /api/auth/logout
         - Remove token from localStorage
         - Clear user state
       - checkAuth(): GET /api/auth/me
         - Validate token on page load
         - Refresh UI state
       - getToken(): retrieve from localStorage
       - isAuthenticated(): boolean check

    2. localStorage keys:
       - 'auth_token': JWT token string
       - 'auth_user': JSON stringified user object

    3. Auth state management:
       - updateAuthUI(isAuthenticated):
         - If true: show dashboard, hide auth-section
         - If false: show auth-section, hide dashboard
       - On page load: call checkAuth(), update UI accordingly

    4. API request helper:
       - apiRequest(url, options): automatically add Authorization header
       - Handle 401 responses: redirect to auth screen

    5. Form handlers:
       - signupForm.onsubmit: preventDefault, call auth.signup()
       - loginForm.onsubmit: preventDefault, call auth.login()
       - logoutBtn.onclick: call auth.logout(), update UI
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Signup form creates account and logs in
    - Login form authenticates and stores JWT
    - Token persists in localStorage
    - Page refresh maintains auth state
    - Logout clears token and shows auth screen
    - API calls include Authorization header
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 6: Wire user-scoped document management</name>
  <files>frontend/main.js, frontend/index.html</files>
  <action>
    Update frontend/main.js:

    1. DocumentList class (user-aware):
       - fetchDocuments(): GET /api/documents (with auth header)
       - renderDocuments(documents):
         - Empty state: "No documents yet" message
         - List: filename, type icon, upload date, delete button
       - deleteDocument(id): confirm → DELETE → refresh

    2. Upload form integration:
       - File upload: include auth token in request
       - On success: refresh document list
       - Show user's email in upload confirmation

    3. Dashboard initialization:
       - On auth success: loadDashboard()
       - Load user's documents
       - Load user's interview contexts (from Plan 1.1)
       - Show welcome message

    4. Error handling:
       - 401 from any request → redirect to auth screen
       - Network errors → show toast notification
       - Form validation errors → inline messages

    Update frontend/index.html:
    - Add document empty state component
    - Add delete confirmation dialog
  </action>
  <verify>
    <automated>MISSING - requires browser test harness</automated>
  </verify>
  <done>
    - Document list shows only current user's documents
    - Delete requires confirmation
    - Upload works with auth token
    - 401 responses redirect to auth
    - Dashboard loads user-specific data
  </done>
</task>

</tasks>

<verification>
Overall phase verification:
1. Sign up with email/password → JWT token stored → dashboard visible
2. Refresh browser → token retrieved from localStorage → session persists
3. Upload document → appears in user's document list
4. Delete document → confirmation → removed from list and filesystem
5. Logout → token cleared → auth screen shown
6. Login with same credentials → access previous documents
</verification>

<success_criteria>
- All 4 requirements (USER-01 through USER-04) implemented
- JWT token stored in localStorage and persists across refresh
- Document endpoints require authentication
- Users see and manage only their own documents
- Auth UI follows UI-SPEC.md design
- Logout properly clears session
</success_criteria>

<output>
After completion, create `.planning/phases/01-core-foundation/01-core-foundation-03-SUMMARY.md` documenting:
- Auth endpoints with request/response formats
- JWT configuration and token structure
- User-scoped document storage structure
- Any deviations from plan
- Known issues or technical debt (e.g., in-memory storage for MVP)
</output>
