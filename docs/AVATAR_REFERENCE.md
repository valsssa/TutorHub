# Avatar Component and Integration Reference

## Overview

This document catalogs all files in the codebase that reference the Avatar component, avatar functionality, or avatar-related features. Use this as a reference for understanding avatar integration across the application.

---

## Frontend Components

### Core Avatar Components

1. **`frontend/components/Avatar.tsx`** ⭐ MAIN COMPONENT
   - **Import alias:** `@/components/Avatar` or `@frontend/components/Avatar`
   - **Default export:** `Avatar` component
   - **Primary features:**
     - Displays profile image or fallback to initials
     - Automatic initial generation from name (first character)
     - Dark mode support with Tailwind classes
   - **Size variants:** xs (32px), sm (40px), md (48px), lg (64px), xl (80px)
   - **Color variants:**
     - `gradient` - Blue to cyan gradient (default)
     - `blue` - Light blue with border
     - `emerald` - Light green with border  
     - `purple` - Light purple with border
     - `orange` - Light orange with border
   - **Props interface (`AvatarProps`):**
     - `name?: string` - Display name or email to generate initial from
     - `avatarUrl?: string | null` - Optional avatar image URL
     - `size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'` - Size variant (default: 'md')
     - `variant?: 'blue' | 'emerald' | 'purple' | 'orange' | 'gradient'` - Color scheme (default: 'gradient')
     - `className?: string` - Optional custom className
     - `showOnline?: boolean` - Whether to show online indicator (default: false)
   - **Special features:**
     - Online indicator with pulse animation
     - Next.js Image optimization
     - Filters out ui-avatars.com URLs (uses initials instead)
     - Border and shadow styling

2. **`frontend/components/AvatarUploader.tsx`** ⭐ UPLOADER COMPONENT
   - Avatar upload/removal interface
   - Drag & drop support
   - File validation (2MB max, JPEG/PNG/WebP)
   - Preview and delete functionality
   - Admin mode support (upload for other users)
   - Uses `useAvatar` hook

---

## Frontend Hooks

3. **`frontend/lib/useAvatar.ts`** ⭐ PRIMARY HOOK
   - Avatar state management
   - Upload/remove operations
   - Interfaces: `AvatarController`, `AvatarUploadResult`, `UseAvatarOptions`
   - Auto-refresh on initial URL change

4. **`frontend/lib/useTutorPhoto.ts`**
   - Specialized hook for tutor profile photos
   - Extends avatar controller functionality
   - Used in tutor-specific contexts

---

## Pages Using Avatar

### Main Application Pages

5. **`frontend/app/dashboard/page.tsx`**
   - Handles avatar changes via `handleAvatarChange`
   - Passes avatar handler to role-specific dashboards

6. **`frontend/app/profile/page.tsx`**
   - User profile page with avatar upload
   - Uses `AvatarUploader` component

7. **`frontend/app/settings/page.tsx`**
   - Settings page with avatar management
   - Avatar section with uploader

8. **`frontend/app/tutor/profile/page.tsx`**
   - Tutor profile with avatar uploader
   - Professional profile management

9. **`frontend/app/messages/page.tsx`**
   - Message interface displaying user avatars
   - Uses `Avatar` component for conversation participants

---

## Dashboard Components

10. **`frontend/components/dashboards/TutorDashboard.tsx`**
    - Displays student avatars in booking cards
    - Props: `onAvatarChange: (url: string | null) => void`
    - Uses gradient variant for student avatars

11. **`frontend/components/dashboards/StudentDashboard.tsx`**
    - Student dashboard interface
    - Props: `onAvatarChange: (url: string | null) => void`

12. **`frontend/components/dashboards/AdminDashboard.tsx`**
    - Admin dashboard with avatar management
    - Props: `onAvatarChange: (url: string | null) => void`

---

## Navigation & Layout

13. **`frontend/components/Navbar.tsx`**
    - Imports and uses `Avatar` component
    - Renders avatar in multiple sizes (xs, sm, md)
    - User dropdown with avatar display

---

## Booking Components

14. **`frontend/components/bookings/BookingCardTutor.tsx`**
    - Displays student avatar in booking cards

15. **`frontend/components/bookings/BookingCardStudent.tsx`**
    - Displays tutor avatar in booking cards

---

## Frontend Types & API

16. **`frontend/types/index.ts`**
    - `AvatarApiResponse` interface
    - `AvatarSignedUrl` interface
    - `AvatarDeleteResponse` interface

17. **`frontend/lib/api.ts`**
    - Avatar API methods:
      - `fetch(): Promise<AvatarSignedUrl>`
      - `upload(file: File): Promise<AvatarSignedUrl>`
      - `uploadForUser(userId: number, file: File): Promise<AvatarSignedUrl>`
    - `transformAvatarResponse(data: AvatarApiResponse): AvatarSignedUrl`

18. **`frontend/lib/api/core/utils.ts`**
    - Utility function: `transformAvatarResponse`

---

## Backend Modules

### Avatar Service Module ⭐ CORE SERVICE

19. **`backend/modules/users/avatar/service.py`**
    - Primary avatar service class: `AvatarService`
    - Methods:
      - `upload_for_user(user, upload)` - Upload avatar
      - `fetch_for_user(user)` - Get avatar URL
      - `delete_for_user(user)` - Remove avatar
    - Validation: 2MB max, 150x150 min, 2000x2000 max dimensions
    - Supported formats: JPEG, PNG, WebP

20. **`backend/modules/users/avatar/router.py`**
    - Avatar API endpoints:
      - `POST /me/avatar` - Upload avatar
      - `GET /me/avatar` - Fetch avatar
      - `DELETE /me/avatar` - Delete avatar

21. **`backend/modules/users/avatar/schemas.py`**
    - Pydantic schemas:
      - `AvatarResponse`
      - `AvatarDeleteResponse`

22. **`backend/modules/users/avatar/__init__.py`**
    - Avatar management package init

---

## Admin Module

23. **`backend/modules/admin/presentation/api.py`**
    - Admin endpoint: `PATCH /users/{user_id}/avatar`
    - Allows admins to upload avatars for other users
    - Uses `AvatarService` and `AvatarResponse`

---

## Authentication Module

24. **`backend/modules/auth/presentation/api.py`**
    - Imports `AvatarService`
    - Returns avatar URL in auth responses
    - Handles default avatar URLs

---

## Core Backend

25. **`backend/core/avatar_storage.py`**
    - `AvatarStorageClient` class
    - MinIO/S3-compatible storage integration
    - Signed URL generation (5-minute TTL)
    - `get_avatar_storage()` factory function

26. **`backend/core/config.py`**
    - Avatar storage configuration:
      - `AVATAR_STORAGE_DEFAULT_URL` (default: placeholder image)
      - MinIO/S3 connection settings

---

## Repository Layer

27. **`backend/modules/tutor_profile/infrastructure/repositories.py`**
    - Note: Avatar stored in `users.avatar_key`, not tutor profile

---

## Tests

### Backend Tests

28. **`backend/tests/test_avatar.py`** ⭐ MAIN AVATAR TESTS
    - `FakeAvatarStorage` mock class
    - Tests:
      - `test_upload_avatar_success`
      - `test_upload_avatar_rejects_large_file`
      - `test_upload_avatar_rejects_corrupt_image`
      - Delete avatar workflow tests

29. **`backend/tests/test_auth.py`**
    - Verifies default avatar URL in auth responses
    - Checks avatar_url field in registration/login

---

### Frontend Tests

30. **`frontend/__tests__/components/AvatarUploader.test.tsx`**
    - Tests for `AvatarUploader` component
    - Mocks `useAvatar` hook
    - Tests upload/delete workflows

31. **`frontend/__tests__/components/TutorCard.test.tsx`**
    - Tests tutor card with/without avatar
    - `noAvatarTutor` test case

---

## Docker & Environment

32. **`docker-compose.yml`**
    - Environment variable: `AVATAR_STORAGE_DEFAULT_URL`

33. **`docker-compose.test.yml`**
    - Test environment avatar configuration

34. **`docker-compose.optimized.yml`**
    - Optimized build avatar settings

35. **`docker-compose.prod.yml`**
    - Production avatar storage configuration

36. **`backend/.env.example`**
    - Example avatar configuration values

---

## Scripts & Utilities

37. **`scripts/backup_avatars.sh`**
    - Avatar backup utility script
    - Creates archive of avatar data

---

## Documentation

38. **`docs/API_REFERENCE.md`**
    - Avatar API endpoint documentation
    - Response schemas and examples

39. **`docs/FRONTEND_BACKEND_API_MAPPING.md`**
    - Section: "Avatars & Media"
    - Maps frontend to backend avatar operations

40. **`docs/tests/COMPREHENSIVE_TEST_PLAN.md`**
    - Avatar test coverage documentation
    - References `AvatarUploader.test.tsx`

41. **`docs/analysis/COMPREHENSIVE_CODEBASE_ANALYSIS.md`**
    - Avatar storage architecture
    - MinIO/S3 integration details
    - Avatar upload/download flows

42. **`docs/analysis/PROJECT_ANALYSIS_REPORT.md`**
    - Avatar management overview
    - Security: Signed URLs, MinIO private buckets
    - Test coverage summary

43. **`docs/analysis/ANALYSIS_SUMMARY.md`**
    - Avatar management status
    - MinIO storage and signed URLs

44. **`README.md`**
    - Section: "🖼️ Secure Profile Avatars"
    - Environment variable documentation

45. **`COMPREHENSIVE_INCONSISTENCIES_ANALYSIS.md`**
    - Avatar URL field analysis

---

## Technical Specifications

### Supported Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)

### Size Constraints
- **Maximum file size:** 2 MB
- **Minimum dimensions:** 150x150 pixels
- **Maximum dimensions:** 2000x2000 pixels

### Storage
- **Backend:** MinIO (S3-compatible object storage)
- **Access:** Signed URLs with 5-minute TTL
- **Field:** `users.avatar_key` (stores MinIO key, not URL)
- **Default:** Placeholder image (`https://placehold.co/300x300?text=Avatar`)

### API Endpoints

#### User Endpoints
- `POST /api/users/me/avatar` - Upload avatar
- `GET /api/users/me/avatar` - Fetch avatar URL
- `DELETE /api/users/me/avatar` - Remove avatar

#### Admin Endpoints
- `PATCH /api/admin/users/{user_id}/avatar` - Upload avatar for any user

### Frontend Integration Pattern

```typescript
import Avatar from '@/components/Avatar';
import AvatarUploader from '@/components/AvatarUploader';

// Display avatar
<Avatar 
  name={user.name} 
  avatarUrl={user.avatar_url}
  size="md"
  variant="gradient"
/>

// Upload avatar
<AvatarUploader 
  onAvatarChange={(url) => console.log('New avatar:', url)}
/>
```

---

## Summary Statistics

- **Total files with Avatar references:** 45
- **Frontend components:** 15
- **Backend modules:** 8
- **Test files:** 3
- **Documentation files:** 7
- **Configuration files:** 5
- **Scripts:** 1
- **Hooks/utilities:** 6

---

## Quick Reference

### Import Paths

```typescript
// Components
import Avatar from '@/components/Avatar'
import AvatarUploader from '@/components/AvatarUploader'

// Hooks
import { useAvatar } from '@/lib/useAvatar'
import { useTutorPhoto } from '@/lib/useTutorPhoto'

// Types
import type { AvatarApiResponse, AvatarSignedUrl } from '@/types'
```

```python
# Backend
from modules.users.avatar.service import AvatarService
from modules.users.avatar.schemas import AvatarResponse, AvatarDeleteResponse
from core.avatar_storage import AvatarStorageClient, get_avatar_storage
```

---

*Generated: January 24, 2026*  
*Project: Project1-splitversion*
