# Security & Reliability

## 1. Authentication Architecture

### Authentication Flow

```
+-----------------------------------------------------------------------------+
|                         AUTHENTICATION FLOW                                  |
+-----------------------------------------------------------------------------+

Email/Password Flow:
  +------------+     +-----------+     +----------+
  | Email +    |---->| bcrypt    |---->| JWT      |----> HttpOnly Cookie
  | Password   |     | (12 rounds)|    | (HS256)  |
  +------------+     +-----------+     | 30 min   |
                                       +----------+

Google OAuth Flow:
  +------------+     +-----------+
  | Google     |---->| OAuth 2.0 |-----+
  | Sign-In    |     | (state)   |     |
  +------------+     +-----------+     v
                                  +----------+
                                  | JWT      |----> HttpOnly Cookie
                                  | (HS256)  |
                                  +----------+
```

### JWT Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "student|tutor|admin|owner",
  "exp": 1706543210,
  "iat": 1706541410
}
```

### Security Properties

| Property | Implementation | Notes |
|----------|---------------|-------|
| Password Hashing | bcrypt, 12 rounds | ~300ms per hash |
| Token Algorithm | HS256 (symmetric) | Consider RS256 for microservices |
| Token Lifetime | 30 minutes | Configurable via env |
| OAuth State | HMAC-signed | CSRF protection |
| Cookie Flags | Secure, HttpOnly, SameSite=Strict | XSS/CSRF protection |

### Implementation Details

```python
# core/security.py
class TokenManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, user: User, expires_delta: timedelta) -> str:
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + expires_delta,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

class PasswordHasher:
    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self.rounds)).decode()

    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())
```

## 2. Authorization Model

### Role Hierarchy

```
OWNER (level 3)
   |
   +-- Can access: Everything
   +-- Special: Business analytics, commission settings
   |
   v
ADMIN (level 2)
   |
   +-- Can access: Admin panel, user management
   +-- Special: Tutor approvals, dispute resolution
   |
   v
TUTOR (level 1)
   |
   +-- Can access: Tutor dashboard, own bookings
   +-- Special: Accept/decline requests, earnings
   |
   v
STUDENT (level 0)
   |
   +-- Can access: Student features, bookings
   +-- Special: Search tutors, book sessions
```

### Dependency-Based Access Control

```python
# core/dependencies.py

# Type aliases for clean signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
OwnerUser = Annotated[User, Depends(get_current_owner_user)]
TutorUser = Annotated[User, Depends(get_current_tutor_user)]
StudentUser = Annotated[User, Depends(get_current_student_user)]

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token."""
    payload = token_manager.verify_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or user.deleted_at:
        raise HTTPException(401, "Invalid credentials")
    return user

async def get_current_admin_user(user: CurrentUser) -> User:
    """Require admin or owner role."""
    if user.role not in ("admin", "owner"):
        raise HTTPException(403, "Admin access required")
    return user

async def get_current_owner_user(user: CurrentUser) -> User:
    """Require owner role only."""
    if user.role != "owner":
        raise HTTPException(403, "Owner access required")
    return user
```

### Resource-Based Authorization

```python
# Pattern: Verify ownership before access
def _verify_booking_ownership(booking: Booking, user: User, db: Session) -> bool:
    if user.role == "student":
        return booking.student_id == user.id
    elif user.role == "tutor":
        tutor = db.query(TutorProfile).filter(
            TutorProfile.user_id == user.id
        ).first()
        return booking.tutor_profile_id == tutor.id if tutor else False
    elif user.role in ("admin", "owner"):
        return True  # Full access
    return False

# Usage in endpoint
@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, user: CurrentUser, db: DatabaseSession):
    booking = get_booking_or_404(booking_id, db)
    if not _verify_booking_ownership(booking, user, db):
        raise HTTPException(403, "Access denied")
    return booking
```

## 3. Security Controls

### Input Validation

```python
# core/sanitization.py
class InputSanitizer:
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potential XSS payloads."""
        # Remove script tags, event handlers, etc.
        return bleach.clean(text, tags=[], strip=True)

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and normalize email."""
        email = email.lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email

# Applied via Pydantic validators
class BookingCreateRequest(BaseModel):
    notes_student: Optional[str] = Field(max_length=2000)

    @validator('notes_student')
    def sanitize_notes(cls, v):
        return InputSanitizer.sanitize_html(v) if v else v
```

### SQL Injection Prevention

```python
# SQLAlchemy ORM provides parameterized queries
# All queries use bound parameters, not string concatenation

# Safe:
db.query(User).filter(User.email == email).first()

# Never do:
db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # VULNERABLE
```

### Rate Limiting

```python
# core/rate_limiting.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Configured limits
RATE_LIMITS = {
    "registration": "5/minute",
    "login": "10/minute",
    "api_default": "60/minute",
    "password_reset": "3/minute",
}

# Usage
@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, ...):
    ...
```

### Security Headers

```python
# core/middleware.py
class SecurityHeadersMiddleware:
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # OWASP recommended headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = self._build_csp()
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response
```

## 4. Threat Model

### Threat Matrix

| Threat | Probability | Impact | Risk | Mitigation |
|--------|-------------|--------|------|------------|
| Credential Stuffing | Medium | High | High | Rate limiting, bcrypt |
| Token Theft | Medium | High | High | Short expiry, HTTPS, Secure cookies |
| Privilege Escalation | Low | Critical | Medium | Role checks, ownership verification |
| SQL Injection | Low | Critical | Low | ORM, parameterized queries |
| XSS | Low | High | Low | CSP, input sanitization, React escaping |
| CSRF | Low | Medium | Low | SameSite cookies, no session cookies |
| DDoS | Medium | High | Medium | Rate limiting, CDN |
| Data Exfiltration | Medium | Critical | Medium | Pagination limits, field filtering |
| Insider Threat | Low | Critical | Medium | Audit logging, role separation |

### Mitigation Details

#### Credential Stuffing
- bcrypt with 12 rounds (~300ms per attempt)
- Login rate limit: 10/minute
- Account lockout after 5 failed attempts (future)
- Breach password checking (future)

#### Token Theft
- 30-minute token lifetime
- HTTPS enforced in production
- Secure, HttpOnly cookies
- Token revocation list (future)

#### Privilege Escalation
- Role validated on every request
- Resource ownership checks
- No role escalation endpoints
- Audit logging for admin actions

## 5. Audit Logging

### Audit Trail Implementation

```python
# models/admin.py
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True)
    table_name = Column(String(100))
    record_id = Column(Integer)
    action = Column(String(20))  # INSERT, UPDATE, DELETE, SOFT_DELETE, RESTORE
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)

# Indexes for query performance
Index('idx_audit_log_table_record', table_name, record_id)
Index('idx_audit_log_changed_by', changed_by)
Index('idx_audit_log_changed_at', changed_at.desc())
```

### Logged Operations

| Operation | Table | Fields Logged |
|-----------|-------|---------------|
| User creation | users | All fields (password hashed) |
| Role changes | users | old_role, new_role |
| Tutor approval | tutor_profiles | status change, approver |
| Booking state | bookings | All state transitions |
| Payment events | payments | Amount, status changes |
| Admin actions | various | Action, target, actor |

## 6. Observability

### Current Implementation

```python
# Structured logging
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Booking created", extra={
    "booking_id": booking.id,
    "student_id": student.id,
    "tutor_id": tutor.id,
    "amount_cents": amount,
})
```

### Recommended Stack

```
+-----------------------------------------------------------------------------+
|                         OBSERVABILITY STACK                                  |
+-----------------------------------------------------------------------------+

Logs ---------> stdout ---------> Cloud Logging (GCP/AWS)
                                         |
Metrics ------> Prometheus ------> Grafana
                     |
Traces -------> OpenTelemetry ---> Jaeger/Tempo

Errors -------> Sentry

Uptime -------> Healthchecks.io / Better Uptime
```

### Key Metrics to Track

| Category | Metric | Alert Threshold |
|----------|--------|-----------------|
| Availability | Error rate | > 1% (warn), > 5% (critical) |
| Latency | P95 response time | > 500ms (warn), > 2s (critical) |
| Saturation | DB connection pool | > 80% (warn), > 95% (critical) |
| Traffic | Requests per second | Baseline +200% (info) |
| Business | Payment failures | > 2% (warn), > 5% (critical) |
| Business | Booking conversions | < 50% of baseline (warn) |

### Health Check Endpoints

```python
@app.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "healthy"}

@app.get("/api/health/integrity")
async def integrity_check(db: Session = Depends(get_db), user: AdminUser):
    """Database connectivity and data integrity check."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "database": "connected",
            "redis": check_redis(),
            "storage": check_minio(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 7. Data Protection

### Personal Data Handling

| Data Type | Classification | Protection |
|-----------|---------------|------------|
| Email | PII | Encrypted at rest |
| Password | Secret | bcrypt hashed |
| Payment info | Sensitive | Stripe handles (PCI) |
| Profile data | PII | Soft delete, access control |
| Messages | Private | User-scoped access |
| Session history | Private | Audit trail |

### GDPR Compliance

| Right | Implementation |
|-------|---------------|
| Access | User can export their data |
| Rectification | Profile editing available |
| Erasure | Soft delete + data anonymization |
| Portability | JSON export endpoint |
| Restriction | Account deactivation |

### Soft Delete Pattern

```python
# All PII tables support soft delete
class User(Base):
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))

# Queries exclude deleted records by default
def get_active_users(db: Session):
    return db.query(User).filter(User.deleted_at.is_(None)).all()
```

## 8. Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 | Complete outage | 15 minutes | Site down, payments failing |
| P2 | Major degradation | 1 hour | Bookings failing, slow response |
| P3 | Minor issues | 4 hours | Feature not working, UI bug |
| P4 | Low priority | 24 hours | Cosmetic issues, minor bugs |

### Response Procedures

1. **Detection**: Monitoring alert or user report
2. **Triage**: Assess severity and impact
3. **Communication**: Notify stakeholders
4. **Mitigation**: Immediate fixes or rollback
5. **Resolution**: Root cause fix
6. **Post-mortem**: Document and improve

### Rollback Procedure

```bash
# Database rollback (if migration issue)
# Restore from latest backup
pg_restore -d authapp backup_latest.dump

# Application rollback
docker compose down
git checkout previous-tag
docker compose up --build -d

# Verify health
curl https://api.example.com/health
```
