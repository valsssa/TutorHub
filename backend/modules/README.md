# Backend Modules Architecture

This directory contains feature-based modules following DDD-inspired patterns.

## Module Structure Patterns

### Full DDD Structure (recommended for complex domains)

Used by: `auth/`, `tutor_profile/`

```
module_name/
├── domain/          # Domain models, value objects, interfaces
│   ├── entities.py  # Domain entities and aggregates
│   └── interfaces.py # Repository interfaces (abstractions)
├── application/     # Business logic and use cases
│   └── services.py  # Application services
├── infrastructure/  # External concerns implementation
│   └── repositories.py # Repository implementations
├── presentation/    # API layer
│   └── api.py       # FastAPI routes and schemas
└── tests/           # Module tests
```

### Service + Presentation (pragmatic for medium complexity)

Used by: `bookings/`, `packages/`, `notifications/`, `messages/`

```
module_name/
├── services/        # Business logic services
│   └── service.py   # Domain service with business rules
├── presentation/    # API layer
│   └── api.py       # FastAPI routes and schemas
├── schemas.py       # Pydantic schemas (optional)
└── tests/           # Module tests
```

### Presentation Only (for simple CRUD)

Used by: `reviews/`, `subjects/`, `students/`, `favorites/`

```
module_name/
├── presentation/
│   └── api.py       # Routes with inline business logic
└── api.py           # Alternative: direct module-level API
```

## When to Use Each Pattern

### Use Full DDD when:
- Complex business rules that change frequently
- Multiple bounded contexts interact
- Domain experts involved in design
- Long-term maintainability critical

### Use Service + Presentation when:
- Clear business logic but simpler domain
- Need separation for testing
- Moderate complexity
- Growing module that may need full DDD later

### Use Presentation Only when:
- Simple CRUD operations
- Business logic is trivial
- Unlikely to grow in complexity
- Quick delivery needed

## Key Principles

1. **KISS First**: Start with the simplest pattern that works
2. **Evolve When Needed**: Refactor to more layers when complexity demands
3. **Consistency Within Module**: Each module should be internally consistent
4. **Clear Dependencies**: Higher layers depend on lower layers, not vice versa

## Models Location

Domain models live in `/backend/models/` organized by domain:
- `models/auth.py` - User authentication
- `models/tutors.py` - Tutor profiles
- `models/bookings.py` - Sessions and bookings
- `models/students.py` - Student profiles and packages
- etc.

This shared models approach allows cross-module relationships while
keeping modules focused on their bounded context.

## Creating a New Module

1. Determine complexity level
2. Create directory with appropriate structure
3. Add `__init__.py` to each directory
4. Register routes in `main.py`
5. Add tests in `tests/` or module's `tests/` directory

Example minimal module:

```python
# modules/my_feature/api.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.get("/")
async def list_items(db: Session = Depends(get_db)):
    # Implementation
    pass
```

```python
# main.py
from modules.my_feature.api import router as my_feature_router
app.include_router(my_feature_router)
```
