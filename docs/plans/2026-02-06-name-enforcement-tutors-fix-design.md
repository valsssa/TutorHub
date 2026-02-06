# Name Enforcement & Tutors Page Fix Design

**Date:** 2026-02-06
**Status:** Approved for implementation

## Overview

Two related issues need fixing:
1. First/last names not enforced everywhere - OAuth users can have incomplete profiles
2. Tutors page has bugs - missing fields, broken display names, no avatars

## Part A: Name Enforcement

### A1. Add `require_complete_profile` dependency

**File:** `backend/core/dependencies.py`

Add new dependency that checks `profile_incomplete` flag:
```python
async def require_complete_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to have complete profile (first_name and last_name)."""
    if current_user.profile_incomplete or not current_user.first_name or not current_user.last_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Please complete your profile before continuing",
                "code": "PROFILE_INCOMPLETE",
                "redirect": "/settings/profile"
            }
        )
    return current_user
```

### A2. Apply to protected endpoints

**Files to modify:**
- `backend/modules/bookings/presentation/api.py` - POST /bookings
- `backend/modules/messages/presentation/api.py` - POST /messages
- `backend/modules/favorites/api.py` - POST /favorites

Replace `get_current_user` with `require_complete_profile` for create operations.

### A3. Fix UserSelfUpdate validation

**File:** `backend/schemas.py`

Update `UserSelfUpdate` to prevent clearing names:
- Add validator that checks if user already has names set
- Reject empty/null values if names were previously set

### A4. Tutor profile validation

Tutors must have complete names before approval. Add check to tutor approval process.

## Part B: Tutors Page Fixes

### B1. Add currency to TutorPublicProfile

**File:** `backend/schemas.py`

```python
class TutorPublicProfile(BaseModel):
    # ... existing fields
    currency: str = Field(default="USD")  # Add this
```

### B2. Populate first_name/last_name in serialization

**File:** `backend/modules/tutor_profile/application/dto.py`

Ensure `aggregate_to_public_profile()` includes user's first/last name from the User model.

### B3. Fix profile_photo_url

**File:** `backend/models/tutors.py`

Replace placeholder with actual avatar URL retrieval:
```python
@property
def profile_photo_url(self) -> str | None:
    """Get tutor's profile photo URL from user's avatar."""
    if self.user and self.user.avatar_key:
        # Return URL from avatar storage
        return f"/api/v1/avatars/{self.user.avatar_key}"
    return None
```

### B4. Update tutor API to include names

**File:** `backend/modules/tutors/api.py`

Ensure tutor list endpoint includes first_name, last_name from related User.

## Implementation Order

1. Backend: Add `require_complete_profile` dependency
2. Backend: Fix `TutorPublicProfile` schema (add currency, ensure names)
3. Backend: Fix `profile_photo_url` property
4. Backend: Apply profile check to bookings/messages/favorites
5. Frontend: Verify tutors page works with fixed backend

## Files Changed

- `backend/core/dependencies.py`
- `backend/schemas.py`
- `backend/models/tutors.py`
- `backend/modules/bookings/presentation/api.py`
- `backend/modules/messages/presentation/api.py`
- `backend/modules/favorites/api.py`
- `backend/modules/tutors/api.py`
