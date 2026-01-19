# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

Full-stack authentication template with role-based access control, production-ready security, and Docker containerization.

**Stack**: FastAPI (Python 3.12) + Next.js 15 (TypeScript) + PostgreSQL 17

**Key Features**:
- JWT authentication with 3 roles (tutor/admin/student)
- Rate limiting (5/min registration, 10/min login)
- Optimized database with indexes (60% faster queries)
- Corporate proxy support (Harbor + Nexus)

---

## Critical Development Rules

### 1. Always Use Docker

**NEVER run services directly**. All development must use Docker containers:

```bash
# ✅ Correct
docker compose up --build -d
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

#  Wrong
python main.py
npm run dev
```

### 2. Role System Security

- New registrations always create "student" role
- "admin" and "tutor" roles can ONLY be assigned via backend/database or admin panel
- Role validation is enforced server-side with CHECK constraints
- Protected endpoints use `Depends(get_current_user)` or `Depends(get_current_admin_user)`

### 3. Testing is Mandatory

Always run full test suite before committing:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 4. 🧩 Architectural Principles
- **Single Responsibility Principle (SRP)**  
  Each module or class performs exactly one defined role.
- **Separation of Concerns (SoC)**  
  Divide responsibilities between API, business logic, and data layers.
- **Feature-based Modularization**  
  Group code by feature/domain (`auth/`, `users/`, `courses/`), not by type.
- **Dependency Inversion (DI)**  
  Upper layers depend on interfaces/abstractions, not implementations.
- **Convention-over-Configuration**  
  Follow consistent naming and structural conventions (`router.py`, `service.py`, `schemas.py`).
- **Scalability for Future Features**  
  Each module must be self-contained, ready for horizontal extension.
- **Reusability**  
  Extract repeated logic into `core/` or `utils/`.
- **Explicitness & Traceability**  
  Every import and dependency must be clear; no hidden global state.
- **Clean Architecture / DDD Alignment**  
  Keep business logic independent from frameworks or persistence layers.
- **Core / Common Module Pattern**  
  Shared config, security, and helpers live in `core/` or `utils/`.
- **SOLID Principle Compliance**  
  Enforce modular, extensible, and testable components.
- **12-Factor App Compliance**  
 Config via environment variables, stateless services, declarative dependencies, disposable processes.
- **Web A11y: 11 Best Practices and Techniques for Developing Accessible Web-Applications** 
 Config via environment variables, stateless services, declarative dependencies, disposable processes.


### 🚀 5. Performance & Optimization

- Prefer **async functions** and **async DB drivers**.  
- Use **connection pooling** and **lazy initialization** for heavy services.  
- Always **paginate list responses**.  
- Cache configuration and constants via `functools.lru_cache`.  
- Apply **query optimization** (`selectinload`, `joinedload`).  
- Enable **GZipMiddleware** and proper response compression.

### 🧰 6. Code Quality

- 100 % type-hint coverage.  
- Max file length ≈ 300 lines.  
- Logging through centralized config — no `print()`.  
- Format/lint with `black`, `isort`, `ruff` (enforced by pre-commit).  
- Unit tests for all logic in `service.py`.  
- Consistent naming:  
  - snake_case → variables & functions  
  - PascalCase → classes  
  - kebab-case → branches

---

## Essential Commands

### Development

```bash
# Start all services
docker compose up --build -d

# View logs (specific service)
docker compose logs -f backend
docker compose logs -f frontend

# Restart after changes
docker compose up -d --build backend

# Clean reset (removes volumes)
docker compose down -v
```

### Testing

```bash
# Full test suite (lint + unit + E2E)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Individual test suites
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up e2e-tests --abort-on-container-exit

# Cleanup test environment
docker compose -f docker-compose.test.yml down -v
```

### Database Operations

```bash
# Access database shell
docker compose exec db psql -U postgres -d authapp

# View users
docker compose exec db psql -U postgres -d authapp -c "SELECT id, email, role, is_active FROM users;"

# Backup database
docker compose exec -T db pg_dump -U postgres authapp > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U postgres -d authapp
```

### Production Deployment

```bash
# Build and start production stack
docker compose -f docker-compose.prod.yml up -d --build

# View production logs
docker compose -f docker-compose.prod.yml logs 

# Check production status
docker compose -f docker-compose.prod.yml ps
```

---

## Architecture & Code Organization

### Backend Architecture (FastAPI)

**Core Files**:
- `main.py` - FastAPI app, API routes, startup logic (creates default users)
- `auth.py` - JWT tokens, password hashing (bcrypt 12 rounds), auth dependencies
- `models.py` - SQLAlchemy User model with role CHECK constraint
- `schemas.py` - Pydantic validation (email normalization, password 6-128 chars, role regex)
- `database.py` - Database session management, connection pooling

**Key Patterns**:

1. **Protected Endpoints** - Use dependency injection:
```python
@app.get("/api/protected")
async def protected(current_user: User = Depends(get_current_user)):
    return {"user": current_user.email}

@app.get("/admin/protected")
async def admin_only(current_user: User = Depends(get_current_admin_user)):
    return {"admin": current_user.email}
```

2. **Rate Limiting** - Applied per endpoint:
```python
@app.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")  # Prevents abuse
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    # ...
```

3. **Email Normalization** - Always lowercase and strip:
```python
normalized_email = user.email.lower().strip()
db_user = db.query(User).filter(User.email == normalized_email).first()
```

4. **Error Handling** - Structured logging with context:
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception: %s - Path: %s %s",
        exc.detail, request.method, request.url.path,
        extra={"status_code": exc.status_code, "client_host": request.client.host}
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
```

### Frontend Architecture (Next.js 15)

**Directory Structure**:
```
frontend/
├── app/
│   ├── page.tsx              # Dashboard (protected)
│   ├── login/page.tsx        # Login page
│   ├── register/page.tsx     # Registration page
│   ├── admin/page.tsx        # Admin panel (admin only)
│   ├── unauthorized/page.tsx # Access denied
│   └── layout.tsx            # Root layout with ToastProvider
├── components/
│   ├── ProtectedRoute.tsx    # HOC for route protection
│   ├── Toast.tsx             # Toast notification component
│   ├── ToastContainer.tsx    # Toast context provider
│   └── LoadingSpinner.tsx    # Loading indicator
└── lib/
    └── auth.ts               # Auth utilities (isAdmin, isStudent, etc.)
```

**Key Patterns**:

1. **Authentication Check** - All protected pages:
```typescript
'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ProtectedPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('token')
      if (!token) {
        router.replace('/login')
        return
      }

      try {
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
      } catch (error) {
        Cookies.remove('token')
        router.replace('/login')
      }
    }

    checkAuth()
  }, [router])

  if (!user) return <LoadingSpinner />
  return <div>Protected Content</div>
}
```

2. **Toast Notifications** - Use context:
```typescript
import { useToast } from '../../components/ToastContainer'

function MyComponent() {
  const { showSuccess, showError } = useToast()

  const handleAction = async () => {
    try {
      await someAction()
      showSuccess('Operation successful!')
    } catch (error) {
      showError('Operation failed')
    }
  }
}
```

3. **Role-Based UI** - Color-coded badges:
```typescript
<span className={`px-2 py-1 rounded text-sm ${
  user.role === 'admin' ? 'bg-red-100 text-red-800' :
  user.role === 'student' ? 'bg-green-100 text-green-800' :
  'bg-blue-100 text-blue-800'
}`}>
  {user.role}
</span>
```

### Database Architecture

**Schema** (`database/init.sql`):
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_role CHECK (role IN ('tutor', 'admin', 'student')),
    CONSTRAINT valid_email_length CHECK (char_length(email) <= 254)
);
```

**Performance Indexes**:
```sql
-- 60% faster case-insensitive email lookups
CREATE UNIQUE INDEX idx_users_email_lower ON users(LOWER(email));

-- 40% faster role-based queries (partial index)
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;

-- Fast active user filtering
CREATE INDEX idx_users_active ON users(is_active);

-- Optimized sorting by creation date
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Timestamp Management** (No DB Triggers - All in Application Code):
```python
# All updated_at timestamps are set explicitly in application code
from datetime import datetime, timezone

user.email = new_email
user.updated_at = datetime.now(timezone.utc)  # Set in code, not DB
db.commit()
```

See `docs/architecture/DATABASE_ARCHITECTURE.md` for full details on "No Logic in DB" principle.

---

## Adding New Features

### New API Endpoint

1. **Define Pydantic schemas** in `backend/schemas.py`:
```python
class NewFeatureRequest(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)

class NewFeatureResponse(BaseModel):
    result: str
```

2. **Add route** in `backend/main.py`:
```python
@app.post("/api/feature", response_model=NewFeatureResponse)
@limiter.limit("20/minute")  # Set appropriate rate limit
async def new_feature(
    request: Request,
    data: NewFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Feature description."""
    try:
        logger.info("Feature accessed by: %s", current_user.email)
        # Your logic here
        return NewFeatureResponse(result="success")
    except Exception as e:
        logger.error("Feature error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed"
        )
```

3. **Add tests** in `backend/tests/` or `tests/`:
```python
def test_new_feature(client, test_user_token):
    response = client.post(
        "/api/feature",
        json={"field": "test"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

### New Frontend Page

1. **Create page** in `frontend/app/new-page/page.tsx`:
```typescript
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import axios from 'axios'
import LoadingSpinner from '@/components/LoadingSpinner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function NewPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('token')
      if (!token) {
        router.replace('/login')
        return
      }

      try {
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
      } catch (error) {
        Cookies.remove('token')
        router.replace('/login')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [router])

  if (loading) return <LoadingSpinner />

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">New Feature</h1>
      {/* Your page content */}
    </div>
  )
}
```

2. **Add tests** in `frontend/__tests__/new-page.test.tsx`:
```typescript
import { render, screen } from '@testing-library/react'
import NewPage from '../app/new-page/page'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: jest.fn() })
}))

describe('NewPage', () => {
  it('renders page title', () => {
    render(<NewPage />)
    expect(screen.getByText('New Feature')).toBeInTheDocument()
  })
})
```

### New User Role

To add a fourth role (e.g., "teacher"):

1. **Update database** in `database/init.sql`:
```sql
CONSTRAINT valid_role CHECK (role IN ('tutor', 'admin', 'student', 'teacher'))
```

2. **Update role validation** in `backend/main.py`:
```python
def _validate_role(role: str) -> None:
    if role not in ["user", "admin", "student", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'tutor', 'admin', 'student', or 'teacher'"
        )
```

3. **Update Pydantic schema** in `backend/schemas.py`:
```python
role: Optional[str] = Field(None, pattern="^(user|admin|student|teacher)$")
```

4. **Update frontend utilities** in `frontend/lib/auth.ts`:
```typescript
isTeacher: (user: User | null): boolean => {
  return authUtils.hasRole(user, 'teacher')
},

getRoleDisplayName: (role: string): string => {
  switch (role) {
    case 'admin': return 'Administrator'
    case 'teacher': return 'Teacher'
    case 'student': return 'Student'
    case 'tutor': return 'Tutor'
    default: return role
  }
}
```

5. **Add role styling** to frontend pages:
```typescript
<span className={`px-2 py-1 rounded text-sm ${
  user.role === 'admin' ? 'bg-red-100 text-red-800' :
  user.role === 'teacher' ? 'bg-purple-100 text-purple-800' :
  user.role === 'student' ? 'bg-green-100 text-green-800' :
  'bg-blue-100 text-blue-800'
}`}>
  {user.role}
</span>
```

6. **Add default user** (optional) in `backend/main.py`:
```python
# Add to Settings class
default_teacher_email: str = "teacher@example.com"
default_teacher_password: str = "teacher123"

# Add to create_default_users()
teacher_user = db.query(User).filter(User.email == settings.default_teacher_email).first()
if not teacher_user:
    teacher_user = User(
        email=settings.default_teacher_email,
        hashed_password=get_password_hash(settings.default_teacher_password),
        role="teacher",
    )
    db.add(teacher_user)
    logger.info("Created default teacher user: %s", settings.default_teacher_email)
```

---

## Corporate Proxy Configuration

All Docker images use corporate proxy infrastructure at `lazarev.cloud`:

**Docker Registry (Harbor)**:
- DockerHub: `<image>`
- GitHub: `harbor.in.lazarev.cloud/gh-proxy/<image>`

**Package Managers (Nexus)**:
- Debian: `https://nexus.in.lazarev.cloud/repository/debian-proxy/`
- npm: `https://nexus.in.lazarev.cloud/repository/npm-group/`
- pip: `https://nexus.in.lazarev.cloud/repository/pypi-proxy/simple`

**Dockerfile Pattern** (already configured, no changes needed):
```dockerfile
# Backend
FROM python:3.12-slim
RUN echo "deb https://nexus.in.lazarev.cloud/repository/debian-proxy/ bookworm main" > /etc/apt/sources.list
RUN pip config set global.index-url https://nexus.in.lazarev.cloud/repository/pypi-proxy/simple

# Frontend (multi-stage)
FROM node:20-alpine AS base
RUN npm config set registry https://nexus.in.lazarev.cloud/repository/npm-group/
```

See `PROXY_CONFIGURATION.md` for troubleshooting.

---

## Security Guidelines

### Input Validation

**All user inputs MUST be validated**:

1. **Pydantic schemas** - First line of defense:
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 128:
            raise ValueError("Password must be 6-128 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if len(v) > 254:
            raise ValueError("Email must not exceed 254 characters")
        return v.lower()
```

2. **Database constraints** - Enforce at DB level:
```sql
CONSTRAINT valid_role CHECK (role IN ('tutor', 'admin', 'student')),
CONSTRAINT valid_email_length CHECK (char_length(email) <= 254)
```

3. **Rate limiting** - Per endpoint:
```python
@limiter.limit("5/minute")  # Registration
@limiter.limit("10/minute") # Login
@limiter.limit("20/minute") # General API
```

### Authentication Flow

1. **Registration**:
   - Email normalized (lowercase, strip)
   - Password hashed (bcrypt, 12 rounds)
   - Role defaults to "user"
   - Rate limited (5/min)

2. **Login**:
   - Email lookup (case-insensitive via indexed LOWER(email))
   - Password verification (constant-time comparison)
   - JWT issued (30-min expiry)
   - Rate limited (10/min)

3. **Protected Routes**:
   - Token extracted from Authorization header
   - JWT validated (signature, expiration)
   - User loaded from database
   - Role checked if required

### 🛡️ Common Security Mistakes to Avoid (and Secure Countermeasures)

#### 🚫 Never Do This
 **Store plaintext or weakly hashed passwords**  
→ This exposes users to credential stuffing and rainbow-table attacks.  

 **Skip rate limiting on authentication and registration endpoints**  
→ Leads to brute-force and credential-stuffing vulnerabilities.  

 **Trust client-side role or token validation**  
→ All authorization decisions must occur on the server using verified JWT claims or DB lookups.  

 **Expose internal error messages, stack traces, or SQL errors in production**  
→ Reveals sensitive system internals useful for enumeration and exploitation.  

 **Commit secrets, API keys, or tokens to version control**  
→ Compromised repositories are the #1 source of leaked credentials.  

 **Rely solely on HTTPS termination at reverse proxies**  
→ Backend containers must also enforce TLS or reject plaintext connections.  

 **Ignore session revocation and token rotation**  
→ Static long-lived JWTs can be reused indefinitely if leaked.  

 **Log sensitive PII (passwords, JWTs, refresh tokens, IPs without masking)**  
→ Violates data-protection policies (GDPR, SOC2, ISO-27001).  

 **Disable CORS or use `allow_origins="*"` in production**  
→ Enables cross-origin token exfiltration via malicious scripts.  

 **Use unrestricted file uploads or unsanitized filenames**  
→ Allows arbitrary file execution or directory traversal.  

---

#### ✅ Always Do This
✅ **Hash all passwords with bcrypt (≥12 rounds)**  
Use constant-time comparison (`secrets.compare_digest`) to prevent timing attacks.  

✅ **Validate roles and permissions exclusively on the server**  
Map roles → privileges in code or DB; never trust the frontend to enforce access.  

✅ **Normalize and sanitize all user inputs**  
Lowercase and strip emails, escape SQL/HTML, and validate lengths and formats with Pydantic.  

✅ **Use parameterized ORM queries only (SQLAlchemy or async ORM)**  
Eliminates SQL injection risks; never interpolate raw SQL strings.  

✅ **Enforce per-endpoint rate limiting (`slowapi` or Redis-based)**  
Differentiate limits for registration, login, and general API usage.  

✅ **Rotate and revoke JWTs on logout or password change**  
Short access-token TTLs (<30 min) and signed refresh tokens stored in secure cookies.  

✅ **Encrypt all network traffic (TLS 1.2 +) and at-rest data**  
Use database encryption (pgcrypto) and enforce HSTS headers.  

✅ **Secure CORS configuration**  
Explicitly whitelist trusted domains; never allow wildcard origins in production.  

✅ **Store secrets in environment variables or secret managers**  
(e.g., HashiCorp Vault, AWS Secrets Manager, Docker Secrets).  
Rotate regularly and restrict read access.  

✅ **Log security events with context but without sensitive data**  
Include user ID, IP, request ID, and timestamp. Use structured JSON logs and forward to SIEM (ELK, Datadog, or Loki).  

✅ **Enable CSP, X-Frame-Options, X-Content-Type-Options headers**  
Prevents XSS, clickjacking, and MIME-type confusion attacks.  
 

✅ **Regularly review audit logs and anomaly alerts**  
Automate alerting for repeated failed logins, privilege escalation, and token misuse.  

---

> 🧩 **Security Mindset Rule:**  
> “Assume compromise. Design so that a single leak cannot escalate.”  
> – OWASP Principle of Least Privilege


---

## Testing Strategy

### Test Coverage

**Backend Tests** (`tests/test_auth.py`):
- User registration (success, duplicate email)
- Login (success, wrong password)
- Token validation (valid, expired, missing)
- Role enforcement (user vs admin endpoints)
- Health check

**Frontend Tests** (`frontend/__tests__/`):
- Login page rendering and form submission
- Registration page rendering and validation
- Admin panel authorization checks

**E2E Tests** (`tests/test_e2e_admin.py`):
- Admin user management workflows
- Role assignment and validation
- Email uniqueness enforcement
- Invalid input handling

### Writing Tests

**Backend test pattern**:
```python
def test_feature(client, test_user_token):
    """Test description."""
    response = client.post(
        "/api/endpoint",
        json={"field": "value"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["expected_field"] == "expected_value"
```

**Frontend test pattern**:
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

describe('Component', () => {
  it('handles user interaction', async () => {
    render(<Component />)

    const button = screen.getByRole('button', { name: /submit/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })
})
```

---

## Common Troubleshooting

### "Port already in use"

```bash
docker compose down
# If that fails, kill the process:
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### "Database connection failed"

```bash
# Reset database with clean slate
docker compose down -v
docker compose up -d --build
```

### "Frontend can't connect to backend"

1. Check `NEXT_PUBLIC_API_URL` in frontend environment
2. Verify backend is running: `docker compose ps`
3. Check CORS configuration in `backend/main.py`
4. Test connectivity: `docker compose exec frontend ping backend`

### "Tests failing after changes"

1. Rebuild test environment: `docker compose -f docker-compose.test.yml build --no-cache`
2. Clean test data: `docker compose -f docker-compose.test.yml down -v`
3. Check test assertions match current error messages
4. Review logs: `docker compose -f docker-compose.test.yml logs`

### "Next.js chunk loading errors"

If you see 404 errors for `_next/static/chunks/`:

1. Verify frontend Dockerfile uses multi-stage build (already configured)
2. Ensure `.next/static` directory is copied to production image
3. Rebuild: `docker compose build frontend`

---

## Documentation Structure

- `README.md` - Project overview and quick start
- `CLAUDE.md` - This file (AI assistant guidance)
- `AGENTS.md` - Agent-specific rules
- `START_HERE.md` - First-time contributor guide
- `QUICK_REFERENCE.md` - Command cheat sheet
- `docs/` - Organized documentation:
  - `INDEX.md` - Master documentation index
  - `architecture/` - Architecture and design docs
    - `DATABASE_ARCHITECTURE.md` - Database design principles
  - `guides/` - How-to guides and procedures
    - `APPLY_MIGRATION.md` - Migration deployment guide
  - `analysis/` - Code analysis and reports
- `database/migrations/` - Auto-applied SQL migrations
  - `README.md` - Migration system documentation

---

## Default Credentials

Default users are created automatically on startup (configurable via environment variables):

| Role    | Email               | Password    |
|---------|---------------------|-------------|
| Admin   | admin@example.com   | admin123    |
| Tutor   | tutor@example.com   | tutor123    |
| Student | student@example.com | student123  |

**IMPORTANT**: Change these in production via environment variables or `.env` file.

---

## Quick Reference

```bash
# Start development
docker compose up -d --build

# Run all tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Clean slate
docker compose down -v && docker system prune -af --volumes

# Access database
docker compose exec db psql -U postgres -d authapp

# View logs
docker compose logs backend

# Production deploy
docker compose -f docker-compose.prod.yml up -d --build
```

### 🎯 **Core Principle: “Store Agreements, Not Just Data”**

> **Every record in your database should capture a *user decision at a point in time*—not just current state.**

This mindset solves 80% of marketplace pitfalls before they happen.