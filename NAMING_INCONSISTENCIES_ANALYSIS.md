# Naming Inconsistencies Analysis - EduStream Platform

**Date:** January 21, 2026  
**Analysis Source:** Database schema (init.sql) as main source of truth  
**Analyzer:** AI Assistant

## Executive Summary

The EduStream platform suffers from significant naming inconsistencies across the database schema and application code. The system has **multiple conflicting approaches** to storing and managing user names, leading to data duplication, sync complexity, and maintenance overhead.

## Core Problem Areas

### 1. Multiple Name Storage Locations

The system stores user names in **4 different locations** with different patterns:

#### A. Users Table (Primary)
```sql
users (
    first_name VARCHAR(100),  -- Individual fields
    last_name VARCHAR(100)
)
```

#### B. User Profiles Table (Extended)
```sql
user_profiles (
    first_name VARCHAR(100),  -- Duplicate of users.first_name
    last_name VARCHAR(100)    -- Duplicate of users.last_name
)
```

#### C. Student Profiles Table (Role-specific)
```sql
student_profiles (
    first_name VARCHAR(100),  -- Duplicate of users.first_name
    last_name VARCHAR(100)    -- Duplicate of users.last_name
)
```

#### D. Booking Snapshots (Immutable)
```sql
bookings (
    tutor_name VARCHAR(200),    -- Concatenated: "First Last"
    student_name VARCHAR(200)   -- Concatenated: "First Last"
)
```

### 2. Inconsistent Naming Patterns

The codebase uses **three different approaches** to name fields:

1. **Split names**: `first_name`, `last_name` (users, profiles)
2. **Concatenated names**: `tutor_name`, `student_name` (bookings)
3. **Display names**: `name`, `full_name` (various contexts)

### 3. Data Synchronization Issues

The application code contains **manual sync logic** between tables:

#### In `backend/modules/students/presentation/api.py`:
```python
# Sync first_name and last_name to User table for display in tutor cards and messages
if "first_name" in update_fields or "last_name" in update_fields:
    if "first_name" in update_fields:
        user.first_name = update_fields["first_name"]
    if "last_name" in update_fields:
        user.last_name = update_fields["last_name"]
```

#### In `backend/modules/profiles/presentation/api.py`:
```python
# Sync first_name and last_name to User table for display in tutor cards and messages
if "first_name" in update_data or "last_name" in update_data:
    if "first_name" in update_data:
        user.first_name = update_data["first_name"]
    if "last_name" in update_data:
        user.last_name = update_data["last_name"]
```

#### In `backend/modules/tutor_profile/infrastructure/repositories.py`:
```python
# Sync first_name and last_name to User table for display in tutor cards and messages
if first_name is not None or last_name is not None:
    if first_name is not None:
        user.first_name = first_name.strip()
    if last_name is not None:
        user.last_name = last_name.strip()
```

## Detailed Findings by Component

### Database Schema Issues

#### Tables with Duplicate Name Fields
1. **`users`** - Primary name storage
2. **`user_profiles`** - Extended profile (duplicate)
3. **`student_profiles`** - Student-specific profile (duplicate)
4. **`tutor_profiles`** - No name fields (uses users.first_name/last_name)

#### Inconsistent Field Naming
- **Split approach**: `first_name`, `last_name` (3 tables)
- **Concatenated approach**: `tutor_name`, `student_name` (bookings table)
- **Subject naming**: `subject_name` (bookings) vs `name` (subjects table)

#### Index Duplication
```sql
-- Users table indexes
CREATE INDEX idx_users_first_name ON users(first_name);
CREATE INDEX idx_users_last_name ON users(last_name);
CREATE INDEX idx_users_full_name ON users(first_name, last_name);

-- Student profiles indexes (duplicate functionality)
CREATE INDEX idx_student_profiles_first_name ON student_profiles(first_name);
CREATE INDEX idx_student_profiles_last_name ON student_profiles(last_name);
```

### Application Code Issues

#### Backend Service Layer
**File:** `backend/modules/bookings/service.py`

**Issue:** Manual concatenation of names for snapshots:
```python
tutor_name=f"{tutor_profile.user.profile.first_name or ''} {tutor_profile.user.profile.last_name or ''}".strip()
student_name=f"{student.profile.first_name or ''} {student.profile.last_name or ''}".strip()
```

**Issue:** Inconsistent profile access patterns:

**Line 149-152 (booking creation):**
```python
tutor_name=f"{tutor_profile.user.profile.first_name or ''} {tutor_profile.user.profile.last_name or ''}".strip()
or tutor_profile.user.email,
student_name=f"{student.profile.first_name or ''} {student.profile.last_name or ''}".strip()
or student.email,
```

**Line 453-474 (booking retrieval):**
```python
tutor_name = booking.tutor_name or (
    f"{tutor_user_profile.first_name or ''} {tutor_user_profile.last_name or ''}".strip()
)
student_name = booking.student_name or (
    f"{student_profile.first_name or ''} {student_profile.last_name or ''}".strip()
)
```

**Issue:** Different fallback patterns - sometimes uses `user.profile.first_name`, sometimes uses `user.first_name` directly, sometimes falls back to email.

#### Schema Definitions
**File:** `backend/schemas.py`

**Inconsistent field definitions and validation:**
```python
# User creation schema (REQUIRED fields)
first_name: str = Field(..., min_length=1, max_length=100)
last_name: str = Field(..., min_length=1, max_length=100)

# User response schema (OPTIONAL fields)
first_name: str | None = None
last_name: str | None = None

# User profile update schema (OPTIONAL)
first_name: str | None = None
last_name: str | None = None

# User profile response schema (OPTIONAL)
first_name: str | None
last_name: str | None

# Student profile create/update schema (OPTIONAL with validation)
first_name: str | None = Field(None, min_length=1, max_length=100)
last_name: str | None = Field(None, min_length=1, max_length=100)

# Booking response schema (concatenated names)
tutor_name: str | None = None
student_name: str | None = None
```

**Issue:** Same logical field (`first_name`) has different validation rules across schemas - sometimes required, sometimes optional, sometimes with length limits, sometimes without.

#### Frontend Type Definitions
**File:** `frontend/types/index.ts`

**Mixed naming patterns across interfaces:**

```typescript
// User/UserProfile types (split names)
interface User {
  first_name?: string | null;
  last_name?: string | null;
}

// Booking type (concatenated names)
interface Booking {
  tutor_name?: string;      // "First Last"
  student_name?: string;    // "First Last"
  subject_name?: string;    // Subject name
}

// Message type (split names for other user)
interface Message {
  other_user_first_name?: string | null;
  other_user_last_name?: string | null;
}
```

#### Admin Dashboard Usage
**File:** `frontend/app/admin/page.tsx`

**Uses concatenated booking snapshot names:**
```typescript
// Line 137-138
student: s.student_name || 'Unknown',
tutor: s.tutor_name || 'Unknown',
```

#### Review Page Mapping Issues
**File:** `frontend/app/bookings/[id]/review/page.tsx`

**Inconsistent mapping between DTO and legacy types:**
```typescript
// Line 61
tutor_name: bookingData.tutor.name,  // Maps DTO 'name' to 'tutor_name'
```

**Issue:** Frontend expects `tutor_name` field but backend provides `tutor.name` in DTO.

### Migration History Issues

#### Migration 003: Add User Names
```sql
-- Added to users table
first_name VARCHAR(100),
last_name VARCHAR(100)
```

#### Migration 019: Add Student Profile Fields
```sql
-- Duplicate fields added to student_profiles
first_name VARCHAR(100),
last_name VARCHAR(100)
```

#### Migration 011: Immutable Booking Snapshots
```sql
-- Concatenated names for immutability
tutor_name VARCHAR(200),
student_name VARCHAR(200)
```

#### Migration 019: Student Profile Fields (DUPLICATE)
```sql
-- Added duplicate name fields to student_profiles
first_name VARCHAR(100),
last_name VARCHAR(100)
```

### Seed Data Inconsistencies

#### Student Creation (Profile-centric)
**File:** `backend/seed_data.py`

**Pattern:** Names stored in `StudentProfile` table only:
```python
profile = StudentProfile(
    user_id=user.id,
    first_name=first_name,  # Stored in profile table
    last_name=last_name,    # Stored in profile table
    ...
)
```

#### Tutor Creation (User table empty)
**Issue:** Tutors created without names in users table:
```python
user = User(
    email=email,
    hashed_password=get_password_hash("tutor123"),
    role="tutor",
    is_verified=True,
    # first_name and last_name NOT SET
)
```

**Result:** Tutor names exist only in profile relationships, not directly on User records.

## Data Integrity Risks

### 1. Synchronization Failures
- Manual sync code can fail
- Race conditions between updates
- Partial updates leaving inconsistent state

### 2. Data Inconsistency
- Names can differ between `users` and profile tables
- Booking snapshots may contain outdated names
- Display logic may show wrong names in different contexts

### 3. Performance Impact
- Multiple indexes on same logical data
- Complex queries joining multiple name sources
- Application-level concatenation overhead

## Recommended Solutions

### Option 1: Single Source of Truth (Recommended)
1. **Remove duplicate name fields** from profile tables
2. **Use only `users.first_name`, `users.last_name`** as source of truth
3. **Keep booking snapshots** for immutability
4. **Update all application code** to use single source

### Option 2: Profile-Centric Approach
1. **Remove names from users table**
2. **Use profile tables as source of truth**
3. **Keep sync logic** but make it automatic via triggers
4. **Standardize on split names** everywhere

### Option 3: Hybrid Approach
1. **Keep users table** for core auth
2. **Use computed columns** for concatenated names
3. **Eliminate manual sync** with database triggers
4. **Standardize naming patterns** across all contexts

## Impact Assessment

### Breaking Changes Required
- **High**: Database schema changes
- **High**: API response format changes
- **Medium**: Frontend type updates
- **Low**: UI component updates

### Migration Complexity
- **Data migration**: Consolidate duplicate name data
- **Code migration**: Update 50+ files with name references
- **Test migration**: Update all test fixtures and assertions

### Business Risk
- **User experience**: Potential display inconsistencies during migration
- **Data integrity**: Risk of name data loss during consolidation
- **Application stability**: Extensive code changes increase bug risk

## Immediate Action Items

### Phase 1: Analysis & Planning (Week 1)
1. **Audit all name usage** across codebase (COMPLETED)
2. **Document data dependencies** and usage patterns
3. **Choose consolidation strategy** (recommend Option 1)
4. **Plan migration steps** with rollback procedures

### Phase 2: Database Migration (Week 2)
1. **Create backup** of all name-related data
2. **Implement chosen consolidation** approach
3. **Migrate existing data** preserving all names
4. **Update indexes** removing duplicates

### Phase 3: Application Updates (Weeks 3-4)
1. **Update backend schemas** and models
2. **Modify service layer** logic
3. **Update API endpoints** and responses
4. **Fix frontend types** and components

### Phase 4: Testing & Deployment (Weeks 5-6)
1. **Update all tests** with new naming patterns
2. **Perform integration testing** across all features
3. **Gradual rollout** with feature flags
4. **Monitor for issues** post-deployment

## Files Requiring Updates (50+ files)

### Backend Files
- `backend/schemas.py` - Schema definitions
- `backend/models/auth.py` - User model
- `backend/models/students.py` - Student model
- `backend/modules/bookings/service.py` - Business logic
- `backend/modules/*/presentation/api.py` - API endpoints
- `backend/modules/*/infrastructure/repositories.py` - Data access

### Frontend Files
- `frontend/types/index.ts` - Type definitions
- `frontend/components/TutorCard.tsx` - Display logic
- `frontend/components/TutorProfileView.tsx` - Profile display
- `frontend/app/*/page.tsx` - Page components

### Database Files
- `database/init.sql` - Schema definition
- `database/migrations/` - Migration scripts

## Critical Files Requiring Immediate Attention

### Backend Files (High Priority)
1. **`backend/schemas.py`** - Standardize field validation across all schemas
2. **`backend/modules/bookings/service.py`** - Fix inconsistent profile access patterns
3. **`backend/seed_data.py`** - Ensure tutors get names in users table

### Frontend Files (High Priority)
1. **`frontend/types/index.ts`** - Align naming patterns across interfaces
2. **`frontend/app/bookings/[id]/review/page.tsx`** - Fix DTO mapping inconsistencies
3. **`frontend/app/admin/page.tsx`** - Ensure proper name field usage

### Database Files (Migration Required)
1. **`database/init.sql`** - Remove duplicate indexes and fields
2. **Migration scripts** - Consolidate name data to single source

## Updated Impact Assessment

### Breaking Changes (Expanded)
- **Schema validation changes** - API request validation will change
- **Type definition updates** - Frontend components need type fixes
- **DTO mapping fixes** - Review page and admin dashboard affected
- **Seed data corrections** - Tutor creation needs user table names

### Files Needing Updates (Now 60+ files)
- **Backend:** 15+ schema/model/service files
- **Frontend:** 10+ component/page/type files
- **Database:** 5+ migration/schema files
- **Tests:** 20+ test files with fixture updates

## Conclusion

The naming inconsistencies represent a **significant architectural debt** that affects maintainability, performance, and data integrity. While the current system "works," it creates unnecessary complexity and risk.

**Recommendation:** Implement Option 1 (Single Source of Truth) to consolidate names in the `users` table only, eliminating duplicates and manual sync logic while maintaining booking immutability through snapshots.

**Immediate Action:** Start with the 6 critical files listed above before broader migration.

## Specific Patterns to Fix

### 1. Profile Access Inconsistencies
**Current (broken):**
```python
# Inconsistent access patterns
tutor_profile.user.profile.first_name  # Deep relationship
student.profile.first_name             # Direct relationship
tutor_user_profile.first_name          # Direct from user
```

**Target (consistent):**
```python
# Single pattern for all name access
user.first_name    # Always from users table
user.last_name     # Always from users table
```

### 2. Concatenation Logic Duplication
**Current (duplicated in 3+ places):**
```python
f"{first_name or ''} {last_name or ''}".strip() or email
```

**Target (centralized):**
```python
# Single utility function for name formatting
def format_display_name(first_name, last_name, fallback=None):
    if first_name or last_name:
        return f"{first_name or ''} {last_name or ''}".strip()
    return fallback
```

### 3. Schema Validation Inconsistencies
**Current (inconsistent):**
```python
first_name: str = Field(..., min_length=1, max_length=100)      # Required
first_name: str | None = None                                   # Optional
first_name: str | None = Field(None, min_length=1, max_length=100)  # Optional with validation
```

**Target (consistent):**
```python
# Standardize on optional with validation where needed
first_name: str | None = Field(None, min_length=1, max_length=100)
last_name: str | None = Field(None, min_length=1, max_length=100)
```

## Code Examples: Problems vs Solutions

### Problem: Inconsistent Profile Access
```python
# PROBLEMATIC CODE (from bookings service)
tutor_name = f"{tutor_profile.user.profile.first_name or ''} {tutor_profile.user.profile.last_name or ''}".strip()
student_name = f"{student.profile.first_name or ''} {student.profile.last_name or ''}".strip()

# SOLUTION: Consistent access
tutor_name = f"{tutor_profile.user.first_name or ''} {tutor_profile.user.last_name or ''}".strip()
student_name = f"{student.first_name or ''} {student.last_name or ''}".strip()
```

### Problem: Duplicate Sync Logic
```python
# PROBLEMATIC CODE (scattered across multiple files)
if "first_name" in update_fields:
    user.first_name = update_fields["first_name"]
if "last_name" in update_fields:
    user.last_name = update_fields["last_name"]

# SOLUTION: Single sync function
def sync_user_names_from_profile(user: User, profile_data: dict):
    """Centralized name sync logic."""
    if "first_name" in profile_data:
        user.first_name = profile_data["first_name"]
    if "last_name" in profile_data:
        user.last_name = profile_data["last_name"]
```

### Problem: Mixed Frontend Types
```typescript
// PROBLEMATIC TYPES
interface User {
  first_name?: string | null;  // Split
  last_name?: string | null;
}

interface Booking {
  tutor_name?: string;         // Concatenated
  student_name?: string;
}

// SOLUTION: Consistent patterns
interface User {
  firstName?: string | null;   // camelCase
  lastName?: string | null;
}

interface Booking {
  tutorName?: string;          // camelCase concatenated
  studentName?: string;
}
```

---

*This analysis was generated by examining the database schema as the authoritative source of truth, then tracing naming usage patterns across the entire codebase.*