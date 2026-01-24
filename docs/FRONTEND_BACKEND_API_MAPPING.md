# Frontend to Backend API Reference Mapping

**Generated**: 2026-01-24  
**Purpose**: Complete mapping of all frontend API calls to backend endpoints

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [User Management](#user-management)
3. [Tutor Profiles](#tutor-profiles)
4. [Bookings](#bookings)
5. [Messages](#messages)
6. [Reviews](#reviews)
7. [Subjects](#subjects)
8. [Packages](#packages)
9. [Notifications](#notifications)
10. [Favorites](#favorites)
11. [Admin Operations](#admin-operations)
12. [Avatars & Media](#avatars--media)
13. [Student Profiles](#student-profiles)
14. [Available Slots & Availability](#available-slots--availability)
15. [Utility Endpoints](#utility-endpoints)

---

## Authentication & Authorization

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 364-491), `frontend/lib/api/auth.ts`
- **Base URL**: Configured via `NEXT_PUBLIC_API_URL` environment variable
- **Auth Token**: Stored in cookies (`token`), automatically attached via axios interceptor

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `POST` | `auth.register()` | `/api/auth/register` | `modules/auth/presentation/api.py:33` | Register new user with email, password, name, role, timezone, currency |
| `POST` | `auth.login()` | `/api/auth/login` | `modules/auth/presentation/api.py:136` | Login with email/password (form-encoded), returns JWT token |
| `GET` | `auth.getCurrentUser()` | `/api/auth/me` | `modules/auth/presentation/api.py:216` | Get current authenticated user details |
| `PUT` | `auth.updateUser()` | `/api/auth/me` | `modules/auth/presentation/api.py:295` | Update user profile (first_name, last_name, timezone, currency) |
| `PATCH` | `auth.updatePreferences()` | `/api/users/currency` | `modules/users/currency/router.py:37` | Update user currency preference |
| `PATCH` | `auth.updatePreferences()` | `/api/users/preferences` | `modules/users/preferences/router.py:22` | Update user timezone preference |
| `N/A` | `auth.logout()` | N/A | Client-side only | Remove token cookie and clear cache |

### Frontend Code Patterns

```typescript
// Registration Example
const user = await auth.register(
  "student@example.com",
  "password123",
  "John",
  "Doe",
  "student",
  "America/New_York",
  "USD"
);

// Login Example
const token = await auth.login("student@example.com", "password123");
Cookies.set("token", token, { expires: 7, secure: true, sameSite: 'strict' });

// Get Current User
const currentUser = await auth.getCurrentUser();

// Update User
const updated = await auth.updateUser({
  first_name: "Jane",
  last_name: "Smith",
  timezone: "America/Los_Angeles",
  currency: "EUR"
});

// Logout
auth.logout(); // Removes cookie and redirects to "/"
```

---

## User Management

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 447-490)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `auth.getCurrentUser()` | `/api/auth/me` | `modules/auth/presentation/api.py:216` | Get current user profile |
| `PUT` | `auth.updateUser()` | `/api/auth/me` | `modules/auth/presentation/api.py:295` | Update user information |
| `PATCH` | N/A | `/api/users/currency` | `modules/users/currency/router.py:37` | Update currency |
| `PATCH` | N/A | `/api/users/preferences` | `modules/users/preferences/router.py:22` | Update preferences |

---

## Tutor Profiles

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 517-711)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `tutors.list()` | `/api/tutors` | `modules/tutor_profile/presentation/api.py:303` | List all tutors with filters (subject, rate, rating, experience, search) |
| `GET` | `tutors.get()` | `/api/tutors/{tutor_id}` | `modules/tutor_profile/presentation/api.py:359` | Get full tutor profile (authenticated) |
| `GET` | `tutors.getPublic()` | `/api/tutors/{tutor_id}/public` | `modules/tutor_profile/presentation/api.py:345` | Get public tutor summary |
| `GET` | `tutors.getMyProfile()` | `/api/tutors/me/profile` | `modules/tutor_profile/presentation/api.py:37` | Get current tutor's own profile |
| `PATCH` | `tutors.updateAbout()` | `/api/tutors/me/about` | `modules/tutor_profile/presentation/api.py:122` | Update title, headline, bio, experience, languages |
| `PUT` | `tutors.replaceSubjects()` | `/api/tutors/me/subjects` | `modules/tutor_profile/presentation/api.py:220` | Replace tutor subjects list |
| `PUT` | `tutors.replaceCertifications()` | `/api/tutors/me/certifications` | `modules/tutor_profile/presentation/api.py:134` | Replace certifications with file uploads |
| `PUT` | `tutors.replaceEducation()` | `/api/tutors/me/education` | `modules/tutor_profile/presentation/api.py:180` | Replace education with file uploads |
| `PATCH` | `tutors.updateDescription()` | `/api/tutors/me/description` | `modules/tutor_profile/presentation/api.py:232` | Update tutor description |
| `PATCH` | `tutors.updateVideo()` | `/api/tutors/me/video` | `modules/tutor_profile/presentation/api.py:244` | Update video URL |
| `PATCH` | `tutors.updatePricing()` | `/api/tutors/me/pricing` | `modules/tutor_profile/presentation/api.py:268` | Update hourly rate and pricing options |
| `PUT` | `tutors.replaceAvailability()` | `/api/tutors/me/availability` | `modules/tutor_profile/presentation/api.py:280` | Replace availability schedule |
| `POST` | `tutors.submitForReview()` | `/api/tutors/me/submit` | `modules/tutor_profile/presentation/api.py:292` | Submit profile for admin review |
| `GET` | `tutors.getReviews()` | `/api/reviews/tutors/{tutor_id}` | `modules/reviews/presentation/api.py:163` | Get all reviews for a tutor |
| `PATCH` | `tutors.updateProfilePhoto()` | `/api/tutors/me/photo` | `modules/tutor_profile/presentation/api.py:256` | Upload tutor profile photo |

### Frontend Code Patterns

```typescript
// List tutors with filters
const response = await tutors.list({
  subject_id: 5,
  min_rate: 20,
  max_rate: 100,
  min_rating: 4.0,
  search_query: "math",
  sort_by: "rating_desc",
  page: 1,
  page_size: 20
});

// Get tutor profile
const tutor = await tutors.get(42);

// Update tutor about section
const updated = await tutors.updateAbout({
  title: "Senior Math Tutor",
  headline: "Expert in Calculus and Algebra",
  bio: "10+ years teaching experience",
  experience_years: 10,
  languages: ["English", "Spanish"]
});

// Update pricing
await tutors.updatePricing({
  hourly_rate: 50.00,
  pricing_options: [
    { duration_hours: 5, price: 225, title: "5-hour package" }
  ],
  version: 1
});
```

---

## Bookings

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 719-811)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `bookings.list()` | `/api/bookings` | `modules/bookings/presentation/api.py:146` | List bookings with filters (status, role, pagination) |
| `GET` | `bookings.get()` | `/api/bookings/{booking_id}` | `modules/bookings/presentation/api.py:214` | Get single booking details |
| `POST` | `bookings.create()` | `/api/bookings` | `modules/bookings/presentation/api.py:97` | Create new booking (student only) |
| `POST` | `bookings.cancel()` | `/api/bookings/{booking_id}/cancel` | `modules/bookings/presentation/api.py:225` | Cancel booking with reason |
| `POST` | `bookings.reschedule()` | `/api/bookings/{booking_id}/reschedule` | `modules/bookings/presentation/api.py:264` | Reschedule booking to new time |
| `POST` | `bookings.confirm()` | `/api/tutor/bookings/{booking_id}/confirm` | `modules/bookings/presentation/api.py:353` | Tutor confirms pending booking |
| `POST` | `bookings.decline()` | `/api/tutor/bookings/{booking_id}/decline` | `modules/bookings/presentation/api.py:416` | Tutor declines pending booking |
| `POST` | `bookings.markStudentNoShow()` | `/api/tutor/bookings/{booking_id}/mark-no-show-student` | `modules/bookings/presentation/api.py:467` | Mark student as no-show |
| `POST` | `bookings.markTutorNoShow()` | `/api/tutor/bookings/{booking_id}/mark-no-show-tutor` | `modules/bookings/presentation/api.py:518` | Mark tutor as no-show |

### Frontend Code Patterns

```typescript
// List bookings
const bookings = await bookings.list({
  status: "confirmed",
  role: "student",
  page: 1,
  page_size: 20
});

// Create booking
const booking = await bookings.create({
  tutor_profile_id: 42,
  start_time: "2026-01-25T10:00:00Z",
  duration_hours: 1,
  package_id: 5, // Optional
  notes_student: "Looking forward to the session"
});

// Cancel booking
const cancelled = await bookings.cancel(123, {
  cancellation_reason: "Schedule conflict",
  cancelled_by: "student"
});

// Tutor confirms booking
const confirmed = await bookings.confirm(123, "See you at 10am!");
```

---

## Messages

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 869-959)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `POST` | `messages.send()` | `/api/messages` | `modules/messages/api.py:108` | Send new message to recipient |
| `GET` | `messages.listThreads()` | `/api/messages/threads` | `modules/messages/api.py:183` | List all message threads |
| `GET` | `messages.getThreadMessages()` | `/api/messages/threads/{other_user_id}` | `modules/messages/api.py:234` | Get messages in thread with pagination |
| `GET` | `messages.searchMessages()` | `/api/messages/search` | `modules/messages/api.py:286` | Search messages by query |
| `PATCH` | `messages.markRead()` | `/api/messages/{message_id}/read` | `modules/messages/api.py:344` | Mark single message as read |
| `PATCH` | `messages.markThreadRead()` | `/api/messages/threads/{other_user_id}/read-all` | `modules/messages/api.py:392` | Mark entire thread as read |
| `GET` | `messages.getUnreadCount()` | `/api/messages/unread/count` | `modules/messages/api.py:630` | Get unread message count by sender |
| `PATCH` | `messages.editMessage()` | `/api/messages/{message_id}` | `modules/messages/api.py:668` | Edit message content |
| `DELETE` | `messages.deleteMessage()` | `/api/messages/{message_id}` | `modules/messages/api.py:721` | Delete message |
| `POST` | N/A | `/api/messages/with-attachment` | `modules/messages/api.py:441` | Send message with file attachment |
| `GET` | N/A | `/api/messages/attachments/{attachment_id}/download` | `modules/messages/api.py:547` | Download message attachment |

### WebSocket Support
- **Endpoint**: `ws://{API_URL}/ws/messages` or `wss://{API_URL}/ws/messages`
- **Location**: `frontend/lib/websocket.ts`
- **Backend**: `modules/messages/websocket.py`

### Frontend Code Patterns

```typescript
// Send message
const message = await messages.send(
  recipientId: 42,
  message: "Hello! Ready for our session?",
  bookingId: 123 // Optional
);

// List threads
const threads = await messages.listThreads(limit: 50);

// Get thread messages
const messages = await messages.getThreadMessages(
  otherUserId: 42,
  bookingId: 123, // Optional
  page: 1,
  pageSize: 50
);

// Mark thread as read
await messages.markThreadRead(otherUserId: 42, bookingId: 123);

// Get unread count
const unread = await messages.getUnreadCount();
// Returns: { total: 5, by_sender: { "42": 3, "99": 2 } }
```

---

## Reviews

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 817-831)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `POST` | `reviews.create()` | `/api/reviews` | `modules/reviews/presentation/api.py:42` | Create review for completed booking |
| `GET` | `tutors.getReviews()` | `/api/reviews/tutors/{tutor_id}` | `modules/reviews/presentation/api.py:163` | Get all reviews for tutor |

### Frontend Code Patterns

```typescript
// Create review
const review = await reviews.create(
  bookingId: 123,
  rating: 5,
  comment: "Excellent tutor! Very patient and knowledgeable."
);

// Get tutor reviews
const reviews = await tutors.getReviews(tutorId: 42);
```

---

## Subjects

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 497-511)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `subjects.list()` | `/api/subjects` | `modules/subjects/presentation/api.py:35` | List all subjects (cached for 10 minutes) |
| `POST` | N/A | `/api/subjects` | `modules/subjects/presentation/api.py:47` | Create new subject (admin only) |
| `PUT` | N/A | `/api/subjects/{subject_id}` | `modules/subjects/presentation/api.py:87` | Update subject (admin only) |
| `DELETE` | N/A | `/api/subjects/{subject_id}` | `modules/subjects/presentation/api.py:136` | Delete subject (admin only) |

### Frontend Code Patterns

```typescript
// List all subjects (cached)
const subjects = await subjects.list();
// Returns: [{ id: 1, name: "Mathematics", icon: "📐" }, ...]
```

---

## Packages

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 837-863)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `packages.list()` | `/api/packages` | `modules/packages/presentation/api.py:169` | List student's packages with optional status filter |
| `POST` | `packages.purchase()` | `/api/packages` | `modules/packages/presentation/api.py:54` | Purchase new package |
| `PATCH` | `packages.useCredit()` | `/api/packages/{package_id}/use-credit` | `modules/packages/presentation/api.py:187` | Use one credit from package |

### Frontend Code Patterns

```typescript
// List packages
const packages = await packages.list(statusFilter: "active");

// Purchase package
const newPackage = await packages.purchase({
  tutor_profile_id: 42,
  pricing_option_id: 5,
  payment_intent_id: "pi_123456",
  agreed_terms: "I agree to the terms"
});

// Use package credit
const updated = await packages.useCredit(packageId: 10);
```

---

## Notifications

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 1045-1070)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `notifications.list()` | `/api/notifications` | `modules/notifications/presentation/api.py:17` | List all notifications for current user |
| `PATCH` | `notifications.markAsRead()` | `/api/notifications/{notification_id}/read` | `modules/notifications/presentation/api.py:37` | Mark single notification as read |
| `PATCH` | `notifications.markAllAsRead()` | `/api/notifications/mark-all-read` | `modules/notifications/presentation/api.py:62` | Mark all notifications as read |
| `DELETE` | `notifications.delete()` | `/api/notifications/{notification_id}` | `modules/notifications/presentation/api.py:83` | Delete notification |

### Frontend Code Patterns

```typescript
// List notifications
const notifications = await notifications.list();

// Mark as read
await notifications.markAsRead(notificationId: 42);

// Mark all as read
await notifications.markAllAsRead();

// Delete notification
await notifications.delete(notificationId: 42);
```

---

## Favorites

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 1077-1102)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `favorites.getFavorites()` | `/api/favorites` | `modules/students/presentation/api.py` | Get all favorite tutors for current user |
| `POST` | `favorites.addFavorite()` | `/api/favorites` | `modules/students/presentation/api.py` | Add tutor to favorites |
| `DELETE` | `favorites.removeFavorite()` | `/api/favorites/{tutor_profile_id}` | `modules/students/presentation/api.py` | Remove tutor from favorites |
| `GET` | `favorites.checkFavorite()` | `/api/favorites/{tutor_profile_id}` | `modules/students/presentation/api.py` | Check if tutor is favorited (404 if not) |

### Frontend Code Patterns

```typescript
// Get favorites
const favorites = await favorites.getFavorites();
// Returns: [{ id: 1, tutor_profile_id: 42, tutor: {...}, created_at: "..." }, ...]

// Add to favorites
const favorite = await favorites.addFavorite(tutorProfileId: 42);

// Remove from favorites
await favorites.removeFavorite(tutorProfileId: 42);

// Check if favorited
const isFavorite = await favorites.checkFavorite(tutorProfileId: 42);
// Returns null if not favorited, FavoriteTutor object if favorited
```

---

## Admin Operations

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 1104-1222)

### API Endpoints

#### User Management

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `admin.listUsers()` | `/api/admin/users` | `modules/admin/presentation/api.py:36` | List all users with pagination |
| `PUT` | `admin.updateUser()` | `/api/admin/users/{user_id}` | `modules/admin/presentation/api.py:118` | Update user details (admin override) |
| `DELETE` | `admin.deleteUser()` | `/api/admin/users/{user_id}` | `modules/admin/presentation/api.py:311` | Delete user |
| `PATCH` | N/A | `/api/admin/users/{user_id}/avatar` | `modules/admin/presentation/api.py:234` | Upload avatar for user (admin override) |

#### Tutor Management

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `admin.listPendingTutors()` | `/api/admin/tutors/pending` | `modules/admin/presentation/api.py:345` | List tutors pending approval |
| `GET` | `admin.listApprovedTutors()` | `/api/admin/tutors/approved` | `modules/admin/presentation/api.py:370` | List approved tutors |
| `POST` | `admin.approveTutor()` | `/api/admin/tutors/{tutor_id}/approve` | `modules/admin/presentation/api.py:395` | Approve tutor profile |
| `POST` | `admin.rejectTutor()` | `/api/admin/tutors/{tutor_id}/reject` | `modules/admin/presentation/api.py:441` | Reject tutor with reason |

#### Dashboard Stats

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `admin.getDashboardStats()` | `/api/admin/dashboard/stats` | `modules/admin/presentation/api.py:553` | Get overview statistics (users, bookings, revenue) |
| `GET` | `admin.getRecentActivities()` | `/api/admin/dashboard/recent-activities` | `modules/admin/presentation/api.py:609` | Get recent activities feed |
| `GET` | `admin.getUpcomingSessions()` | `/api/admin/dashboard/upcoming-sessions` | `modules/admin/presentation/api.py:687` | Get upcoming booking sessions |
| `GET` | `admin.getSessionMetrics()` | `/api/admin/dashboard/session-metrics` | `modules/admin/presentation/api.py:718` | Get session completion metrics |
| `GET` | `admin.getMonthlyRevenue()` | `/api/admin/dashboard/monthly-revenue` | `modules/admin/presentation/api.py:859` | Get monthly revenue data |
| `GET` | `admin.getSubjectDistribution()` | `/api/admin/dashboard/subject-distribution` | `modules/admin/presentation/api.py:818` | Get subject booking distribution |
| `GET` | `admin.getUserGrowth()` | `/api/admin/dashboard/user-growth` | `modules/admin/presentation/api.py:918` | Get user growth over time |

#### Audit Logs

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | N/A | `/api/admin/audit/logs` | `modules/admin/audit/router.py:58` | Get audit logs with filters |
| `POST` | N/A | `/api/admin/audit/soft-delete-user` | `modules/admin/audit/router.py:125` | Soft delete user |
| `POST` | N/A | `/api/admin/audit/restore-user` | `modules/admin/audit/router.py:144` | Restore soft-deleted user |
| `GET` | N/A | `/api/admin/audit/deleted-users` | `modules/admin/audit/router.py:163` | List soft-deleted users |
| `POST` | N/A | `/api/admin/audit/purge-old-deletes` | `modules/admin/audit/router.py:200` | Purge old soft deletes |

### Frontend Code Patterns

```typescript
// List users
const users = await admin.listUsers();

// Update user
const updated = await admin.updateUser(userId: 42, {
  role: "tutor",
  is_verified: true
});

// Approve tutor
const approvedTutor = await admin.approveTutor(tutorId: 42);

// Get dashboard stats
const stats = await admin.getDashboardStats();
// Returns: { total_users, active_tutors, total_bookings, total_revenue, ... }

// Get monthly revenue (last 6 months)
const revenue = await admin.getMonthlyRevenue(months: 6);
```

---

## Avatars & Media

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 965-1007), `frontend/lib/media.ts`

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `avatars.fetch()` | `/api/users/me/avatar` | `modules/users/avatar/router.py:46` | Get signed URL for user's avatar |
| `POST` | `avatars.upload()` | `/api/users/me/avatar` | `modules/users/avatar/router.py:27` | Upload user avatar image |
| `DELETE` | `avatars.remove()` | `/api/users/me/avatar` | `modules/users/avatar/router.py:62` | Delete user avatar |
| `PATCH` | `avatars.uploadForUser()` | `/api/admin/users/{user_id}/avatar` | `modules/admin/presentation/api.py:234` | Admin uploads avatar for user |

### Media Utility Functions
- **Location**: `frontend/lib/media.ts`
- **Purpose**: Generate signed URLs for media files (avatars, attachments)

### Frontend Code Patterns

```typescript
// Get avatar URL
const avatar = await avatars.fetch();
// Returns: { avatarUrl: "https://...", expiresAt: "2026-01-25T10:00:00Z" }

// Upload avatar
const file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
const uploaded = await avatars.upload(file);

// Remove avatar
await avatars.remove();

// Admin uploads avatar for user
const adminUpload = await avatars.uploadForUser(userId: 42, file);
```

---

## Student Profiles

### Frontend Implementation
- **Location**: `frontend/lib/api.ts` (lines 1013-1029)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `students.getProfile()` | `/api/profile/student/me` | `modules/students/presentation/api.py:25` | Get student profile |
| `PATCH` | `students.updateProfile()` | `/api/profile/student/me` | `modules/students/presentation/api.py:55` | Update student profile |

### Frontend Code Patterns

```typescript
// Get student profile
const profile = await students.getProfile();

// Update student profile
const updated = await students.updateProfile({
  learning_goals: ["Improve math skills", "Prepare for SAT"],
  grade_level: "12th Grade",
  subjects_of_interest: [1, 5, 7] // Subject IDs
});
```

---

## Available Slots & Availability

### Frontend Implementation
- **Location**: 
  - `frontend/components/TimeSlotPicker.tsx` (lines 108-125)
  - `frontend/components/ModernBookingModal.tsx` (lines 142-155)
  - `frontend/components/TutorProfileView.tsx` (lines 180-201)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | `fetch()` (raw) | `/api/tutors/{tutor_id}/available-slots` | `modules/tutor_profile/presentation/availability_api.py:23` | Get available time slots for tutor |
| `GET` | N/A | `/api/tutors/availability` | `modules/tutor_profile/presentation/availability_api.py:135` | Get tutor's availability rules |
| `POST` | N/A | `/api/tutors/availability` | `modules/tutor_profile/presentation/availability_api.py:153` | Create availability rule |
| `DELETE` | N/A | `/api/tutors/availability/{availability_id}` | `modules/tutor_profile/presentation/availability_api.py:225` | Delete availability rule |
| `POST` | N/A | `/api/tutors/availability/bulk` | `modules/tutor_profile/presentation/availability_api.py:256` | Bulk create availability rules |

### Query Parameters for Available Slots
- `start_date`: ISO 8601 date string (e.g., "2026-01-25")
- `end_date`: ISO 8601 date string (e.g., "2026-02-01")

### Frontend Code Patterns

```typescript
// Get available slots (using native fetch)
const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
const token = Cookies.get('token');
const startDateStr = "2026-01-25";
const endDateStr = "2026-02-01";

const response = await fetch(
  `${API_URL}/api/tutors/${tutorId}/available-slots?start_date=${startDateStr}&end_date=${endDateStr}`,
  {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }
);

const slots = await response.json();
// Returns: [{ start_time: "2026-01-25T10:00:00Z", end_time: "2026-01-25T11:00:00Z", ... }, ...]
```

---

## Utility Endpoints

### Frontend Implementation
- **Location**: Backend only (not directly used in frontend lib)

### API Endpoints

| Method | Frontend Call | Backend Endpoint | Backend File | Description |
|--------|---------------|------------------|--------------|-------------|
| `GET` | N/A | `/api/utils/countries` | `modules/utils/presentation/api.py:40` | List all countries |
| `GET` | N/A | `/api/utils/languages` | `modules/utils/presentation/api.py:52` | List all languages |
| `GET` | N/A | `/api/utils/proficiency-levels` | `modules/utils/presentation/api.py:64` | List language proficiency levels |
| `GET` | N/A | `/api/utils/phone-codes` | `modules/utils/presentation/api.py:76` | List phone country codes |
| `GET` | N/A | `/api/users/currency/options` | `modules/users/currency/router.py:28` | List currency options |

---

## Environment Configuration

### Frontend Environment Variables

```bash
# .env.development / .env.production
NEXT_PUBLIC_API_URL=https://api.valsa.solutions

# .env.localhost (for local development)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API URL Resolution Logic
- **Location**: `frontend/shared/utils/url.ts`
- **Fallback**: `https://api.valsa.solutions`
- **Function**: `getApiBaseUrl(raw?: string)`

```typescript
const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
// Returns validated URL with proper protocol and no trailing slash
```

---

## Request/Response Interceptors

### Authentication Interceptor
- **Location**: `frontend/lib/api.ts` (lines 279-288)
- **Function**: Automatically attaches JWT token from cookies to all requests
- **Header**: `Authorization: Bearer {token}`

### Error Handling Interceptor
- **Location**: `frontend/lib/api.ts` (lines 291-320)
- **Features**:
  - Automatic logout on 401 (Unauthorized)
  - Structured error logging
  - Decimal field parsing for monetary values
  - Redirect to `/login` on auth failures

### Retry Logic
- **Location**: `frontend/lib/api.ts` (lines 149-201)
- **Strategy**: Exponential backoff (1s, 2s, 4s)
- **Max Retries**: 3
- **Conditions**: Network errors and 5xx server errors only
- **Excludes**: 4xx client errors (including 429 rate limits)

### Rate Limiting
- **Location**: `frontend/lib/api.ts` (lines 52-143)
- **Features**:
  - Parse rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
  - Show browser notifications on rate limit (429)
  - Store warning in localStorage
  - Dispatch custom `rateLimit` event for UI components
  - Warning threshold: < 10 remaining requests

---

## Caching Strategy

### Cache Implementation
- **Location**: `frontend/lib/api.ts` (lines 203-276)
- **Type**: In-memory LRU cache with TTL
- **Max Size**: 100 entries
- **Default TTL**: 2 minutes
- **Eviction**: 
  - Stale entries (older than 10 minutes)
  - Least recently used (LRU) if at capacity

### Cached Endpoints

| Endpoint | TTL | Notes |
|----------|-----|-------|
| `/api/subjects` | 10 minutes | Subjects rarely change |
| `/api/tutors` | 1 minute | Only non-search results |
| `/api/admin/dashboard/stats` | 30 seconds | Frequent updates |
| `/api/admin/dashboard/recent-activities` | 15 seconds | Real-time data |
| `/api/admin/dashboard/upcoming-sessions` | 30 seconds | Semi-real-time |
| `/api/admin/dashboard/session-metrics` | 1 minute | Aggregated data |
| `/api/admin/dashboard/monthly-revenue` | 5 minutes | Historical data |
| `/api/admin/dashboard/subject-distribution` | 5 minutes | Historical data |
| `/api/admin/dashboard/user-growth` | 5 minutes | Historical data |

### Cache Invalidation
- **Function**: `clearCache(pattern?: string)`
- **Triggers**: After mutations (create, update, delete operations)
- **Scope**: Can clear specific patterns or entire cache

```typescript
// Clear specific pattern
clearCache('/api/tutors');

// Clear all cache
clearCache();
```

---

## WebSocket Connections

### Real-time Messaging
- **Location**: `frontend/lib/websocket.ts`
- **Backend**: `modules/messages/websocket.py`
- **Protocol**: WebSocket (ws:// or wss://)
- **Authentication**: JWT token via query parameter
- **URL Format**: `ws://{API_URL}/ws/messages?token={jwt_token}`

### WebSocket Events
- **Connection**: Auto-reconnect with exponential backoff
- **Message Types**:
  - `new_message`: New message received
  - `message_read`: Message marked as read
  - `typing`: User is typing indicator
  - `connection`: Connection status updates

### Frontend Implementation

```typescript
import { WebSocketManager } from '@/lib/websocket';

const wsManager = new WebSocketManager();
wsManager.connect(token);

wsManager.on('new_message', (message) => {
  console.log('New message:', message);
});

wsManager.on('message_read', (data) => {
  console.log('Message read:', data);
});
```

---

## Type Definitions

### Primary Type Files
- **Location**: `frontend/types/` and `frontend/lib/api.ts`
- **Imports**: 
  - `User` - User account details
  - `TutorProfile` - Full tutor profile
  - `TutorPublicSummary` - Public tutor card data
  - `Subject` - Subject entity
  - `Booking` - Booking entity
  - `BookingDTO` - Enhanced booking with relations
  - `Review` - Review entity
  - `Message` - Message entity
  - `MessageThread` - Thread summary
  - `StudentProfile` - Student profile
  - `StudentPackage` - Package purchase
  - `FavoriteTutor` - Favorite tutor relation
  - `PaginatedResponse<T>` - Generic pagination wrapper

### Response Type Patterns

```typescript
// Paginated response
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// API Error response
interface ApiErrorResponse {
  detail: string;
  [key: string]: unknown;
}

// Rate limit info
interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number; // Unix timestamp
  retryAfter?: number; // Seconds to wait
}
```

---

## Testing References

### API Integration Tests
- **Location**: `frontend/__tests__/api/favorites-api.test.ts`
- **Coverage**: Favorites endpoints
- **Mocking**: Uses `axios` mocks

### E2E Tests
- **Location**: `frontend/__tests__/e2e/messaging-flow.test.tsx`
- **Coverage**: Message sending, thread viewing, unread counts

### Backend Tests
- **Location**: `backend/tests/`
- **Key Files**:
  - `test_auth.py` - Authentication flows
  - `test_bookings.py` - Booking operations
  - `test_messages.py` - Messaging system
  - `test_tutors_api.py` - Tutor profile endpoints
  - `test_admin_api.py` - Admin operations
  - `test_e2e_admin.py` - Admin workflows
  - `test_e2e_booking.py` - Booking workflows

---

## Common Patterns & Best Practices

### 1. Error Handling

```typescript
try {
  const data = await api.someMethod();
  showSuccess("Operation successful!");
} catch (error: any) {
  const errorMessage = error.response?.data?.detail || error.message || "Unknown error";
  showError(errorMessage);
  logger.error("Operation failed", error);
}
```

### 2. Loading States

```typescript
const [loading, setLoading] = useState(false);

const handleAction = async () => {
  setLoading(true);
  try {
    await api.someMethod();
  } finally {
    setLoading(false);
  }
};
```

### 3. Cache-Aware Mutations

```typescript
// Clear cache after mutation
await api.post("/api/tutors", data);
clearCache('/api/tutors'); // Invalidate tutors list cache
```

### 4. Pagination

```typescript
const [page, setPage] = useState(1);
const [data, setData] = useState<PaginatedResponse<T> | null>(null);

const fetchData = async () => {
  const response = await api.list({ page, page_size: 20 });
  setData(response);
};
```

### 5. Form Encoding for Login

```typescript
// Login requires form encoding, not JSON
const params = new URLSearchParams();
params.append("username", email);
params.append("password", password);

await api.post("/api/auth/login", params.toString(), {
  headers: { "Content-Type": "application/x-www-form-urlencoded" }
});
```

---

## Security Considerations

### CORS Configuration
- **Backend**: `backend/main.py` - CORS middleware
- **Allowed Origins**: Configured via environment variables
- **Credentials**: `allow_credentials=True` for cookies

### Rate Limiting
- **Backend**: `slowapi` middleware
- **Limits**:
  - Registration: 5 requests/minute
  - Login: 10 requests/minute
  - General API: 20-60 requests/minute (endpoint-specific)

### Token Security
- **Storage**: HTTP-only cookies (recommended) or `js-cookie`
- **Expiry**: 7 days
- **Secure**: HTTPS only in production
- **SameSite**: `strict`

### Sensitive Data
- **Never log**: Passwords, tokens, credit card numbers
- **Mask in logs**: Email addresses, phone numbers
- **Encrypt in transit**: HTTPS/TLS for all requests
- **Encrypt at rest**: Database encryption for sensitive fields

---

## Changelog & Version History

### 2026-01-24
- Initial comprehensive mapping created
- Documented all 100+ endpoints
- Added caching strategy details
- Included WebSocket connections
- Added testing references

---

## Quick Reference: Most Used Endpoints

| Operation | Frontend Call | Backend Endpoint |
|-----------|---------------|------------------|
| Login | `auth.login()` | `POST /api/auth/login` |
| Get current user | `auth.getCurrentUser()` | `GET /api/auth/me` |
| List tutors | `tutors.list()` | `GET /api/tutors` |
| Get tutor profile | `tutors.get(id)` | `GET /api/tutors/{id}` |
| Create booking | `bookings.create()` | `POST /api/bookings` |
| List bookings | `bookings.list()` | `GET /api/bookings` |
| Send message | `messages.send()` | `POST /api/messages` |
| List threads | `messages.listThreads()` | `GET /api/messages/threads` |
| Add favorite | `favorites.addFavorite(id)` | `POST /api/favorites` |
| Get favorites | `favorites.getFavorites()` | `GET /api/favorites` |
| Create review | `reviews.create()` | `POST /api/reviews` |
| Get notifications | `notifications.list()` | `GET /api/notifications` |

---

## Support & Maintenance

- **Documentation**: Keep this file updated when adding/changing endpoints
- **Testing**: Update tests when modifying API contracts
- **Versioning**: Consider API versioning for breaking changes (e.g., `/api/v2/...`)
- **Deprecation**: Mark deprecated endpoints and provide migration paths

---

**Last Updated**: 2026-01-24  
**Maintained By**: Development Team  
**Related Docs**: 
- `docs/API_REFERENCE.md` - Backend API specification
- `frontend/lib/api.ts` - Frontend API client implementation
- `backend/main.py` - Backend router configuration
