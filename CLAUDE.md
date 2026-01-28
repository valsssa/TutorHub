# CLAUDE.md

AI guidance for working with this codebase. For detailed docs see `README.md`, `START_HERE.md`, `LINTING.md`, and `docs/`.

---

## Project Overview

**Stack**: FastAPI (Python 3.12) + Next.js 15 (TypeScript) + PostgreSQL 17

**Key Features**:
- JWT authentication with role-based access (tutor/admin/student)
- Rate limiting, optimized DB indexes, Docker containerization
- Corporate proxy support (Harbor + Nexus at lazarev.cloud)

---

## Repository Structure

```
├── backend/           # FastAPI backend
│   ├── core/         # Shared utilities, security, config
│   ├── modules/      # Feature modules (DDD structure)
│   ├── models/       # SQLAlchemy models
│   ├── tests/        # Backend tests
│   └── main.py       # Application entry point
├── frontend/         # Next.js 15 frontend
│   ├── app/          # Next.js App Router pages
│   ├── components/   # Reusable React components
│   ├── lib/          # Utilities and helpers
│   └── __tests__/    # Frontend tests
├── database/         # DB resources, migrations
├── docs/             # Documentation
├── tests/            # Integration & E2E tests
└── scripts/          # Utility scripts
```

**Key Directories**:
- `backend/core/` - Shared utilities, security, config
- `backend/modules/` - Feature modules (auth, users, bookings, payments)
- `frontend/app/` - Next.js pages using App Router
- `database/migrations/` - SQL migrations (auto-applied on startup)

---

## Git Workflow

### Dual-Push Setup (GitHub + GitLab)
```bash
# Single command pushes to BOTH remotes
git push origin main

# View configuration
git remote -v
```

### Branch Naming
```bash
feature/<description>   # New features
fix/<description>       # Bug fixes
refactor/<component>    # Code refactoring
docs/<update>           # Documentation
test/<description>      # Tests
chore/<task>            # Maintenance
```

### Commit Convention
Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `ci`

Examples:
```bash
feat(auth): add JWT refresh mechanism
fix(booking): resolve timezone error
refactor(api): simplify error handling
```

**Co-authored commits**:
```bash
git commit -m "feat(booking): implement cancellation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Workflow
```bash
# 1. Create branch
git checkout -b feature/new-feature

# 2. Make changes & commit
git add backend/main.py
git commit -m "feat(api): add endpoint"

# 3. Run tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# 4. Push (auto-pushes to GitHub + GitLab)
git push origin feature/new-feature

# 5. Create PR
gh pr create --title "Add feature" --body "Description"
```

---

## Critical Development Rules

### 1. Always Use Docker
**NEVER run services directly**. All development must use Docker:
```bash
# ✅ Correct
docker compose up --build -d

# ❌ Wrong
python main.py
npm run dev
```

### 2. Role System Security
- New registrations always create "student" role
- "admin" and "tutor" roles ONLY assigned via backend/database or admin panel
- Role validation enforced server-side with CHECK constraints
- Protected endpoints use `Depends(get_current_user)` or `Depends(get_current_admin_user)`

### 3. Testing is Mandatory
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 4. Architectural Principles
- **SRP**: Each module performs one defined role
- **Feature-based**: Group by domain (`auth/`, `users/`), not type
- **DDD/Clean Architecture**: Business logic independent of frameworks
- **12-Factor App**: Config via env vars, stateless services
- **SOLID**: Modular, extensible, testable components

### 5. Performance
- Prefer async functions and async DB drivers
- Always paginate list responses
- Use `selectinload`/`joinedload` for relationships
- Enable GZipMiddleware

### 6. Code Quality
- 100% type-hint coverage
- Max file length ≈ 300 lines
- Logging via centralized config (no `print()`)
- Format/lint with `ruff` (pre-commit enforced)
- Naming: `snake_case` (variables), `PascalCase` (classes), `kebab-case` (branches)

**Linting**: See `LINTING.md` for comprehensive guide
```bash
./scripts/lint-all.sh [--fix]
./scripts/lint-backend.sh [--fix]
./scripts/lint-frontend.sh [--fix]
```

---

## Essential Commands

### Development
```bash
# Start services
docker compose up --build -d

# View logs
docker compose logs -f backend

# Restart after changes
docker compose up -d --build backend

# Clean reset
docker compose down -v
```

### Testing
```bash
# Full test suite
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Individual suites
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up e2e-tests --abort-on-container-exit
```

### Database
```bash
# Access DB shell
docker compose exec db psql -U postgres -d authapp

# View users
docker compose exec db psql -U postgres -d authapp -c "SELECT id, email, role FROM users;"

# Backup
docker compose exec -T db pg_dump -U postgres authapp > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose exec -T db psql -U postgres -d authapp
```

### Git
```bash
git status
git checkout -b feature/new-feature
git add backend/main.py
git commit -m "feat(api): add endpoint"
git push origin feature/new-feature
gh pr create --title "Title" --body "Description"
```

---

## Architecture Patterns

### Backend (FastAPI)

**Protected Endpoints**:
```python
@app.get("/api/protected")
async def protected(current_user: User = Depends(get_current_user)):
    return {"user": current_user.email}
```

**Rate Limiting**:
```python
@app.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate):
    # ...
```

**Email Normalization**:
```python
normalized_email = user.email.lower().strip()
```

### Frontend (Next.js 15)

**Auth Check Pattern**:
```typescript
const token = Cookies.get('token')
if (!token) router.replace('/login')

const response = await axios.get(`${API_URL}/users/me`, {
  headers: { Authorization: `Bearer ${token}` }
})
```

**Toast Notifications**:
```typescript
const { showSuccess, showError } = useToast()
```

### Database

**Schema**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    CONSTRAINT valid_role CHECK (role IN ('tutor', 'admin', 'student'))
);
```

**Timestamps**: All `updated_at` set in application code (no DB triggers)
```python
user.updated_at = datetime.now(timezone.utc)
```

See `docs/architecture/DATABASE_ARCHITECTURE.md` for details.

---

## Security Guidelines

### Validation
1. **Pydantic schemas** - First line of defense
2. **Database constraints** - Enforce at DB level
3. **Rate limiting** - Per endpoint (5/min registration, 10/min login)

### 🚫 Never
- Store plaintext passwords
- Skip rate limiting on auth endpoints
- Trust client-side role validation
- Expose internal error messages
- Commit secrets to version control
- Log sensitive PII

### ✅ Always
- Hash passwords with bcrypt (≥12 rounds)
- Validate roles server-side only
- Normalize and sanitize inputs
- Use parameterized ORM queries
- Rotate JWTs on logout/password change
- Secure CORS (whitelist origins)

> **Security Principle**: "Assume compromise. Design so a single leak cannot escalate."

---

## Default Credentials

| Role    | Email               | Password    |
|---------|---------------------|-------------|
| Admin   | admin@example.com   | admin123    |
| Tutor   | tutor@example.com   | tutor123    |
| Student | student@example.com | student123  |

**Change in production via environment variables.**

---

## Common Pitfalls

### DON'T
- Run services directly (`python main.py`, `npm run dev`)
- Commit without tests
- Push to `main` directly
- Use `git add .` without reviewing
- Skip type hints or use `any` type
- Write raw SQL queries
- Trust client-side validation
- Skip writing tests

### DO
- Always use Docker
- Run tests before pushing
- Create feature branches
- Review changes (`git diff --cached`)
- Provide 100% type coverage
- Use ORM queries (SQLAlchemy)
- Validate server-side
- Test error cases and edge cases

---

## Quick Reference

### Development Workflow
```bash
# Start
docker compose up -d --build

# Test
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Commit
git checkout -b feature/new-feature
git add backend/main.py
git commit -m "feat(api): add endpoint"
git push origin feature/new-feature
gh pr create --title "Add feature" --body "Description"
```

### Emergency Commands
```bash
# Port in use
docker compose down
lsof -ti:8000 | xargs kill -9

# DB connection failed
docker compose down -v
docker compose up -d --build

# Complete reset
docker compose down -v
docker system prune -af --volumes
docker compose up -d --build
```

### Environment Variables
**Backend** (`.env`):
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/authapp
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEFAULT_ADMIN_EMAIL=admin@example.com
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Documentation

- `README.md` - Project overview and quick start
- `START_HERE.md` - First-time contributor guide
- `LINTING.md` - Comprehensive linting guide
- `AGENTS.md` - Agent-specific rules
- `docs/architecture/` - Architecture docs
- `docs/guides/` - How-to guides
- `database/migrations/README.md` - Migration system

---

## Core Principle

> **"Store Agreements, Not Just Data"**
> Every record should capture a user decision at a point in time—not just current state.

This solves 80% of marketplace pitfalls before they happen.
