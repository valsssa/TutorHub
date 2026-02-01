# User Identity Contract

This document defines the requirements, validations, and display rules for user identity fields in EduConnect.

## Overview

All registered users in EduConnect MUST have both a first name and last name. This ensures:
- Personalized user experience
- Clear identification in communications
- Professional appearance in tutor-student interactions
- Consistent display across the platform

## Required Fields

### first_name
- **Type**: String
- **Required**: Yes (for complete profile)
- **Min Length**: 1 character (after trim)
- **Max Length**: 100 characters
- **Validation**:
  - Must be non-empty after trimming
  - Whitespace-only strings are rejected
  - Automatically trimmed on save

### last_name
- **Type**: String
- **Required**: Yes (for complete profile)
- **Min Length**: 1 character (after trim)
- **Max Length**: 100 characters
- **Validation**:
  - Must be non-empty after trimming
  - Whitespace-only strings are rejected
  - Automatically trimmed on save

### full_name (computed)
- **Type**: String (computed field)
- **Format**: `"{first_name} {last_name}"`
- **Computed**: Server-side in API responses
- **Note**: Read-only, not stored in database

### profile_incomplete
- **Type**: Boolean
- **Default**: FALSE
- **Purpose**: Indicates user needs to complete profile (missing names)
- **Set TRUE when**:
  - OAuth user created without names from provider
  - Legacy user missing names after migration
- **Set FALSE when**:
  - User provides both first_name and last_name

## Enforcement Points

### Registration (Email/Password)
- Both first_name and last_name are required
- Validation in `UserCreate` schema (backend/schemas.py)
- Frontend form validation (register/page.tsx)

### OAuth/Social Login
- Names extracted from provider (e.g., Google's given_name/family_name)
- If provider doesn't supply names:
  - User created with `profile_incomplete=TRUE`
  - User redirected to Complete Profile page on first login
  - User cannot access protected routes until profile is complete

### Profile Updates
- Names cannot be cleared once set
- Empty/whitespace-only values rejected
- Validation in `UserSelfUpdate` schema

### Admin-Created Users
- Admin UI must collect both names
- Same validation rules apply

## Display Rules

### Where Full Name MUST Appear

1. **Navbar/Header**
   - User dropdown: Full name as primary, email as secondary
   - Avatar tooltip: Full name

2. **Dashboards**
   - Greeting: "Welcome, {first_name}"
   - Profile card: Full name

3. **Profile Pages**
   - Account settings: Full name displayed
   - Public tutor profile: Full name

4. **Messages**
   - Thread list: Participant names
   - Message headers: Sender name

5. **Bookings**
   - Booking cards: Tutor/student names
   - Calendar events: Participant names

6. **Admin Views**
   - User lists: Full name column
   - User details: Full name header

### Fallback Behavior

For legacy users with incomplete profiles during migration:
1. Show email as temporary display name
2. Show warning banner prompting profile completion
3. Block access to protected routes until complete

### Display Name Utility

Use the centralized utility for consistent formatting:

```typescript
// Frontend (lib/displayName.ts)
import { getDisplayName, getGreetingName, formatFullName } from '@/lib/displayName';

// Full name for display
const name = getDisplayName(user); // "John Doe"

// First name for greetings
const greeting = getGreetingName(user); // "John"

// Format from separate fields
const full = formatFullName(firstName, lastName); // "John Doe"
```

```python
# Backend (core/utils.py)
from core.utils import StringUtils

name = StringUtils.format_display_name(first_name, last_name, fallback)
```

## Migration Plan

### Existing Users with Missing Names

1. **Identification**
   - Query: Users where first_name IS NULL OR last_name IS NULL
   - Migration 043 marks these as `profile_incomplete=TRUE`

2. **Enforcement**
   - Users with `profile_incomplete=TRUE` see CompleteProfile gate
   - Cannot access protected routes until names provided
   - No data loss - existing email/auth preserved

3. **Rollout Steps**
   1. Deploy migration 043 (adds column, marks incomplete users)
   2. Deploy updated API (returns profile_incomplete in responses)
   3. Deploy frontend (CompleteProfile component)
   4. Monitor incomplete profile completion rate

### Database Migration

File: `database/migrations/043_enforce_user_names.sql`

Key changes:
- Adds `profile_incomplete` column
- Marks existing users with missing names
- Adds CHECK constraints for non-empty names
- Creates trigger for auto-updating profile_incomplete

## Testing Requirements

### Backend Tests

1. **Registration Tests**
   - Reject registration with missing first_name
   - Reject registration with missing last_name
   - Reject whitespace-only names
   - Accept valid names and normalize

2. **Update Tests**
   - Reject update with empty names
   - Allow update with valid names
   - Verify profile_incomplete auto-clears

3. **OAuth Tests**
   - Handle provider with names
   - Handle provider without names
   - Verify profile_incomplete flag set correctly

### Frontend Tests

1. **Registration Form**
   - Validate required fields
   - Show errors for empty names
   - Submit with valid data

2. **CompleteProfile Component**
   - Display when profile_incomplete
   - Validate input
   - Update user on submit
   - Clear gate on success

3. **ProtectedRoute**
   - Show CompleteProfile when needed
   - Allow access when profile complete

## API Response Format

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "profile_incomplete": false,
  "role": "student",
  "is_active": true,
  "is_verified": true,
  "avatar_url": null,
  "currency": "USD",
  "timezone": "UTC"
}
```

## Security Considerations

1. **Input Validation**
   - Validate at API boundary, not just UI
   - Sanitize names (trim, escape HTML if needed)
   - Enforce max length to prevent abuse

2. **Privacy**
   - Full names are visible to authenticated users only
   - Public tutor profiles show full name (by design)
   - Admins can see all user names

3. **Data Integrity**
   - Database constraints prevent empty names
   - Trigger auto-manages profile_incomplete flag
   - No way to bypass via direct SQL (CHECK constraints)

## Changelog

- **2026-02-01**: Initial implementation
  - Made first_name/last_name required for registration
  - Added profile_incomplete flag
  - Created CompleteProfile gate component
  - Updated all display locations to use centralized utility
