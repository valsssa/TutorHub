# Engineer Onboarding Guide

**Last Updated**: 2026-01-29

Welcome to EduStream! This guide will help you get up to speed quickly.

---

## Day 1: Environment Setup

### Prerequisites

- Docker Desktop installed
- Git configured with SSH key
- VS Code or preferred IDE
- Node.js 20+ (for local frontend dev tools)
- Python 3.12+ (for local backend tools)

### Clone and Start

```bash
# Clone the repository
git clone git@github.com:your-org/edustream.git
cd edustream

# Start all services
docker compose up --build -d

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                STATUS
edustream-backend   Up (healthy)
edustream-frontend  Up
edustream-db        Up (healthy)
edustream-redis     Up
edustream-minio     Up
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000/docs | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| PostgreSQL | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | - |

### Create Test Accounts

```bash
# Connect to database
docker compose exec db psql -U postgres -d authapp

# Create test users (or use the seeded data)
```

Test accounts (if seeded):
- Admin: admin@test.com / password123
- Tutor: tutor@test.com / password123
- Student: student@test.com / password123

---

## Day 1-2: Codebase Orientation

### Project Structure

```
edustream/
├── backend/                 # FastAPI backend
│   ├── core/               # Shared utilities
│   ├── models/             # SQLAlchemy ORM models
│   ├── modules/            # Feature modules
│   └── main.py             # App entry point
├── frontend/               # Next.js frontend
│   ├── app/                # Pages (App Router)
│   ├── components/         # React components
│   └── lib/                # Utilities
├── database/               # SQL files
│   ├── init.sql            # Schema
│   └── migrations/         # Migration scripts
├── docs/                   # Documentation
└── docker-compose.yml      # Development setup
```

### Key Files to Read

1. **CLAUDE.md** - Development guidelines and patterns
2. **docs/architecture.md** - System architecture
3. **docs/project_status.md** - Current progress
4. **backend/modules/README.md** - Module patterns

### Architecture Patterns

#### Backend Module Types

**Full DDD** (complex features):
```
modules/bookings/
├── domain/          # Business logic, state machines
├── application/     # Use cases, orchestration
├── infrastructure/  # External integrations
└── presentation/    # API routes
```

**Service + Presentation** (medium complexity):
```
modules/packages/
├── services/        # Business logic
└── presentation/    # API routes
```

**Presentation Only** (simple CRUD):
```
modules/reviews/
└── api.py           # Direct routes
```

#### Frontend Patterns

- **App Router**: All pages in `app/` directory
- **Protected Routes**: Use `ProtectedRoute` HOC
- **API Calls**: Use `lib/api.ts` utilities
- **State Management**: React Context + hooks

---

## Day 2-3: Core Concepts

### User Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **student** | Books and takes sessions | Search tutors, create bookings, message |
| **tutor** | Teaches sessions | Manage availability, accept bookings |
| **admin** | Platform management | User management, tutor approval |
| **owner** | Business analytics | Revenue dashboard, commission settings |

### Booking State Machine

The booking system uses a four-field status:

```python
SessionState: pending_tutor → confirmed → in_progress → completed
SessionOutcome: pending → successful | failed | cancelled | disputed
PaymentState: pending → authorized → captured → released_to_tutor
DisputeState: none | filed → under_review → resolved_*
```

See `backend/modules/bookings/domain/state_machine.py` for transition rules.

### Key Integrations

| Service | Purpose | Config Location |
|---------|---------|-----------------|
| Stripe | Payments | `backend/core/stripe.py` |
| Brevo | Email | `backend/core/email.py` |
| Google | OAuth, Calendar | `backend/core/calendar.py` |
| Zoom | Video meetings | `backend/core/zoom.py` |
| MinIO | File storage | `backend/core/storage.py` |
| Sentry | Error monitoring | `backend/core/sentry.py` |

---

## Day 3-4: Development Workflow

### Running Tests

```bash
# Full test suite (recommended before PR)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Backend tests only
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit

# Single test locally
cd backend
pytest tests/test_favorites.py::test_add_favorite_tutor -v
```

### Linting

```bash
# Check all
./scripts/lint-all.sh

# Fix all
./scripts/lint-all.sh --fix

# Backend only (Ruff, Mypy, Bandit)
./scripts/lint-backend.sh --fix

# Frontend only (ESLint, Prettier, TypeScript)
./scripts/lint-frontend.sh --fix
```

### Database Changes

1. Create migration file in `database/migrations/`
2. Follow naming: `NNN_description.sql`
3. Include both `up` and `down` (commented) SQL
4. Apply:
   ```bash
   docker compose exec db psql -U postgres -d authapp -f /migrations/NNN_description.sql
   ```

### Adding a New API Endpoint

1. **Router** (existing module):
   ```python
   # modules/mymodule/api.py
   @router.get("/my-endpoint")
   async def my_endpoint(current_user: User = Depends(get_current_user)):
       return {"message": "Hello"}
   ```

2. **New Module**:
   ```python
   # modules/newmodule/api.py
   from fastapi import APIRouter

   router = APIRouter(prefix="/new-feature", tags=["new-feature"])

   # main.py
   from modules.newmodule.api import router as new_feature_router
   app.include_router(new_feature_router, prefix=API_V1_PREFIX)
   ```

### Adding a New Frontend Page

```typescript
// app/my-page/page.tsx
import ProtectedRoute from "@/components/ProtectedRoute";

export default function MyPage() {
  return (
    <ProtectedRoute allowedRoles={["student", "tutor"]}>
      <div>My Page Content</div>
    </ProtectedRoute>
  );
}
```

---

## Day 4-5: First Tasks

### Recommended First Contributions

1. **Documentation improvements** - Fix typos, clarify instructions
2. **Test coverage** - Add tests for untested functions
3. **Bug fixes** - Pick a P2 bug from the backlog
4. **Small features** - UI polish, minor enhancements

### How to Pick Up Work

1. Check GitHub Issues for unassigned tasks
2. Look at `docs/TODO_PHASE_0_STABILIZATION.md` for current priorities
3. Ask in team chat if unsure

### PR Process

1. Create feature branch: `git checkout -b feature/description`
2. Make changes with tests
3. Run linting: `./scripts/lint-all.sh --fix`
4. Run tests: `docker compose -f docker-compose.test.yml up --build`
5. Create PR with description
6. Request review
7. Address feedback
8. Merge after approval

---

## Week 2+: Deep Dives

### Booking System

- Read `backend/modules/bookings/` thoroughly
- Understand state transitions
- Study `jobs.py` for background tasks
- Review tests in `tests/test_state_machine.py`

### Payment Flow

- Study `backend/modules/payments/`
- Understand Stripe integration
- Review package and wallet systems
- Test refund scenarios

### Real-time Messaging

- Study `backend/modules/messages/`
- Understand WebSocket implementation
- Review conversation context handling

---

## Resources

### Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | Development guidelines |
| [architecture.md](./architecture.md) | System architecture |
| [project_status.md](./project_status.md) | Current progress |
| [changelog.md](./changelog.md) | Version history |
| [runbooks/](./runbooks/) | Operational procedures |

### External Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js 15 Docs](https://nextjs.org/docs)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [Stripe API Docs](https://stripe.com/docs/api)

### Getting Help

1. Check existing documentation
2. Search codebase for examples
3. Ask in team Slack channel
4. Pair with a teammate

---

## Troubleshooting

### Docker Issues

```bash
# Clean reset
docker compose down -v
docker system prune -af
docker compose up --build -d
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps db

# Connect manually
docker compose exec db psql -U postgres -d authapp
```

### Frontend Build Issues

```bash
# Clear Next.js cache
rm -rf frontend/.next
docker compose up --build frontend
```

### Backend Import Errors

```bash
# Rebuild backend container
docker compose build backend --no-cache
docker compose up -d backend
```

---

## Checklist

### Day 1
- [ ] Clone repository
- [ ] Start Docker services
- [ ] Access frontend at localhost:3000
- [ ] Access API docs at localhost:8000/docs
- [ ] Create test account and log in

### Day 2-3
- [ ] Read CLAUDE.md
- [ ] Read architecture.md
- [ ] Understand module patterns
- [ ] Review booking state machine

### Day 4-5
- [ ] Run test suite successfully
- [ ] Run linting successfully
- [ ] Make a small code change
- [ ] Create first PR

### Week 2
- [ ] Complete first task
- [ ] Review a teammate's PR
- [ ] Deep dive into one module
- [ ] Ask questions in team chat

---

## Questions?

Contact:
- Team Lead: [name]
- Engineering Manager: [name]
- Slack: #edustream-engineering
