# Action Plan - Codebase Issues Resolution

**Date**: January 24, 2026  
**Status**: In Progress  
**Last Updated**: January 24, 2026  

---

## Overview

This action plan provides a step-by-step approach to resolving all identified issues in the codebase. Issues are organized by priority and grouped for efficient resolution.

---

## Phase 1: Critical Fixes (Day 1 - IMMEDIATE)

**Goal**: Resolve all critical security vulnerabilities and blocking issues.

### Task 1.1: Fix Syntax Error
**File**: `backend/models/tutors.py:59`  
**Time Estimate**: 5 minutes

```python
# Line 59 - Add the complete definition
version = Column(Integer, nullable=False, default=1, server_default="1")
```

**Test**:
```bash
docker compose up --build backend
# Verify backend starts without errors
```

---

### Task 1.2: Remove Hardcoded Passwords
**Files**: 
- `backend/main.py`
- `backend/core/config.py`

**Time Estimate**: 30 minutes

**Step 1**: Update `backend/core/config.py`:
```python
# Remove these lines:
default_admin_password: str = "admin123"
default_tutor_password: str = "tutor123"
default_student_password: str = "student123"

# Replace with:
default_admin_password: str = Field(..., env="ADMIN_DEFAULT_PASSWORD")
default_tutor_password: str = Field(..., env="TUTOR_DEFAULT_PASSWORD")
default_student_password: str = Field(..., env="STUDENT_DEFAULT_PASSWORD")
```

**Step 2**: Update `.env` files:
```bash
# .env.localhost
ADMIN_DEFAULT_PASSWORD=your_secure_admin_password
TUTOR_DEFAULT_PASSWORD=your_secure_tutor_password
STUDENT_DEFAULT_PASSWORD=your_secure_student_password

# .env.domain
ADMIN_DEFAULT_PASSWORD=${ADMIN_DEFAULT_PASSWORD}
TUTOR_DEFAULT_PASSWORD=${TUTOR_DEFAULT_PASSWORD}
STUDENT_DEFAULT_PASSWORD=${STUDENT_DEFAULT_PASSWORD}
```

**Step 3**: Update `docker-compose.yml`:
```yaml
backend:
  environment:
    - ADMIN_DEFAULT_PASSWORD=${ADMIN_DEFAULT_PASSWORD}
    - TUTOR_DEFAULT_PASSWORD=${TUTOR_DEFAULT_PASSWORD}
    - STUDENT_DEFAULT_PASSWORD=${STUDENT_DEFAULT_PASSWORD}
```

**Test**:
```bash
# Verify environment variables are required
docker compose up backend
# Should fail if variables are missing

# Set variables and verify startup
export ADMIN_DEFAULT_PASSWORD=SecurePass123!
export TUTOR_DEFAULT_PASSWORD=SecurePass123!
export STUDENT_DEFAULT_PASSWORD=SecurePass123!
docker compose up --build backend
```

---

### Task 1.3: Fix Secret Key Generation
**File**: `backend/core/config.py`  
**Time Estimate**: 15 minutes

**Current Code**:
```python
if DEBUG:
    SECRET_KEY = secrets.token_urlsafe(32)
```

**Fix**:
```python
# Remove conditional generation
SECRET_KEY: str = Field(..., env="SECRET_KEY")

# Add validation
@field_validator('SECRET_KEY')
@classmethod
def validate_secret_key(cls, v: str) -> str:
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

**Update `.env` files**:
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env.localhost
SECRET_KEY=<generated_key>
```

**Test**:
```bash
# Verify secret key is required and validated
docker compose up --build backend
```

---

### Task 1.4: Remove Default MinIO Credentials
**Files**: 
- `backend/core/config.py`
- `backend/core/storage.py`

**Time Estimate**: 20 minutes

**Fix**:
```python
# backend/core/config.py
MINIO_ACCESS_KEY: str = Field(..., env="MINIO_ACCESS_KEY")
MINIO_SECRET_KEY: str = Field(..., env="MINIO_SECRET_KEY")
```

**Update `docker-compose.yml`**:
```yaml
minio:
  environment:
    - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
    - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}

backend:
  environment:
    - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
    - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
```

**Test**:
```bash
docker compose up --build minio backend
# Verify MinIO authentication works
```

---

### Task 1.5: Remove Environment Variable Defaults in Docker Compose
**Files**: 
- `docker-compose.yml`
- `docker-compose.prod.yml`

**Time Estimate**: 30 minutes

**Fix**: Remove all default values:
```yaml
# Before:
- SECRET_KEY=default_secret_key

# After:
- SECRET_KEY=${SECRET_KEY}  # No default
```

**Create `.env.example`**:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=authapp

# Backend
SECRET_KEY=
ADMIN_DEFAULT_PASSWORD=
TUTOR_DEFAULT_PASSWORD=
STUDENT_DEFAULT_PASSWORD=

# MinIO
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_ENDPOINT=minio:9000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Test**:
```bash
# Should fail without .env file
docker compose up

# Copy and fill .env.example
cp .env.example .env
# Edit .env with secure values
docker compose up --build
```

---

### Task 1.6: Add Environment Validation
**File**: `backend/main.py`  
**Time Estimate**: 20 minutes

**Add startup validation**:
```python
@app.on_event("startup")
async def validate_environment():
    """Validate all required environment variables are set."""
    required_vars = {
        "DATABASE_URL": "Database connection string",
        "SECRET_KEY": "JWT secret key (min 32 chars)",
        "ADMIN_DEFAULT_PASSWORD": "Admin user password",
        "TUTOR_DEFAULT_PASSWORD": "Tutor user password",
        "STUDENT_DEFAULT_PASSWORD": "Student user password",
        "MINIO_ACCESS_KEY": "MinIO access key",
        "MINIO_SECRET_KEY": "MinIO secret key",
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({description})")
        elif var == "SECRET_KEY" and len(value) < 32:
            missing.append(f"{var} (must be at least 32 characters)")
    
    if missing:
        error_msg = "Missing or invalid environment variables:\n" + "\n".join(f"  - {m}" for m in missing)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Environment validation passed")
```

**Test**:
```bash
# Test with missing variables
unset SECRET_KEY
docker compose up backend
# Should fail with clear error message

# Test with valid variables
export SECRET_KEY=<32-char-key>
docker compose up backend
# Should start successfully
```

---

### Phase 1 Completion Checklist

- [ ] Syntax error fixed in `backend/models/tutors.py`
- [ ] All hardcoded passwords removed
- [ ] Secret key generation fixed
- [ ] MinIO credentials moved to environment variables
- [ ] Docker Compose defaults removed
- [ ] Environment validation added
- [ ] `.env.example` created
- [ ] All tests pass
- [ ] Documentation updated

**Expected Time**: 2-3 hours

---

## Phase 2: High-Priority Fixes (Days 2-5)

### Task 2.1: Replace Console.log Statements
**Affected Files**: 86 instances across frontend  
**Time Estimate**: 4 hours

**Step 1**: Verify logger exists:
```typescript
// frontend/lib/logger.ts
export const logger = {
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEBUG] ${message}`, data);
    }
  },
  info: (message: string, data?: any) => {
    console.info(`[INFO] ${message}`, data);
  },
  warn: (message: string, data?: any) => {
    console.warn(`[WARN] ${message}`, data);
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  }
};
```

**Step 2**: Replace console statements:
```bash
# Find all console.log usage
grep -r "console\." frontend/app frontend/components --exclude-dir=node_modules

# Replace manually or with script
find frontend/app frontend/components -name "*.tsx" -o -name "*.ts" | while read file; do
  sed -i 's/console\.log/logger.debug/g' "$file"
  sed -i 's/console\.error/logger.error/g' "$file"
  sed -i 's/console\.warn/logger.warn/g' "$file"
  sed -i 's/console\.info/logger.info/g' "$file"
done
```

**Step 3**: Add imports:
```typescript
import { logger } from '@/lib/logger';
```

**Test**:
```bash
cd frontend
npm run build
# Verify no build errors
```

---

### Task 2.2: Fix Broad Exception Handling
**Affected Files**: 153 instances  
**Time Estimate**: 8 hours

**Step 1**: Create custom exceptions:
```python
# backend/core/exceptions.py
from fastapi import HTTPException

class ApplicationException(HTTPException):
    """Base application exception."""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class ValidationException(ApplicationException):
    """Validation error."""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400)

class NotFoundException(ApplicationException):
    """Resource not found."""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=404)

class UnauthorizedException(ApplicationException):
    """Unauthorized access."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=401)

class ForbiddenException(ApplicationException):
    """Forbidden access."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=403)

class ConflictException(ApplicationException):
    """Resource conflict."""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)
```

**Step 2**: Replace generic exception handlers:
```python
# Before:
try:
    result = perform_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# After:
try:
    result = perform_operation()
except ValueError as e:
    raise ValidationException(str(e))
except KeyError as e:
    raise NotFoundException(f"Resource not found: {e}")
except sqlalchemy.exc.IntegrityError as e:
    raise ConflictException("Resource already exists")
except Exception as e:
    logger.exception("Unexpected error in operation")
    raise ApplicationException("Internal server error", status_code=500)
```

**Step 3**: Update all modules systematically:
- Start with `backend/modules/auth/`
- Then `backend/modules/users/`
- Continue through all modules

**Test**:
```bash
# Run backend tests
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
```

---

### Task 2.3: Fix N+1 Query Issues
**Affected Files**: Multiple repository files  
**Time Estimate**: 6 hours

**Step 1**: Identify N+1 queries:
```bash
# Enable SQL logging
# backend/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    echo=True  # Enable SQL logging
)
```

**Step 2**: Add eager loading:
```python
# Before:
users = db.query(User).filter(User.is_active == True).all()
for user in users:
    print(user.tutor_profile.bio)  # N+1 query!

# After:
from sqlalchemy.orm import selectinload

users = db.query(User).options(
    selectinload(User.tutor_profile)
).filter(User.is_active == True).all()
```

**Step 3**: Common patterns to fix:
```python
# Booking with user and tutor
bookings = db.query(Booking).options(
    selectinload(Booking.student),
    selectinload(Booking.tutor).selectinload(User.tutor_profile)
).all()

# Tutor with packages
tutors = db.query(TutorProfile).options(
    selectinload(TutorProfile.packages)
).all()
```

**Test**:
```bash
# Review SQL logs for duplicate queries
docker compose logs backend | grep "SELECT"
```

---

### Task 2.4: Add Missing Database Indexes
**File**: Create new migration  
**Time Estimate**: 3 hours

**Step 1**: Analyze query patterns:
```sql
-- Check table sizes and common queries
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

**Step 2**: Create migration:
```sql
-- database/migrations/006_add_missing_indexes.sql
-- Subject search index
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_subjects 
ON tutor_profiles USING GIN(subjects);

-- Booking queries
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_date 
ON bookings(tutor_id, booking_date);

CREATE INDEX IF NOT EXISTS idx_bookings_student_date 
ON bookings(student_id, booking_date);

CREATE INDEX IF NOT EXISTS idx_bookings_status 
ON bookings(status) WHERE status != 'cancelled';

-- Availability queries
CREATE INDEX IF NOT EXISTS idx_availability_tutor_date 
ON availability(tutor_id, date);

-- Message queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation 
ON messages(conversation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_unread 
ON messages(recipient_id) WHERE read_at IS NULL;

-- Package queries
CREATE INDEX IF NOT EXISTS idx_packages_tutor_active 
ON packages(tutor_id) WHERE is_active = TRUE;
```

**Step 3**: Apply migration:
```bash
docker compose exec db psql -U postgres -d authapp -f /migrations/006_add_missing_indexes.sql
```

**Test**:
```sql
-- Verify indexes created
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Test query performance
EXPLAIN ANALYZE SELECT * FROM tutor_profiles WHERE subjects && ARRAY['Math'];
```

---

### Task 2.5: Increase Test Coverage
**Time Estimate**: 12 hours

**Step 1**: Identify untested modules:
```bash
# Backend coverage
cd backend
pytest --cov=. --cov-report=html
# Check coverage report

# Frontend coverage
cd ../frontend
npm run test:coverage
# Check coverage report
```

**Step 2**: Add missing tests:

**Priority Areas**:
1. `backend/modules/availability/` - 0% coverage
2. `backend/modules/messaging/` - <50% coverage
3. Frontend components in `components/settings/` - 0% coverage
4. Frontend modals - 0% coverage

**Example test template**:
```python
# backend/modules/availability/tests/test_service.py
import pytest
from datetime import datetime, timedelta
from modules.availability.service import AvailabilityService

@pytest.fixture
def availability_service(db_session):
    return AvailabilityService(db_session)

def test_create_availability(availability_service, test_tutor):
    """Test creating availability slot."""
    availability = availability_service.create(
        tutor_id=test_tutor.id,
        date=datetime.now().date() + timedelta(days=1),
        start_time="09:00",
        end_time="17:00"
    )
    assert availability.tutor_id == test_tutor.id
    assert availability.is_available == True

def test_create_past_date_fails(availability_service, test_tutor):
    """Test creating availability for past date fails."""
    with pytest.raises(ValidationException):
        availability_service.create(
            tutor_id=test_tutor.id,
            date=datetime.now().date() - timedelta(days=1),
            start_time="09:00",
            end_time="17:00"
        )
```

**Step 3**: Run tests and verify coverage:
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

---

### Phase 2 Completion Checklist

- [ ] All console.log replaced with logger
- [ ] Exception handling standardized
- [ ] N+1 queries fixed
- [ ] Database indexes added
- [ ] Test coverage >80%
- [ ] All tests pass
- [ ] Performance benchmarks improved

**Expected Time**: 3-4 days

---

## Phase 3: Medium-Priority Fixes (Week 2)

### Task 3.1: Fix TypeScript `any` Types
**Time Estimate**: 6 hours

### Task 3.2: Add Missing Rate Limiting
**Time Estimate**: 3 hours

### Task 3.3: Fix Test Isolation
**Time Estimate**: 4 hours

### Task 3.4: Update Documentation
**Time Estimate**: 8 hours

### Task 3.5: Add Missing Foreign Keys
**Time Estimate**: 3 hours

### Task 3.6: Add Error Boundaries
**Time Estimate**: 4 hours

### Task 3.7: Improve Accessibility
**Time Estimate**: 8 hours

### Phase 3 Completion Checklist

- [ ] TypeScript types fixed
- [ ] Rate limiting complete
- [ ] Tests isolated
- [ ] Documentation updated
- [ ] Foreign keys added
- [ ] Error boundaries implemented
- [ ] Accessibility improved

**Expected Time**: 1 week

---

## Phase 4: Low-Priority Fixes (Week 3-4)

### Task 4.1: Remove Dead Code
**Time Estimate**: 2 hours

### Task 4.2: Resolve TODO Comments
**Time Estimate**: Variable

### Task 4.3: Standardize State Management
**Time Estimate**: 6 hours

### Task 4.4: Add Loading States
**Time Estimate**: 4 hours

### Task 4.5: Standardize Response Formats
**Time Estimate**: 4 hours

### Task 4.6: Add Pagination
**Time Estimate**: 6 hours

### Task 4.7: Standardize Logging
**Time Estimate**: 4 hours

### Phase 4 Completion Checklist

- [ ] Dead code removed
- [ ] TODOs resolved or documented
- [ ] State management standardized
- [ ] Loading states added
- [ ] Response formats standardized
- [ ] Pagination added
- [ ] Logging standardized

**Expected Time**: 1-2 weeks

---

## Progress Tracking

### Week 1
- [ ] Phase 1 complete (Critical fixes)
- [ ] Phase 2 started

### Week 2
- [ ] Phase 2 complete (High-priority fixes)
- [ ] Phase 3 complete (Medium-priority fixes)

### Week 3-4
- [ ] Phase 4 complete (Low-priority fixes)
- [ ] Final review and testing

---

## Testing Strategy

After each phase:

```bash
# Run full test suite
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run linters
cd backend && ruff check . && mypy .
cd frontend && npm run lint && npm run type-check

# Run security scan
docker compose exec backend safety check
cd frontend && npm audit

# Performance test
docker compose exec backend pytest --benchmark-only
```

---

## Rollback Plan

If any phase causes issues:

```bash
# Rollback to previous commit
git reset --hard HEAD^

# Or create a branch before starting
git checkout -b fix-phase-1
# Make changes
git commit -m "Phase 1 fixes"
# If issues occur:
git checkout main
```

---

## Success Metrics

- [ ] All critical issues resolved
- [ ] Test coverage >80%
- [ ] No hardcoded credentials
- [ ] All environment variables validated
- [ ] Performance improved (query times <100ms)
- [ ] Security audit passed
- [ ] Documentation complete

---

## Next Steps

1. Review this action plan with the team
2. Assign tasks to team members
3. Create tracking issues in project management system
4. Start Phase 1 immediately
5. Schedule daily standups during fix period
6. Plan code review sessions after each phase

---

*Last Updated: January 24, 2026*
