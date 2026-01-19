# DDD (Domain-Driven Design) Compliance Analysis
## EduStream LoginTemplate Codebase

**Analysis Date**: November 9, 2025  
**Codebase**: Full-stack FastAPI + Next.js authentication platform  
**Scope**: Thorough review of DDD principles, layering, bounded contexts, and architectural patterns

---

## Executive Summary

**Overall DDD Maturity**: **PARTIAL (50-60%)**

The codebase demonstrates **intentional DDD structure** with clear separation of layers (domain, application, infrastructure, presentation), but suffers from **critical leakage across architectural boundaries**. Two modules (Auth, TutorProfile) show proper DDD patterns while others (Messages, Bookings) mix concerns and expose ORM directly in presentation layers.

### Key Findings:
- Bounded contexts exist but are **not cleanly enforced**
- Domain entities are **properly isolated** (Auth, TutorProfile)
- **Presentation layer violates SRP**: contains business logic and direct DB queries
- Repository pattern **partially implemented** (Auth, TutorProfile only)
- Cross-cutting concerns (logging, error handling) **lack consistency**
- **No event-driven architecture** despite complex domain (bookings, messaging)

---

## 1. Module Structure & Bounded Contexts

### Current Structure (Good Foundation)

```
backend/modules/
├── auth/
│   ├── domain/           [GOOD]
│   │   ├── entities.py
│   ├── application/      [GOOD]
│   │   └── services.py
│   ├── infrastructure/   [GOOD]
│   │   └── repository.py
│   └── presentation/     [GOOD]
│       └── api.py
│
├── tutor_profile/
│   ├── domain/           [GOOD]
│   │   ├── entities.py
│   │   └── repositories.py (interface)
│   ├── application/      [GOOD]
│   │   ├── services.py
│   │   └── dto.py
│   ├── infrastructure/   [GOOD]
│   │   └── repositories.py (implementation)
│   └── presentation/     [GOOD]
│       └── api.py
│
├── messages/
│   ├── presentation/     [BAD]
│   │   └── api.py
│   └── websocket.py
│   [MISSING: domain/, application/, infrastructure/]
│
├── bookings/
│   ├── presentation/     [PARTIAL]
│   │   └── api.py
│   ├── service.py        [MEDIOCRE]
│   └── policy_engine.py  [GOOD]
│   [MISSING: domain/, infrastructure/, proper repository]
│
└── [Other modules: minimal/no layering]
```

### Violation 1: Messaging Module - Complete Layer Inversion

**Location**: `/backend/modules/messages/presentation/api.py`

**Problem**: Presentation layer directly queries and manipulates ORM models.

```python
# VIOLATION: Business logic in presentation
@router.post("", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),  # Direct DB access in presentation!
):
    # VIOLATION: Direct ORM model instantiation
    message = Message(
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        booking_id=message_data.booking_id,
        message=sanitized_message,
    )
    
    db.add(message)       # VIOLATION: Direct persistence in presentation
    db.commit()
    db.refresh(message)
    
    # VIOLATION: Business logic (WebSocket broadcasting) in presentation
    await manager.send_personal_message(message_payload, message_data.recipient_id)
```

**Impact**:
- Cannot test business logic in isolation
- WebSocket manager tightly coupled to HTTP API
- Domain rules (message validation, threading) not enforced
- No repository abstraction → difficult to swap backends

**Expected DDD Structure**:
```python
# domain/entities.py
@dataclass
class MessageEntity:
    id: Optional[int]
    sender_id: int
    recipient_id: int
    content: str  # Named "content", not "message"
    booking_id: Optional[int] = None
    is_read: bool = False
    
    def mark_as_read(self) -> None:
        """Domain method: mark message as read."""
        self.is_read = True
    
    def validate(self) -> None:
        """Domain validation."""
        if not self.content or len(self.content) > 2000:
            raise BusinessRuleError("Message must be 1-2000 chars")

# application/service.py
class MessageService:
    def __init__(self, repository: MessageRepository):
        self.repository = repository
    
    def send_message(self, entity: MessageEntity) -> MessageEntity:
        entity.validate()  # Business rule enforcement
        return self.repository.save(entity)

# infrastructure/repository.py
class SqlMessageRepository(MessageRepository):
    def save(self, entity: MessageEntity) -> MessageEntity:
        # Convert entity → model, persist, convert back
        model = Message(...)
        self.db.add(model)
        self.db.commit()
        return self._to_entity(model)

# presentation/api.py
@router.post("")
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    entity = MessageEntity(
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        content=message_data.message,  # Sanitization in domain or input layer
    )
    saved = service.send_message(entity)  # Business logic in service
    return message_to_response(saved)
```

---

### Violation 2: Bookings Module - Partial Layering

**Location**: `/backend/modules/bookings/`

**Problem**: Service layer exists but presentation layer bypasses it; state machine mixed with HTTP concerns.

```python
# Current (Problematic)
# presentation/api.py
@router.post("/bookings")
async def create_booking(
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = BookingService(db)
    booking = service.create_booking(
        student_id=current_user.id,
        tutor_id=payload.tutor_id,
        ...
    )
    return booking_to_dto(booking)

# service.py (Contains BOTH business logic AND ORM operations)
class BookingService:
    def create_booking(self, student_id: int, tutor_id: int, ...) -> Booking:
        tutor_profile = self.db.query(TutorProfile)...  # MIXING: should be in repo
        
        # GOOD: Domain logic (policy evaluation)
        conflicts = self._check_conflicts(tutor_id, start_at, end_at)
        
        # BAD: Direct ORM
        booking = Booking(
            student_id=student_id,
            tutor_id=tutor_id,
            ...
        )
        self.db.add(booking)
        self.db.commit()
        return booking
```

**Impact**:
- Service layer is a "fat service" that does too much
- Bookings state machine (`can_transition()`) not integrated with aggregate
- No aggregate root pattern
- Policy engine (good!) isolated from booking entity

**Expected DDD Structure**:
```python
# domain/value_objects.py
@dataclass(frozen=True)
class BookingTimeSlot:
    start_at: datetime
    duration_minutes: int
    
    @property
    def end_at(self) -> datetime:
        return self.start_at + timedelta(minutes=self.duration_minutes)
    
    def overlaps_with(self, other: 'BookingTimeSlot') -> bool:
        """Domain logic for time overlap."""
        return not (self.end_at <= other.start_at or 
                    self.start_at >= other.end_at)

# domain/aggregate_root.py
@dataclass
class BookingAggregate:
    """Aggregate root for booking domain."""
    id: Optional[int]
    student_id: int
    tutor_profile_id: int
    time_slot: BookingTimeSlot
    status: BookingStatus  # Enum
    
    @property
    def can_cancel(self) -> bool:
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    
    def cancel_by_student(self) -> None:
        """Domain method: validate state transition."""
        if not self.can_cancel:
            raise BusinessRuleError(f"Cannot cancel booking in {self.status} state")
        self.status = BookingStatus.CANCELLED_BY_STUDENT

# infrastructure/repository.py
class BookingRepository:
    def find_conflicts(
        self, 
        tutor_id: int, 
        time_slot: BookingTimeSlot
    ) -> List[BookingAggregate]:
        """Find conflicting bookings via repository."""
        models = self.db.query(Booking).filter(...)
        return [self._to_aggregate(m) for m in models]
    
    def save(self, aggregate: BookingAggregate) -> BookingAggregate:
        model = self._to_model(aggregate)
        self.db.add(model)
        self.db.commit()
        return self._to_aggregate(model)

# application/service.py
class CreateBookingUseCase:
    def __init__(self, booking_repo: BookingRepository, tutor_repo: TutorRepository):
        self.booking_repo = booking_repo
        self.tutor_repo = tutor_repo
    
    async def execute(self, cmd: CreateBookingCommand) -> BookingDTO:
        # Validation at application layer
        tutor = await self.tutor_repo.find_by_id(cmd.tutor_id)
        if not tutor:
            raise NotFoundError("Tutor")
        
        # Check conflicts at repository level
        conflicts = self.booking_repo.find_conflicts(
            tutor.profile_id,
            cmd.time_slot
        )
        if conflicts:
            raise BusinessRuleError("Time slot unavailable")
        
        # Create aggregate at domain layer
        booking = BookingAggregate(
            id=None,
            student_id=cmd.student_id,
            tutor_profile_id=tutor.profile_id,
            time_slot=cmd.time_slot,
            status=BookingStatus.PENDING,
        )
        
        # Persist via repository
        saved = self.booking_repo.save(booking)
        return booking_to_dto(saved)
```

---

## 2. Domain Layer Analysis

### Well-Implemented Domains

#### Auth Domain (Grade: A-)

**File**: `/backend/modules/auth/domain/entities.py`

**Strengths**:
- Clear `UserEntity` dataclass
- Domain methods (`is_admin()`, `can_access_admin()`)
- Type-safe with Optional fields
- No ORM dependencies

```python
@dataclass
class UserEntity:
    id: Optional[int]
    email: str
    hashed_password: str
    role: str
    
    def is_admin(self) -> bool:
        """Domain method: role check."""
        return self.role == "admin"
    
    def can_access_admin(self) -> bool:
        """Domain method: permission logic."""
        return self.is_admin()
```

**Issues**:
- Role strings ("admin", "student") should be Enums
- Domain methods lack business context (e.g., `can_access_admin` is trivial)
- No value objects (email should be `Email` VO with validation)
- Password hashing logic should be in domain service, not in service layer

#### TutorProfile Domain (Grade: B+)

**File**: `/backend/modules/tutor_profile/domain/entities.py`

**Strengths**:
- Aggregate root pattern: `TutorProfileAggregate`
- Proper composition of child entities
- Value objects (TutorSubjectEntity, TutorCertificationEntity)
- Clear data structure with slots optimization

```python
@dataclass(slots=True)
class TutorProfileAggregate:
    """Aggregate root for tutor profile domain."""
    id: int
    user_id: int
    # ... core fields
    subjects: List[TutorSubjectEntity] = field(default_factory=list)
    availabilities: List[TutorAvailabilityEntity] = field(default_factory=list)
    certifications: List[TutorCertificationEntity] = field(default_factory=list)
```

**Issues**:
- No domain methods on aggregate (e.g., `add_certification()`, `update_availability()`)
- No validation methods (e.g., `validate_pricing()`)
- Business rules (approval, versioning) scattered in repository
- Child entities are mutable dataclasses (should be immutable or have methods)

**Missing Domain Logic Example**:
```python
# SHOULD BE IN DOMAIN, currently in repository/service
class TutorProfileAggregate:
    def add_certification(self, cert: TutorCertificationEntity) -> None:
        """Domain method: add certification with validation."""
        if len(self.certifications) >= 10:
            raise BusinessRuleError("Maximum 10 certifications")
        if not cert.issue_date or not cert.expiration_date:
            raise BusinessRuleError("Certification dates required")
        self.certifications.append(cert)
    
    def is_complete(self) -> bool:
        """Domain method: check profile completion."""
        return (self.title and self.bio and 
                len(self.subjects) >= 1 and 
                len(self.educations) >= 1)
    
    def can_go_live(self) -> bool:
        """Domain method: check if profile can be published."""
        return self.is_complete() and self.is_approved
```

### Weak/Missing Domains

#### Messages Domain

**Status**: DOES NOT EXIST

**Should Define**:
```python
# domain/value_objects.py
@dataclass(frozen=True)
class MessageContent:
    text: str
    
    def __post_init__(self):
        if not self.text or len(self.text) > 2000:
            raise ValueError("Message must be 1-2000 characters")

@dataclass(frozen=True)
class MessageParticipants:
    sender_id: int
    recipient_id: int
    
    def __post_init__(self):
        if self.sender_id == self.recipient_id:
            raise ValueError("Cannot message yourself")

# domain/entities.py
@dataclass
class MessageEntity:
    id: Optional[int]
    participants: MessageParticipants
    content: MessageContent
    booking_id: Optional[int]
    is_read: bool = False
    created_at: Optional[datetime] = None
    
    def mark_read(self) -> None:
        self.is_read = True
    
    def belongs_to_thread(self, user_id: int, other_id: int, booking_id: Optional[int]) -> bool:
        """Domain logic: check if message is in conversation thread."""
        users_match = (
            (self.participants.sender_id == user_id and 
             self.participants.recipient_id == other_id) or
            (self.participants.sender_id == other_id and 
             self.participants.recipient_id == user_id)
        )
        booking_match = self.booking_id == booking_id or (booking_id is None and self.booking_id is None)
        return users_match and booking_match
```

#### Bookings Domain

**Status**: PARTIAL (policy_engine.py exists but not integrated)

**Issues**:
- `PolicyDecision` dataclass is good but not tied to aggregate
- State machine logic in service, not aggregate
- No aggregate root class

**Should Look Like**:
```python
# domain/entities.py
class BookingStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED_BY_STUDENT = "CANCELLED_BY_STUDENT"
    COMPLETED = "COMPLETED"

@dataclass
class BookingAggregate:
    id: Optional[int]
    student_id: int
    tutor_profile_id: int
    status: BookingStatus
    start_at: datetime
    duration_minutes: int
    # ... other fields
    
    def request_cancellation_by_student(self, now: datetime) -> CancellationDecision:
        """Domain method: apply cancellation policy."""
        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=self.start_at,
            now=now,
            rate_cents=self.rate_cents,
            lesson_type=self.lesson_type,
            is_trial=self.is_trial,
            is_package=self.is_package,
        )
        
        if decision.allow:
            self.status = BookingStatus.CANCELLED_BY_STUDENT
        
        return decision  # Return decision object, not just allow flag
    
    def can_transition_to(self, new_status: BookingStatus) -> bool:
        """Domain method: validate state transitions."""
        allowed = self._get_valid_transitions()
        return new_status in allowed[self.status]
    
    @staticmethod
    def _get_valid_transitions() -> Dict[BookingStatus, List[BookingStatus]]:
        return {
            BookingStatus.PENDING: [
                BookingStatus.CONFIRMED,
                BookingStatus.CANCELLED_BY_STUDENT,
                BookingStatus.CANCELLED_BY_TUTOR,
            ],
            # ... etc
        }
```

---

## 3. Application Layer Analysis

### Proper Implementation: Auth Module

**File**: `/backend/modules/auth/application/services.py`

**Strengths**:
- Clean orchestration of domain entities
- Dependency injection of repository
- Input validation before business logic
- Logging at service level
- Transaction management

```python
class AuthService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def register_user(self, email: str, password: str, role: str = "student") -> UserEntity:
        # 1. Validate inputs at application layer
        if not email or len(password) < 6:
            raise HTTPException(...)
        
        # 2. Check business rule via repository
        if self.repository.exists_by_email(email):
            raise HTTPException(...)
        
        # 3. Create domain entity
        user_entity = UserEntity(
            id=None,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
        )
        
        # 4. Persist and return
        return self.repository.create(user_entity)
```

**Issues**:
- HTTPException imported in domain layer (should be in presentation)
- Password hashing should be in domain service
- Role assignment logic should reject non-"student" roles (only backend assignment allowed)

### Problematic Implementation: TutorProfile Service

**File**: `/backend/modules/tutor_profile/application/services.py`

**Issues**:
1. **Dependency on concrete repository**: Should depend on protocol/interface

```python
# Current (WRONG)
class TutorProfileService:
    def __init__(self, repository: TutorProfileRepository):
        # 'repository' is the Protocol interface, but...
        self.repository = repository  # Called directly without abstraction

# Should be
class TutorProfileService:
    def __init__(self, repository: TutorProfileRepository):
        # This is already correct - 'repository' is Protocol
        # But the implementation (SqlAlchemyTutorProfileRepository)
        # imports HTTPException, creating tight coupling
        pass
```

2. **Infrastructure layer imports HTTPException**:

```python
# infrastructure/repositories.py
class SqlAlchemyTutorProfileRepository(TutorProfileRepository):
    def get_or_create_by_user(self, db: Session, user_id: int):
        from fastapi import HTTPException, status  # VIOLATION
        
        # Should raise domain exceptions, let presentation layer convert
```

### Missing: Bookings Application Layer

**Current Structure**:
```python
# Only has service.py, which mixes concerns
class BookingService:
    def __init__(self, db: Session):
        self.db = db  # Tight coupling to DB
    
    def create_booking(self, ...):
        # Contains business logic AND infrastructure calls
```

**Should Have**:
```python
# application/dto/
class CreateBookingCommand:
    student_id: int
    tutor_id: int
    start_at: datetime
    duration_minutes: int

class BookingDTO:
    id: int
    student_id: int
    tutor_id: int
    status: str

# application/services.py
class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        tutor_repo: TutorRepository,
        student_repo: StudentRepository,
    ):
        self.booking_repo = booking_repo
        self.tutor_repo = tutor_repo
        self.student_repo = student_repo
    
    async def create_booking(self, cmd: CreateBookingCommand) -> BookingDTO:
        # Pure application logic
        tutor = self.tutor_repo.find_by_id(cmd.tutor_id)
        student = self.student_repo.find_by_id(cmd.student_id)
        
        # Create domain aggregate
        booking = BookingAggregate.create(
            student_id=student.id,
            tutor_profile_id=tutor.profile_id,
            time_slot=BookingTimeSlot(cmd.start_at, cmd.duration_minutes),
        )
        
        # Persist
        saved = self.booking_repo.save(booking)
        return booking_to_dto(saved)
```

---

## 4. Infrastructure Layer Analysis

### Good: Auth Repository

**File**: `/backend/modules/auth/infrastructure/repository.py`

**Strengths**:
- Clean conversion between ORM model ↔ domain entity
- Query abstractions (case-insensitive email lookup)
- Implements repository protocol
- No business logic leakage

```python
class UserRepository:
    def _to_entity(self, user: User) -> UserEntity:
        """Map ORM model to domain entity."""
        return UserEntity(...)
    
    def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Repository method: case-insensitive lookup."""
        user = (
            self.db.query(User)
            .filter(func.lower(User.email) == email.lower())
            .first()
        )
        return self._to_entity(user) if user else None
```

### Good: TutorProfile Repository

**File**: `/backend/modules/tutor_profile/infrastructure/repositories.py`

**Strengths**:
- Implements `TutorProfileRepository` protocol
- Eager loading optimization (joinedload)
- Conversion between models and aggregates
- Pagination support

**Issues**:
- Imports `HTTPException` (framework code in infrastructure!)
- Business rule validation in repository (should be domain)

```python
# VIOLATION: HTTPException in infrastructure layer
def get_or_create_by_user(self, db: Session, user_id: int):
    from fastapi import HTTPException, status
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(...)  # Framework code here!

# Should be
def get_or_create_by_user(self, db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User")  # Domain exception
```

### Missing: Message Repository

Messages module has no repository at all. Direct ORM access in presentation layer.

### Partial: Bookings Repository

Bookings has a "service" but no proper repository abstraction. Conflict checking is inline in service:

```python
# service.py
def create_booking(self, ...):
    # Should be in repository
    conflicts = self.db.query(Booking).filter(...).all()
    if conflicts:
        raise HTTPException(...)
```

---

## 5. Presentation Layer Analysis

### Good Pattern: Auth API

**File**: `/backend/modules/auth/presentation/api.py`

**Strengths**:
- Dependency injection of service: `Depends(get_auth_service)`
- HTTP exception handling (401, 400, 409)
- Comprehensive docstrings
- Delegates to application layer

```python
@router.post("/register")
async def register(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register endpoint delegates to service."""
    try:
        created_user = auth_service.register_user(...)
        return user_to_response(created_user)
    except DuplicateError:
        raise HTTPException(status_code=409, detail="Email exists")
```

### Bad Pattern: Messages API

**File**: `/backend/modules/messages/presentation/api.py`

**Violations**:
1. Direct DB access: `db: Session = Depends(get_db)`
2. ORM model instantiation: `message = Message(...)`
3. Direct persistence: `db.add(message); db.commit()`
4. Business logic: `await manager.send_personal_message(...)`
5. No service layer

```python
@router.post("")
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),  # VIOLATION: presentation has DB
):
    # VIOLATION: Validation logic
    sanitized_message = sanitize_text_input(message_data.message)
    
    # VIOLATION: Direct ORM
    message = Message(
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        message=sanitized_message,
    )
    
    # VIOLATION: Persistence logic
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # VIOLATION: Business logic (should be in domain)
    await manager.send_personal_message(
        message_payload,
        message_data.recipient_id,
    )
    
    return message  # Returns ORM model, not DTO!
```

### Problematic: Bookings API

**File**: `/backend/modules/bookings/presentation/api.py`

**Issues**:
1. Uses service correctly (good):
   ```python
   service = BookingService(db)
   booking = service.create_booking(...)
   ```

2. But helper functions bypass service (bad):
   ```python
   def _get_booking_or_404(booking_id: int, db: Session):
       booking = db.query(Booking).filter(...).first()  # Direct DB access
   ```

3. Verification logic in presentation (bad):
   ```python
   def _verify_booking_ownership(booking: Booking, current_user: User, db: Session):
       # Should be in domain or application
       if current_user.role == "student":
           if booking.student_id != current_user.id:
               raise HTTPException(...)
   ```

---

## 6. Cross-Cutting Concerns

### Logging Inconsistency

**Issue**: No centralized logging pattern; each module rolls its own.

**Auth Module** (Good):
```python
logger = logging.getLogger(__name__)
logger.debug(f"Registering user: {email}")
logger.info(f"User registered: {email}")
logger.warning(f"Failed login: {email}")
```

**Messages Module** (Missing):
```python
# No logging at all in presentation/api.py
# Only in websocket.py:
logger.info("User %d connected")
logger.error("Error sending message: %s", str(e))
```

**Bookings Module** (Minimal):
```python
# Logging only in service.py, not in api.py
```

**Expected Pattern**:
```python
# core/logging.py
def get_logger(module: str):
    logger = logging.getLogger(module)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger

# Any module
logger = get_logger(__name__)

# With context
logger.info("User registered", extra={
    "user_id": user.id,
    "email": user.email,
    "role": user.role,
})
```

### Error Handling Inconsistency

**Auth** (Good):
```python
if not user or not verify_password(password, hashed):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )
```

**Messages** (Ad-hoc):
```python
if not recipient:
    raise HTTPException(status_code=404, detail="Recipient not found")

if not sanitized_message or not sanitized_message.strip():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Message cannot be empty"
    )
```

**Bookings** (Mixed):
```python
# In service
raise HTTPException(status_code=400, detail="...")

# Should use domain exceptions
raise BusinessRuleError("...")
```

**Expected Pattern** (Already exists in `/backend/core/exceptions.py`):
```python
class BusinessRuleError(AppException):
    """Raised when a business rule is violated."""
    
# Use in application/domain
try:
    service.create_booking(...)
except BusinessRuleError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
except NotFoundError:
    raise HTTPException(status_code=404, detail="Not found")
```

### Transaction Management

**Issue**: No explicit transaction boundaries.

**Current**: Each operation commits immediately
```python
db.add(message)
db.commit()  # Commits immediately, no rollback on downstream errors
```

**Should Be**:
```python
try:
    message_repo.save(entity)  # Save in transaction
    event_bus.publish(MessageSent(entity))  # Publish event
    # If event publishing fails, transaction rolled back
except Exception:
    db.rollback()
    raise
```

---

## 7. Dependency Inversion Violations

### Violation 1: Infrastructure imports FastAPI

**File**: `/backend/modules/tutor_profile/infrastructure/repositories.py`

```python
from fastapi import HTTPException, status

class SqlAlchemyTutorProfileRepository:
    def get_or_create_by_user(self, db, user_id):
        if not user:
            raise HTTPException(...)  # Framework code in infra!
```

**Impact**: Cannot test repository in isolation without FastAPI

**Fix**:
```python
# infrastructure/repositories.py
class NotFoundError(Exception):
    """Domain exception."""

class SqlAlchemyTutorProfileRepository:
    def get_or_create_by_user(self, db, user_id):
        if not user:
            raise NotFoundError(f"User {user_id}")

# presentation/api.py (handles conversion)
try:
    profile = repo.get_or_create_by_user(db, user_id)
except NotFoundError:
    raise HTTPException(status_code=404, detail="User not found")
```

### Violation 2: Presentation depends on global manager

**File**: `/backend/modules/messages/presentation/api.py`

```python
from modules.messages.websocket_manager import manager

@router.post("")
async def send_message(...):
    await manager.send_personal_message(...)  # Global state
```

**Impact**: Tight coupling, difficult to mock, WebSocket side effect in HTTP handler

**Fix**:
```python
# Define interface in domain
class MessagePublisher(Protocol):
    async def publish_new_message(self, message: MessageEntity) -> None:
        """Publish message to subscribers."""

# Application service depends on interface
class SendMessageUseCase:
    def __init__(self, repository: MessageRepository, publisher: MessagePublisher):
        self.repository = repository
        self.publisher = publisher
    
    async def execute(self, cmd: SendMessageCommand):
        entity = MessageEntity.create(cmd)
        saved = self.repository.save(entity)
        await self.publisher.publish_new_message(saved)
        return saved

# Presentation layer injects both
@router.post("")
async def send_message(
    cmd: MessageCreate,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    result = await use_case.execute(SendMessageCommand.from_request(cmd))
    return message_to_response(result)
```

---

## 8. Absence of Domain Events

### Problem

Complex domains (Bookings, Messages) should emit events but don't:

```python
# CURRENT: No events
booking = service.create_booking(...)
db.commit()  # Only database state changes

# EXPECTED: Domain events
class BookingCreated(DomainEvent):
    booking_id: int
    student_id: int
    tutor_id: int
    scheduled_at: datetime

class BookingConfirmed(DomainEvent):
    booking_id: int
    confirmed_by: str  # "tutor" or "student"

booking = booking_aggregate.create(...)
booking.add_event(BookingCreated(...))
booking.add_event(BookingConfirmed(...))

# Service publishes events
saved = booking_repo.save(booking)
for event in saved.events:
    event_bus.publish(event)
    # Triggers: notification creation, audit logging, etc.
```

### Impact

Without events:
- No audit trail
- Notifications created via separate API calls (inconsistent)
- Cascading actions require hardcoded service calls
- Difficult to implement CQRS or event sourcing

---

## 9. Model/Entity Consistency Issues

### Models in `models/` vs Modules

**Current**:
- ORM models in `/backend/models/` (centralized)
- Domain entities in `/backend/modules/*/domain/entities.py`
- Duplication and inconsistency

**Example**:
```python
# models/auth.py
class User(Base):
    email: str
    role: str  # String

# modules/auth/domain/entities.py
@dataclass
class UserEntity:
    role: str  # String, not Enum

# Frontend expects
# "admin" | "student" | "tutor"
```

**Should Be**:
```python
# models/base.py
class Role(Enum):
    ADMIN = "admin"
    STUDENT = "student"
    TUTOR = "tutor"

# models/auth.py
class User(Base):
    role: Role  # Enum type

# modules/auth/domain/entities.py
@dataclass
class UserEntity:
    role: Role  # Use same Enum
```

---

## 10. Bounded Contexts Summary

### Auth Context

**Maturity**: 8/10

**Strengths**:
- Clear domain entity
- Repository abstraction
- Service coordination
- Dependency injection

**Weaknesses**:
- Role strings instead of Enum
- Email not a value object
- Password hashing in service, not domain

### TutorProfile Context

**Maturity**: 7/10

**Strengths**:
- Aggregate root pattern
- Protocol-based repository
- Entity composition
- Multi-layer separation

**Weaknesses**:
- HTTPException in infrastructure
- No domain methods on aggregate
- Validation scattered across layers

### Booking Context

**Maturity**: 4/10

**Strengths**:
- Policy engine (good design)
- Service layer exists
- State machine logic

**Weaknesses**:
- No domain aggregate root
- No repository abstraction
- State machine not integrated
- Direct DB access in presentation helpers

### Messaging Context

**Maturity**: 2/10

**Weaknesses**:
- No domain layer
- No application layer
- No repository
- Direct ORM in presentation
- WebSocket tightly coupled

---

## 11. Recommendations (Priority Order)

### CRITICAL (Week 1)

1. **Refactor Messages Module**
   - Create domain entities and aggregate
   - Create application service
   - Create repository abstraction
   - Move business logic from presentation
   - **Effort**: 3-4 days
   - **Impact**: 40% improvement

2. **Remove HTTPException from Infrastructure**
   - Create domain exceptions
   - Map them in presentation layer
   - Update all repositories
   - **Effort**: 2 days
   - **Impact**: Testability ++

3. **Enforce Repository Pattern in Bookings**
   - Create `BookingRepository` interface
   - Extract conflict checking to repository
   - **Effort**: 2-3 days
   - **Impact**: Separation of concerns

### HIGH (Week 2)

4. **Create Booking Aggregate Root**
   - `BookingAggregate` with state machine
   - Integrate with policy engine
   - Domain methods for transitions
   - **Effort**: 3 days
   - **Impact**: Business logic cohesion

5. **Add Domain Events**
   - Create event hierarchy (BookingCreated, Confirmed, etc.)
   - Publish from aggregates
   - Implement event bus
   - **Effort**: 2-3 days
   - **Impact**: Audit trail, notifications

6. **Standardize Logging**
   - Create logging utility
   - Add structured logging (JSON)
   - Document pattern
   - **Effort**: 1 day
   - **Impact**: Ops debugging

### MEDIUM (Week 3)

7. **Use Enums for Roles**
   - Create `Role` enum
   - Update all models
   - **Effort**: 1 day
   - **Impact**: Type safety

8. **Create Value Objects**
   - `Email`, `MoneyAmount`, `TimeSlot`, `MessageContent`
   - Move validation logic
   - **Effort**: 2-3 days
   - **Impact**: Business rule enforcement

9. **Add Domain Services**
   - `PasswordService`, `BookingScheduleValidator`
   - **Effort**: 1-2 days
   - **Impact**: Business logic cohesion

### LOW (Week 4)

10. **Comprehensive Documentation**
    - DDD patterns guide
    - Layer responsibilities
    - Example module structure
    - **Effort**: 1 day

---

## 12. DDD Maturity Scorecard

| Dimension | Score | Status |
|-----------|-------|--------|
| **Module Structure** | 6/10 | Some modules have layers, others missing |
| **Domain Entities** | 6/10 | Auth & TutorProfile good; others weak |
| **Domain Logic** | 4/10 | Scattered across layers |
| **Repositories** | 5/10 | Only Auth & TutorProfile implemented |
| **Application Services** | 5/10 | Auth good; others mixed or missing |
| **Bounded Contexts** | 5/10 | Exist but not enforced |
| **Error Handling** | 6/10 | Consistent in some modules |
| **Logging** | 5/10 | Ad-hoc patterns |
| **Value Objects** | 3/10 | Minimal use |
| **Domain Events** | 1/10 | Not implemented |
| **Dependency Inversion** | 4/10 | Framework code in infra |
| **Transaction Management** | 4/10 | Implicit, no boundaries |
| **Testing Isolation** | 5/10 | Hard to test without full stack |
| **Code Reusability** | 6/10 | Scattered logic duplication |
| **SOLID Principles** | 5/10 | Partial compliance |
| | | |
| **OVERALL** | **5.0/10** | **PARTIAL DDD** |

---

## Conclusion

The codebase has **strong architectural intentions** (clear folder structure, separation attempts) but suffers from **inconsistent execution**. Auth and TutorProfile modules demonstrate proper DDD patterns, while Messages and Bookings violate fundamental principles.

**Next Steps**:
1. Use Auth & TutorProfile as **reference implementations**
2. **Refactor Messages first** (highest impact, lowest complexity)
3. **Create reusable DDD templates** for future modules
4. **Document bounded contexts** and their dependencies
5. **Enforce architectural boundaries** with tests

**Estimated ROI**: 
- 2 weeks of focused refactoring → 40%+ improvement in DDD maturity
- Easier testing, maintenance, and feature addition
- Foundation for scaling to 10+ bounded contexts
