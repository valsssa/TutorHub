# Database Architecture - Pure Data Storage

## Core Principle: "No Logic in Database"

**ALL business logic resides in the application layer. The database is ONLY for data storage.**

## Architecture Summary

### Database Responsibilities (ONLY)
- Store data with proper constraints and indexes
- Enforce referential integrity (foreign keys)
- Provide default values (`DEFAULT`, `server_default`)
- Ensure data types and constraints (`NOT NULL`, `CHECK`)

### Application Code Responsibilities (ALL LOGIC)
- Update `updated_at` timestamps on every record modification
- Enforce role-profile consistency
- Validate booking conflicts
- Create booking snapshots before saving
- Auto-confirm instant bookings
- Track package usage
- Maintain tutor profile history
- Generate audit logs
- All business rules and validations

## Implementation Details

### 1. Timestamp Management

**In Database (`database/init.sql`):**
```sql
-- Only default value on insert
updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
```

**In SQLAlchemy Models:**
```python
# No onupdate - handled in application code
updated_at = Column(
    TIMESTAMP(timezone=True),
    server_default=func.now(),
    # No onupdate - updated_at is set in application code
    nullable=False,
)
```

**In Application Code:**
```python
from datetime import datetime, timezone

# Every update must explicitly set updated_at
message.content = new_content
message.updated_at = datetime.now(timezone.utc)  # <-- Required!
db.commit()
```

### 2. Files Modified for "No DB Logic" Compliance

#### Models (Removed `onupdate=func.now()`):
- `backend/models/messages.py` - Message model
- `backend/models/auth.py` - User, UserProfile models
- `backend/models/bookings.py` - Booking model
- `backend/models/tutors.py` - TutorProfile, Certification, Education, PricingOption
- `backend/models/students.py` - StudentProfile, StudentPackage
- `backend/models/payments.py` - Payment, TutorPayout

#### Services (Added explicit `updated_at` setting):
- `backend/modules/messages/service.py`
  - `send_message()` - Sets updated_at on new message
  - `edit_message()` - Sets updated_at on edit
  - `delete_message()` - Sets updated_at on soft delete
  - `mark_message_read()` - Sets updated_at when marking read
  - `mark_thread_read()` - Sets updated_at in bulk update

- `backend/modules/profiles/presentation/api.py`
  - `update_my_profile()` - Sets updated_at on profile update

- `backend/modules/students/presentation/api.py`
  - `update_student_profile()` - Sets updated_at on profile update

- `backend/modules/tutor_profile/infrastructure/repositories.py`
  - `update_description()` - Sets updated_at on tutor profile
  - `update_video()` - Sets updated_at on tutor profile
  - `update_profile_photo()` - Sets updated_at on both User and TutorProfile
  - `update_pricing()` - Sets updated_at after pricing changes
  - `replace_availability()` - Sets updated_at after availability update

- `backend/modules/bookings/presentation/api.py`
  - `confirm_booking()` - Sets updated_at when confirming

- `backend/modules/admin/presentation/api.py`
  - `update_user()` - Sets updated_at on user changes

#### Database Schema (`database/init.sql`):
- Removed all `CREATE FUNCTION` statements
- Removed all `CREATE TRIGGER` statements
- Added documentation explaining the architecture

### 3. Migration Path

For existing databases, the transition is seamless:
1. Database triggers/functions are removed (or simply not created on fresh install)
2. Application code now handles all timestamp updates
3. No data migration needed - only code changes

### 4. Benefits of This Architecture

✅ **Simplicity**: All logic in one place (application code)
✅ **Testability**: Business logic can be unit tested without database
✅ **Portability**: Works across different database systems
✅ **Debuggability**: Full control and visibility in application logs
✅ **Version Control**: All logic tracked in Git, not hidden in DB
✅ **Maintainability**: Developers only need to know Python, not PL/pgSQL

### 5. Testing

All services with database updates should be tested to ensure:
```python
def test_message_edit_updates_timestamp():
    """Verify updated_at is set in application code."""
    old_timestamp = message.updated_at
    time.sleep(0.01)
    
    service.edit_message(message.id, user.id, "New content")
    
    assert message.updated_at > old_timestamp
```

### 6. Code Review Checklist

When adding new database update code, verify:
- [ ] `updated_at` is explicitly set before `db.commit()`
- [ ] No new database functions or triggers are added
- [ ] Business logic is in service layer, not database
- [ ] Unit tests verify timestamp updates
- [ ] Logging captures the business decision

## Common Patterns

### Pattern 1: Single Record Update
```python
def update_entity(entity_id: int, new_data: dict):
    from datetime import datetime, timezone
    
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    for key, value in new_data.items():
        setattr(entity, key, value)
    
    entity.updated_at = datetime.now(timezone.utc)  # Always set!
    db.commit()
    db.refresh(entity)
    return entity
```

### Pattern 2: Bulk Update
```python
def mark_all_read(user_id: int):
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    count = db.query(Message).filter(...).update(
        {"is_read": True, "read_at": now, "updated_at": now},  # Include updated_at!
        synchronize_session=False
    )
    db.commit()
    return count
```

### Pattern 3: Soft Delete
```python
def soft_delete_entity(entity_id: int, user_id: int):
    from datetime import datetime, timezone
    
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    entity.deleted_at = datetime.now(timezone.utc)
    entity.deleted_by = user_id
    entity.updated_at = datetime.now(timezone.utc)  # Also update!
    db.commit()
    return entity
```

## Historical Context

**Previous Architecture (Before Refactor):**
- Database had multiple functions and triggers
- `updated_at` managed by PostgreSQL trigger
- Business logic split between application and database
- Hard to test and debug

**Current Architecture (After Refactor):**
- Pure data storage in database
- All logic in application code
- Single source of truth for business rules
- Full control and visibility

---

**Last Updated:** 2025-11-12  
**Architecture Version:** 2.0 (Pure Data Storage)
