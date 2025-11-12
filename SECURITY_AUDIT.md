# FlowPilot - Comprehensive Security Audit and Code Review

**Framework:** Python/FastAPI  
**Date:** November 2025  
**Auditor Role:** Senior Principal Software Engineer and Security Auditor

---

## 🔐 Authentication Workflow Deep Dive

### Overview
FlowPilot uses **Google OAuth 2.0** with the Authorization Code flow for authentication. The application integrates with Google Calendar API and uses session-based authentication to maintain user state.

### Step-by-Step Authentication Flow

1. **User Initiates Login** (`/api/auth/init`)
   - User navigates to `/api/auth/init` endpoint
   - Application creates a Google OAuth Flow with client credentials
   - A unique `state` parameter is generated for CSRF protection
   - State is stored in server-side session (`request.session["state"]`)
   - User is redirected to Google's authorization URL

2. **User Grants Permissions**
   - User authenticates with Google
   - User grants calendar access permissions
   - Google redirects back to the application's callback URL with `code` and `state` parameters

3. **Authorization Code Exchange** (`/api/auth/callback`)
   - Application receives `code` and `state` from Google
   - Server validates `state` matches the session value (CSRF protection)
   - Application exchanges authorization code for access/refresh tokens via Google's token endpoint
   - OAuth credentials (access token, refresh token) are obtained

4. **User Information Retrieval**
   - Application uses credentials to call Google OAuth2 API
   - Retrieves user's email and name from Google
   
5. **Credential Storage**
   - User info is stored in `users` table (email, full_name)
   - OAuth credentials (tokens) are stored in `user_credentials` table as JSON
   - User email is stored in session (`request.session["user_email"]`)

6. **Accessing Protected Resources**
   - For calendar endpoints (`/events`), `authenticate_google_calendar()` is called
   - Function checks session for `user_email`
   - Retrieves stored OAuth credentials from database using email
   - Reconstructs `Credentials` object from JSON
   - Creates Google Calendar service with credentials
   - Makes authorized API calls to Google Calendar

### 3 Critical Security Checks

#### 1. **CSRF Protection via State Parameter Validation**
- **Location:** `router_auth.py:54-56`
- **Check:** Validates OAuth `state` parameter matches session state
- **Importance:** Prevents Cross-Site Request Forgery attacks where malicious sites trick users into authorizing access
- **Current Implementation:** ✅ Implemented
```python
if not session_state or session_state != state:
    raise HTTPException(status_code=400, detail="State mismatch")
```

#### 2. **Session-Based Authentication Check**
- **Location:** `calendar_services.py:24-26`
- **Check:** Validates user has active session before accessing protected resources
- **Importance:** Ensures only authenticated users can access calendar data
- **Current Implementation:** ✅ Implemented
```python
user_email = request.session.get("user_email")
if not user_email:
    raise HTTPException(status_code=401, detail="User not authenticated")
```

#### 3. **Credential Existence Validation**
- **Location:** `calendar_services.py:32-33`
- **Check:** Verifies OAuth credentials exist in database before use
- **Importance:** Prevents application errors and ensures user has completed OAuth flow
- **Current Implementation:** ✅ Implemented
```python
if not row:
    raise HTTPException(status_code=403, detail="No credentials found for user")
```

---

## 🔗 File Connectivity and Architecture Map

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      app/main.py (Entry Point)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ FastAPI App + SessionMiddleware                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────┬──────────────────────────────────┬───────────────────────┘
       │                                  │
       │                                  │
       ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────────┐
│  router_auth.py     │          │ router_calendar.py      │
│  (Auth Routes)      │          │ (Calendar Routes)       │
│                     │          │                         │
│  /api/auth/init     │          │  GET  /events           │
│  /api/auth/callback │          │  POST /events           │
└──────┬──────────────┘          └───────┬─────────────────┘
       │                                 │
       │                                 │
       │                                 ▼
       │                         ┌──────────────────────┐
       │                         │ calendar_services.py │
       │                         │ (Business Logic)     │
       │                         │                      │
       │                         │ - authenticate_*()   │
       │                         │ - GoogleCalendar     │
       │                         │   Service class      │
       │                         └──────┬───────────────┘
       │                                │
       ▼                                ▼
┌─────────────────────────────────────────────────────────┐
│                    database.py                          │
│                  (Data Layer)                           │
│                                                         │
│  SQLite Database: flowpilot.db                         │
│  ├── users table                                       │
│  └── user_credentials table                            │
└─────────────────────────────────────────────────────────┘
       ▲
       │
       └────── Google OAuth2 & Calendar APIs
```

### Component Dependencies

**Routes Layer** → **Services Layer** → **Data Layer** → **External APIs**

1. **Routes** (`router_auth.py`, `router_calendar.py`)
   - Handle HTTP requests/responses
   - Depend on: Services layer, Session middleware

2. **Services** (`calendar_services.py`, `llm_service.py`)
   - Business logic and external API integration
   - Depend on: Database, Google APIs

3. **Middleware** (SessionMiddleware)
   - Session management
   - Depends on: Secret key from environment

4. **Database** (`database.py`)
   - Data persistence
   - SQLite with two tables

5. **Configuration** (`config/config.py`)
   - Settings management using Pydantic
   - Loads from environment variables

### Three Most Critical Files

#### 1. **app/main.py** - Application Entry Point
**Role:** 
- Initializes the FastAPI application
- Sets up critical SessionMiddleware for authentication state
- Registers all API routers
- Triggers database initialization

**Critical Functions:**
- Loads environment variables
- Configures session middleware with secret key
- Includes authentication and calendar routers
- Calls `init_db()` on startup

**Dependencies:**
- `database.py` for DB initialization
- `router_auth.py` and `router_calendar.py` for routing
- Environment variables (especially `GOOGLE_CLIENT_SECRET` used as session secret)

**Why Critical:** 
Without proper initialization here, the entire application fails. The SessionMiddleware configuration is essential for OAuth state management and user session persistence.

---

#### 2. **app/router/router_auth.py** - Authentication Controller
**Role:**
- Implements OAuth 2.0 flow with Google
- Manages authentication lifecycle (login, callback, session creation)
- Stores user credentials and profile information

**Critical Functions:**
- `auth_init()`: Initiates OAuth flow, generates authorization URL
- `auth_callback()`: Handles OAuth callback, validates state, exchanges code for tokens, stores credentials

**Dependencies:**
- Google OAuth libraries (`google_auth_oauthlib`, `google.oauth2`)
- Session middleware from `main.py`
- Database for credential storage
- Environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)

**Why Critical:**
This is the security gateway. Any vulnerability here compromises the entire application's authentication system. It handles sensitive operations like token exchange and credential storage.

---

#### 3. **app/services/calendar_services.py** - Calendar Service Layer
**Role:**
- Provides authentication middleware for protected endpoints
- Implements Google Calendar API integration
- Manages credential retrieval and service initialization

**Critical Functions:**
- `authenticate_google_calendar()`: Validates session, retrieves stored credentials
- `GoogleCalendarService.get_upcoming_events()`: Fetches calendar events
- `GoogleCalendarService.create_event()`: Creates new calendar events

**Dependencies:**
- Session data (user_email)
- Database (user_credentials table)
- Google Calendar API

**Why Critical:**
Acts as the authentication middleware for all protected resources. Every calendar operation must pass through `authenticate_google_calendar()`, making it a critical security checkpoint.

---

## 🔍 Code Review Findings

### HIGH Severity - Critical Security Vulnerabilities

#### H1. **Secret Key Misuse for Session Security**
**File:** `app/main.py:25`
**Issue:** Using `GOOGLE_CLIENT_SECRET` as the session middleware secret key
```python
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("GOOGLE_CLIENT_SECRET")
)
```
**Risk:** 
- OAuth client secret should never be used for other purposes
- If session secret is compromised, OAuth credentials are also exposed
- Violates principle of key separation

**Recommendation:** 
Create a separate `SESSION_SECRET_KEY` environment variable with a strong random value:
```python
secret_key=os.getenv("SESSION_SECRET_KEY", secrets.token_urlsafe(32))
```

---

#### H2. **Plaintext Token Storage in Database**
**File:** `router_auth.py:87`, `calendar_services.py:35`
**Issue:** OAuth tokens (including refresh tokens) stored as plain JSON in SQLite
```python
cur.execute("INSERT OR REPLACE INTO user_credentials (user_email, token_json) VALUES (?, ?)", 
            (user_email, creds.to_json()))
```
**Risk:**
- Database breach exposes all user access tokens
- Refresh tokens have long-lived access to user accounts
- No encryption at rest

**Recommendation:**
Implement encryption for token storage using libraries like `cryptography`:
```python
from cryptography.fernet import Fernet
# Encrypt before storage
encrypted_token = cipher.encrypt(creds.to_json().encode())
```

---

#### H3. **SQL Injection Vulnerability Potential**
**File:** `calendar_services.py:29`, `router_auth.py:86-87`
**Issue:** While using parameterized queries (correct), user_email comes from session which could be manipulated
**Current Code:**
```python
user_email = request.session.get("user_email")
cur.execute("SELECT token_json FROM user_credentials WHERE user_email = ?", (user_email,))
```
**Risk:** 
- Session tampering could lead to unauthorized data access
- No validation that email format is correct

**Recommendation:**
Add input validation for email:
```python
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
if not EMAIL_REGEX.match(user_email):
    raise HTTPException(status_code=400, detail="Invalid email format")
```

---

#### H4. **Missing HTTPS Enforcement**
**File:** `router_auth.py:18`
**Issue:** Redirect URI uses `http://` instead of `https://`
```python
REDIRECT_URI = "http://127.0.0.1:8000/api/auth/callback"
```
**Risk:**
- OAuth tokens transmitted over unencrypted connection
- Man-in-the-middle attacks possible
- Violates OAuth 2.0 security best practices

**Recommendation:**
- Use HTTPS in production
- Add configuration for environment-specific redirect URIs
- Implement HTTPS redirect middleware

---

#### H5. **Token Expiry Not Handled**
**File:** `calendar_services.py:35`
**Issue:** No token refresh logic when access token expires
```python
creds = Credentials.from_authorized_user_info(json.loads(token_json))
return creds
```
**Risk:**
- Application breaks when token expires
- User forced to re-authenticate unnecessarily
- Poor user experience

**Recommendation:**
Implement token refresh:
```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Update token in database
```

---

#### H6. **Hardcoded Timezone**
**File:** `calendar_services.py:77, 81`
**Issue:** Timezone hardcoded to 'America/Vancouver'
```python
'timeZone': 'America/Vancouver',
```
**Risk:**
- Incorrect times for users in other timezones
- Data integrity issues
- Poor user experience for global users

**Recommendation:**
Make timezone configurable per user or use UTC:
```python
'timeZone': 'UTC',
```

---

### MEDIUM Severity - Performance and Best Practice Issues

#### M1. **Database Connection Not Managed**
**File:** `database.py`, `router_auth.py:84-89`, `calendar_services.py:27-31`
**Issue:** Creating new SQLite connections for each request
```python
con = sqlite3.connect(DATABASE_FILE)
# ... operations ...
con.close()
```
**Impact:**
- Performance overhead from connection creation
- Risk of connection leaks if exceptions occur before `close()`
- No connection pooling

**Recommendation:**
Use context managers and consider connection pooling:
```python
with sqlite3.connect(DATABASE_FILE) as con:
    cur = con.cursor()
    # operations
    con.commit()
```

---

#### M2. **Missing Request Logging and Audit Trail**
**File:** All router files
**Issue:** No comprehensive logging of authentication events
**Impact:**
- Cannot track authentication failures
- No audit trail for compliance
- Difficult to debug security incidents

**Recommendation:**
Implement structured logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user_email} authenticated successfully")
```

---

#### M3. **Error Messages Leak Information**
**File:** `calendar_services.py:26, 33`
**Issue:** Detailed error messages could help attackers
```python
raise HTTPException(status_code=401, detail="User not authenticated")
raise HTTPException(status_code=403, detail="No credentials found for user")
```
**Impact:**
- Attackers can enumerate valid user states
- Information disclosure

**Recommendation:**
Use generic error messages in production:
```python
raise HTTPException(status_code=401, detail="Authentication required")
```

---

#### M4. **No Rate Limiting**
**File:** All API endpoints
**Issue:** No protection against brute force or DoS attacks
**Impact:**
- Vulnerable to credential stuffing
- API abuse possible
- Google API quota exhaustion

**Recommendation:**
Implement rate limiting:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
@limiter.limit("5/minute")
```

---

#### M5. **Missing Input Validation for Event Data**
**File:** `router_calendar.py:40-56`
**Issue:** No validation of datetime formats or event data
```python
def create_new_event(event_data: EventCreate, request: Request):
    # No validation that dates are valid ISO format
```
**Impact:**
- Application errors with malformed data
- Potential Google API errors
- Poor user experience

**Recommendation:**
Add Pydantic validators:
```python
from pydantic import validator
from datetime import datetime

@validator('start_time', 'end_time')
def validate_datetime(cls, v):
    datetime.fromisoformat(v)
    return v
```

---

#### M6. **No CORS Configuration**
**File:** `main.py`
**Issue:** No CORS middleware configured
**Impact:**
- Cannot call API from different domains
- Limits frontend deployment options

**Recommendation:**
Add CORS middleware:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

---

#### M7. **Database Migration Strategy Missing**
**File:** `database.py`
**Issue:** No migration system for schema changes
**Impact:**
- Difficult to update schema in production
- Data loss risk during updates

**Recommendation:**
Use Alembic for migrations or add version tracking to schema

---

### LOW Severity - Code Style and Readability

#### L1. **Inconsistent Error Handling**
**File:** `calendar_services.py:58-65, 90-97`
**Issue:** Some functions return empty list on error, others return None
```python
# Inconsistent returns
return []  # in get_upcoming_events
return None  # in create_event
```
**Recommendation:** Standardize error handling approach across all service methods

---

#### L2. **Print Statements for Logging**
**File:** Multiple files
**Issue:** Using `print()` instead of proper logging
```python
print("--- /events GET endpoint was hit! ---")
print(f"Google API error: {e}")
```
**Recommendation:** Replace with Python logging module

---

#### L3. **Magic Strings and Numbers**
**File:** `router_calendar.py:27`
**Issue:** Hardcoded values like `max_results=5`
**Recommendation:** Use configuration constants or environment variables

---

#### L4. **Incomplete LLM Service Implementation**
**File:** `llm_service.py`, `llm_router.py`
**Issue:** Files contain only comments, no actual implementation
**Recommendation:** Either implement or remove these files

---

#### L5. **Missing Type Hints**
**File:** `database.py`, `calendar_services.py`
**Issue:** Functions lack type hints
```python
def init_db():  # Should be: def init_db() -> None:
```
**Recommendation:** Add type hints for better IDE support and documentation

---

#### L6. **No API Documentation**
**File:** Router files
**Issue:** Missing detailed docstrings for API endpoints
**Recommendation:** Add comprehensive docstrings with parameter descriptions and response formats

---

#### L7. **Configuration Duplication**
**File:** `router_auth.py:16-20`, `calendar_services.py:16-17`
**Issue:** Constants like `SCOPES` and `DATABASE_FILE` duplicated across files
**Recommendation:** Create centralized configuration module

---

#### L8. **Typo in .gitignore**
**File:** `.gitignore:5`
**Issue:** `fkowpilot.db` instead of `flowpilot.db`
**Recommendation:** Fix typo to prevent database from being committed

---

## ➡️ Prioritized Next Steps (Development Roadmap)

### Priority 1: **Implement Proper Secret Management** [HIGH - Security Critical]
**Timeline:** Immediate (1-2 days)

**Actions:**
1. Create separate `SESSION_SECRET_KEY` environment variable
2. Generate strong random secret key (use `secrets.token_urlsafe(32)`)
3. Update `main.py` to use dedicated session secret
4. Document environment variable requirements in README

**Impact:** Prevents OAuth credential exposure if session secret is compromised

**Files to Modify:**
- `app/main.py`
- Add `.env.example` file

---

### Priority 2: **Encrypt Tokens at Rest** [HIGH - Security Critical]
**Timeline:** 3-5 days

**Actions:**
1. Install `cryptography` package
2. Create encryption/decryption utilities using Fernet symmetric encryption
3. Generate encryption key from environment variable
4. Update `router_auth.py` to encrypt tokens before database storage
5. Update `calendar_services.py` to decrypt tokens when retrieving
6. Implement database migration to encrypt existing tokens

**Impact:** Protects user OAuth tokens from database breaches

**Files to Modify:**
- `requirements.txt`
- Create `app/utils/encryption.py`
- `app/router/router_auth.py`
- `app/services/calendar_services.py`

---

### Priority 3: **Implement Token Refresh Logic** [HIGH - Functionality Critical]
**Timeline:** 2-3 days

**Actions:**
1. Add token expiry check in `authenticate_google_calendar()`
2. Implement automatic token refresh using refresh_token
3. Update stored credentials after refresh
4. Add error handling for expired refresh tokens
5. Add logging for token refresh events

**Impact:** Improves user experience by preventing unexpected authentication failures

**Files to Modify:**
- `app/services/calendar_services.py`
- `database.py` (add updated_at column)

---

### Priority 4: **Add Comprehensive Logging and Monitoring** [MEDIUM - Operations Critical]
**Timeline:** 3-4 days

**Actions:**
1. Set up Python logging configuration
2. Replace all `print()` statements with proper logging
3. Add structured logging for authentication events (login, logout, token refresh)
4. Log security events (failed authentication, state mismatch, invalid tokens)
5. Add request/response logging middleware
6. Configure different log levels for development/production
7. Add log rotation and retention policies

**Impact:** Enables security auditing, debugging, and compliance monitoring

**Files to Modify:**
- Create `app/utils/logging_config.py`
- `app/main.py`
- `app/router/router_auth.py`
- `app/services/calendar_services.py`
- `app/router/router_calendar.py`

---

### Priority 5: **Implement Security Hardening** [MEDIUM-HIGH - Security Enhancement]
**Timeline:** 5-7 days

**Actions:**
1. **Input Validation:**
   - Add email format validation
   - Add datetime format validation for event endpoints
   - Validate event data ranges and constraints

2. **Rate Limiting:**
   - Install `slowapi` package
   - Add rate limiting to authentication endpoints (prevent brute force)
   - Add rate limiting to API endpoints (prevent DoS)

3. **HTTPS Enforcement:**
   - Add configuration for production HTTPS redirect URI
   - Implement HTTPS redirect middleware for production
   - Add security headers middleware (HSTS, X-Frame-Options, etc.)

4. **Database Security:**
   - Implement connection pooling or context managers
   - Add prepared statement validation
   - Enable SQLite encryption (SQLCipher) for production

5. **Error Handling:**
   - Standardize error responses
   - Use generic error messages in production
   - Add custom exception classes

**Impact:** Significantly reduces attack surface and improves overall security posture

**Files to Modify:**
- `requirements.txt`
- `app/main.py`
- `app/router/router_auth.py`
- `app/router/router_calendar.py`
- `app/services/calendar_services.py`
- Create `app/middleware/security.py`
- Create `app/utils/validators.py`

---

## Additional Recommendations

### Short-term (1-2 weeks)
- Add comprehensive unit and integration tests
- Create API documentation with examples
- Implement health check endpoint
- Add environment-specific configuration
- Create proper README with setup instructions

### Medium-term (1-2 months)
- Consider migrating to PostgreSQL for production
- Implement user logout functionality
- Add user profile management endpoints
- Implement proper session timeout and renewal
- Add OpenAPI/Swagger documentation enhancements
- Consider implementing API versioning

### Long-term (3+ months)
- Implement OAuth 2.0 PKCE flow for enhanced security
- Add multi-factor authentication (MFA)
- Implement proper user permission/role system
- Add webhook support for calendar events
- Consider implementing LLM service functionality
- Add monitoring and alerting (Prometheus, Grafana)
- Implement automated security scanning in CI/CD pipeline

---

## Summary

**Overall Security Posture:** ⚠️ **MODERATE RISK**

The application implements the OAuth 2.0 flow correctly at a basic level with proper CSRF protection via state validation. However, several critical security issues need immediate attention:

**Critical Issues (Must Fix Immediately):**
1. Secret key misuse for session management
2. Plaintext token storage in database
3. Missing token refresh logic
4. HTTP instead of HTTPS for OAuth callbacks

**Strengths:**
- ✅ Proper OAuth 2.0 flow implementation
- ✅ CSRF protection with state parameter
- ✅ Session-based authentication
- ✅ Parameterized SQL queries
- ✅ Basic separation of concerns (routes, services, data)

**Weaknesses:**
- ❌ No encryption for sensitive data at rest
- ❌ Inadequate error handling and logging
- ❌ Missing rate limiting and DoS protection
- ❌ No input validation for user data
- ❌ Security configuration issues

**Recommended Priority:** Address Priority 1-3 items within the next 2 weeks to achieve a secure production-ready state.
