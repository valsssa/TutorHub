# CLAUDE.md

AI guidance for working with this codebase. For detailed docs see `README.md`, `START_HERE.md`, `LINTING.md`, and `docs/`.

---

## Project Overview

**Stack**: FastAPI (Python 3.12) + Next.js 15 (TypeScript) + PostgreSQL 17

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
- **Role Hierarchy**: Owner (level 3) → Admin (level 2) → Tutor (level 1) → Student (level 0)
- New registrations always create "student" role
- "owner", "admin", and "tutor" roles ONLY assigned via backend/database or admin panel
- **Owner role**: Highest privilege level with access to financial data and business intelligence
- Role validation enforced server-side with CHECK constraints
- Protected endpoints use `Depends(get_current_user)`, `Depends(get_current_admin_user)`, or `Depends(get_current_owner_user)`
- Owner role CANNOT be assigned via public registration (security by design)

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
---

## Architecture Patterns


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
| Owner   | owner@example.com   | owner123    |
| Admin   | admin@example.com   | admin123    |
| Tutor   | tutor@example.com   | tutor123    |
| Student | student@example.com | student123  |

**Change in production via environment variables:**
- `DEFAULT_OWNER_PASSWORD`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_TUTOR_PASSWORD`
- `DEFAULT_STUDENT_PASSWORD`

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
`.env` - all
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

## Feature Implementation System Guidelines

### Feature Implementation Priority Rules
- IMMEDIATE EXECUTION: Launch parallel Tasks immediately upon feature requests.
- NO CLARIFICATION: Skip asking what type of implementation unless absolutely critical.
- PARALLEL BY DEFAULT: Always use 7-parallel-Task method for efficiency.

### Parallel Feature Implementation Workflow
1. **Component:** Create main component file.
2. **Styles:** Create component styles/CSS.
3. **Tests:** Create test files.
4. **Types:** Create type definitions.
5. **Hooks:** Create custom hooks/utilities.
6. **Integration:** Update routing, imports, exports.
7. **Remaining:** Update package.json, documentation, configuration files.
8. **Review and Validation:** Coordinate integration, run tests, verify build, check for conflicts.

### Context Optimization Rules
- Strip out all comments when reading code files for analysis.
- Each task handles ONLY specified files or file types.
- Task 7 combines small config/doc updates to prevent over-splitting.

### Feature Implementation Guidelines
- **CRITICAL:** Make MINIMAL CHANGES to existing patterns and structures.
- **CRITICAL:** Preserve existing naming conventions and file organization.
- Follow project's established architecture and component patterns.
- Use existing utility functions and avoid duplicating functionality.