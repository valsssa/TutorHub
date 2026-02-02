# Backend Modules Architecture

This directory contains feature-based modules following Clean Architecture and DDD-inspired patterns.

## Module Structure Overview

The codebase uses three architectural patterns based on module complexity:

| Pattern | Complexity | Layers | Use When |
|---------|------------|--------|----------|
| **Full DDD** | High | domain, application, infrastructure, presentation | Complex business rules, state machines, multiple integrations |
| **Service + Presentation** | Medium | domain, services, presentation | Clear business logic, moderate complexity |
| **Presentation Only** | Low | domain (optional), presentation/api | Simple CRUD, minimal business rules |

### Choosing the Right Pattern

**Full DDD** - Use for:
- Complex business rules that change frequently
- Modules with state machines or workflows
- Multiple external integrations requiring abstraction
- Long-term maintainability is critical
- Domain experts involved in design

**Service + Presentation** - Use for:
- Clear business logic but simpler domain
- Need separation for testing
- Growing module that may need full DDD later
- Moderate external dependencies

**Presentation Only** - Use for:
- Simple CRUD operations
- Business logic is trivial
- Unlikely to grow in complexity
- Quick delivery needed

---

## Standard Directory Structure

### Full DDD Module

```
modules/example/
├── domain/
│   ├── __init__.py
│   ├── entities.py       # Pure data classes (dataclasses)
│   ├── value_objects.py  # Immutable primitives with validation
│   ├── repositories.py   # Protocol interfaces (abstractions)
│   ├── exceptions.py     # Domain-specific exceptions
│   └── state_machine.py  # State transition logic (if applicable)
├── application/
│   ├── __init__.py
│   ├── services.py       # Use cases / application services
│   └── dto.py            # Data Transfer Objects
├── infrastructure/
│   ├── __init__.py
│   └── repositories.py   # SQLAlchemy implementations of domain protocols
├── presentation/
│   ├── __init__.py
│   └── api.py            # FastAPI routes and request/response schemas
└── tests/
    ├── __init__.py
    └── test_*.py         # Unit and integration tests
```

### Service + Presentation Module

```
modules/example/
├── domain/
│   ├── __init__.py
│   ├── entities.py       # Domain entities (optional)
│   └── exceptions.py     # Domain exceptions (optional)
├── services/
│   ├── __init__.py
│   └── service.py        # Business logic services
├── presentation/
│   ├── __init__.py
│   └── api.py            # FastAPI routes
├── schemas.py            # Pydantic schemas (optional)
└── tests/
    └── __init__.py
```

### Presentation Only Module

```
modules/example/
├── domain/
│   └── __init__.py       # Minimal domain (enums, simple entities)
├── presentation/
│   └── api.py            # Routes with inline business logic
├── api.py                # Alternative: direct module-level API file
└── tests/
    └── __init__.py
```

---

## Module Inventory

| Module | Pattern | Layers | Status | Description |
|--------|---------|--------|--------|-------------|
| **tutor_profile** | Full DDD | domain, application, infrastructure, presentation | Complete | Tutor profile management |
| **auth** | Full DDD | domain, application, infrastructure, presentation, services | Complete | Authentication, OAuth, password management |
| **bookings** | Service + Domain | domain, services, presentation | Complete | Session booking with state machine |
| **packages** | Service + Presentation | domain, services, presentation | Complete | Student session packages |
| **notifications** | Service + Presentation | domain, presentation | Complete | Notification delivery |
| **messages** | Service + Presentation | domain | Complete | Real-time messaging, WebSocket |
| **payments** | Presentation Only | domain | Complete | Stripe payments, wallet |
| **integrations** | Presentation Only | domain | Complete | Calendar, Zoom video |
| **admin** | Presentation Only | domain, presentation, audit, owner | Complete | Admin panel, feature flags |
| **users** | Presentation Only | domain, avatar, currency, preferences | Complete | User settings sub-modules |
| **students** | Presentation Only | domain, presentation | Complete | Student profiles |
| **subjects** | Presentation Only | domain, presentation | Complete | Subject management |
| **reviews** | Presentation Only | domain, presentation | Complete | Session reviews |
| **favorites** | Presentation Only | domain | Complete | Favorite tutors |
| **profiles** | Presentation Only | domain, presentation | Complete | Public profile views |
| **public** | Presentation Only | domain | Complete | Public endpoints |
| **tutors** | Presentation Only | domain | Complete | Tutor-specific features (notes, video settings) |
| **utils** | Presentation Only | domain, presentation | Complete | Utility endpoints (health, time) |

---

## Key Conventions

### 1. No SQLAlchemy in Domain Layer

The domain layer must remain pure and framework-agnostic:

```python
# domain/entities.py - CORRECT
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TutorProfile:
    id: str
    user_id: str
    bio: str
    hourly_rate: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# domain/entities.py - WRONG
from sqlalchemy import Column, String  # Never import SQLAlchemy in domain
```

### 2. Use Protocol for Repository Interfaces

Define interfaces in domain, implement in infrastructure:

```python
# domain/repositories.py
from typing import Protocol, Optional
from .entities import TutorProfile

class TutorProfileRepository(Protocol):
    """Repository interface - no implementation details."""

    def get_by_id(self, profile_id: str) -> Optional[TutorProfile]:
        ...

    def get_by_user_id(self, user_id: str) -> Optional[TutorProfile]:
        ...

    def save(self, profile: TutorProfile) -> TutorProfile:
        ...

# infrastructure/repositories.py
from sqlalchemy.orm import Session
from models.tutors import TutorProfileModel
from ..domain.entities import TutorProfile
from ..domain.repositories import TutorProfileRepository

class SqlAlchemyTutorProfileRepository:
    """Concrete implementation using SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, profile_id: str) -> Optional[TutorProfile]:
        model = self.db.query(TutorProfileModel).filter_by(id=profile_id).first()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: TutorProfileModel) -> TutorProfile:
        return TutorProfile(
            id=str(model.id),
            user_id=str(model.user_id),
            bio=model.bio,
            hourly_rate=model.hourly_rate,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

### 3. Use Dataclasses for Domain Entities

Keep entities simple and immutable when possible:

```python
# domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass(frozen=True)  # Immutable value object
class Money:
    amount: int
    currency: str = "USD"

@dataclass
class TutorProfile:
    id: str
    user_id: str
    bio: str
    hourly_rate: Money
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### 4. Dependency Injection via FastAPI Depends

Wire up dependencies in the presentation layer:

```python
# presentation/api.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from ..application.services import TutorProfileService
from ..infrastructure.repositories import SqlAlchemyTutorProfileRepository

router = APIRouter(prefix="/tutor-profile", tags=["tutor-profile"])

def get_tutor_profile_service(db: Session = Depends(get_db)) -> TutorProfileService:
    repository = SqlAlchemyTutorProfileRepository(db)
    return TutorProfileService(repository)

@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    service: TutorProfileService = Depends(get_tutor_profile_service)
):
    return service.get_profile(profile_id)
```

### 5. Router Registration

Router prefixes should NOT include `/api` - this is added centrally:

```python
# modules/my_feature/presentation/api.py
router = APIRouter(prefix="/my-feature", tags=["my-feature"])

# main.py
from modules.my_feature.presentation.api import router as my_feature_router

API_V1_PREFIX = "/api/v1"
app.include_router(my_feature_router, prefix=API_V1_PREFIX)
```

---

## Best Example Modules

For reference implementations, examine these modules:

### Full DDD: `tutor_profile/`

The cleanest example of full clean architecture:
- **domain/entities.py** - Pure dataclass entities
- **domain/value_objects.py** - Immutable value types with validation
- **domain/repositories.py** - Protocol-based interfaces
- **domain/exceptions.py** - Domain-specific errors
- **application/services.py** - Use cases orchestrating domain logic
- **application/dto.py** - Data transfer objects
- **infrastructure/repositories.py** - SQLAlchemy implementations
- **presentation/api.py** - FastAPI routes with dependency injection

### Full DDD with State Machine: `auth/`

Demonstrates complex authentication flows:
- Multiple sub-routers (oauth, password)
- Domain entities for users and sessions
- Infrastructure for token storage
- Services layer for specialized auth logic (fraud detection)

### Domain-Heavy with State Machine: `bookings/`

Demonstrates complex state management:
- **domain/status.py** - Four-field status system (SessionState, SessionOutcome, PaymentState, DisputeState)
- **domain/state_machine.py** - BookingStateMachine enforcing valid transitions
- **jobs.py** - Background jobs for auto-transitions (expire, start, end)
- **policy_engine.py** - Cancellation and refund policies

---

## Creating a New Module

1. **Assess complexity** - Determine which pattern fits
2. **Create directory structure** - Use appropriate template above
3. **Add `__init__.py` files** - To each directory
4. **Implement domain first** - If using DDD, start with entities and interfaces
5. **Register routes in `main.py`** - With API v1 prefix
6. **Add tests** - In module's `tests/` directory

### Quick Start Template

```bash
# Create a new Service + Presentation module
mkdir -p backend/modules/my_feature/{domain,services,presentation,tests}
touch backend/modules/my_feature/__init__.py
touch backend/modules/my_feature/domain/__init__.py
touch backend/modules/my_feature/services/__init__.py
touch backend/modules/my_feature/presentation/__init__.py
touch backend/modules/my_feature/tests/__init__.py
```

---

## Models Location

ORM models live in `/backend/models/` organized by domain:
- `models/auth.py` - User authentication
- `models/tutors.py` - Tutor profiles
- `models/bookings.py` - Sessions and bookings
- `models/students.py` - Student profiles and packages

This shared models approach allows cross-module relationships while keeping modules focused on their bounded context. Domain entities in modules map to/from these ORM models via repositories.

---

## Key Principles

1. **KISS First** - Start with the simplest pattern that works
2. **Evolve When Needed** - Refactor to more layers when complexity demands
3. **Consistency Within Module** - Each module should be internally consistent
4. **Clear Dependencies** - Higher layers depend on lower layers, not vice versa
5. **Domain Purity** - Domain layer has no external dependencies
6. **Testability** - Use protocols/interfaces to enable mocking
