# EduStream API Reference

**Version:** 1.0.0  
**Base URL (Production):** `https://api.valsa.solutions`  
**Base URL (Local Development):** `http://localhost:8000`

---

## Table of Contents

- [Authentication](#authentication)
- [User Management](#user-management)
- [Tutor Profiles](#tutor-profiles)
- [Student Profiles](#student-profiles)
- [Bookings](#bookings)
- [Reviews](#reviews)
- [Messages](#messages)
- [Notifications](#notifications)
- [Packages](#packages)
- [Subjects](#subjects)
- [Admin Panel](#admin-panel)
- [Audit Logs](#audit-logs)
- [Utilities](#utilities)
- [Health & Monitoring](#health--monitoring)

---

## Authentication

All authenticated endpoints require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### POST /auth/register
**Summary:** Register new user account  
**Rate Limit:** 5 requests/minute  
**Authentication:** None required

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student"
}
```

**Response (201):**
```json
{
  "id": 42,
  "email": "student@example.com",
  "role": "student",
  "is_active": true,
  "is_verified": false,
  "first_name": "John",
  "last_name": "Doe",
  "avatar_url": "https://api.valsa.solutions/api/avatars/default.png",
  "currency": "USD",
  "timezone": "UTC",
  "created_at": "2025-01-24T10:30:00.000Z",
  "updated_at": "2025-01-24T10:30:00.000Z"
}
```

**Errors:**
- `400`: Validation error (invalid email/password)
- `409`: Email already registered
- `429`: Rate limit exceeded

---

### POST /auth/login
**Summary:** Login and get JWT token  
**Rate Limit:** 10 requests/minute  
**Authentication:** None required

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 42,
    "email": "student@example.com",
    "role": "student",
    "is_active": true
  }
}
```

**Errors:**
- `401`: Invalid credentials
- `429`: Rate limit exceeded

---

### GET /auth/me
**Summary:** Get current user profile  
**Authentication:** Required  

**Response (200):**
```json
{
  "id": 42,
  "email": "student@example.com",
  "role": "student",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar_url": "https://api.valsa.solutions/api/avatars/42.jpg",
  "currency": "USD",
  "timezone": "America/New_York",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-01-24T10:30:00.000Z"
}
```

---

### PUT /auth/me
**Summary:** Update current user profile  
**Authentication:** Required

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone": "+1234567890",
  "timezone": "America/New_York"
}
```

**Response (200):** Updated user object

---

## User Management

### POST /api/users/me/avatar
**Summary:** Upload user avatar  
**Authentication:** Required  

**Request:** Multipart form-data with `file` field  
**Allowed formats:** JPG, PNG, GIF, WebP  
**Max size:** 5MB

**Response (201):**
```json
{
  "avatar_url": "https://api.valsa.solutions/api/avatars/42.jpg",
  "uploaded_at": "2025-01-24T10:30:00.000Z"
}
```

---

### GET /api/users/me/avatar
**Summary:** Get current user avatar URL  
**Authentication:** Required

**Response (200):**
```json
{
  "avatar_url": "https://api.valsa.solutions/api/avatars/42.jpg"
}
```

---

### DELETE /api/users/me/avatar
**Summary:** Delete user avatar (revert to default)  
**Authentication:** Required

**Response (200):**
```json
{
  "message": "Avatar deleted successfully",
  "avatar_url": "https://api.valsa.solutions/api/avatars/default.png"
}
```

---

### PATCH /api/users/preferences
**Summary:** Update user preferences  
**Authentication:** Required

**Request Body:**
```json
{
  "email_notifications": true,
  "push_notifications": false,
  "sms_notifications": true
}
```

---

### GET /api/users/currency/options
**Summary:** Get available currency options  
**Authentication:** Required

**Response (200):**
```json
[
  {"code": "USD", "symbol": "$", "name": "US Dollar"},
  {"code": "EUR", "symbol": "€", "name": "Euro"},
  {"code": "GBP", "symbol": "£", "name": "British Pound"}
]
```

---

### PATCH /api/users/currency
**Summary:** Update user preferred currency  
**Authentication:** Required

**Request Body:**
```json
{
  "currency": "EUR"
}
```

---

## Tutor Profiles

### GET /api/tutors
**Summary:** Search and list tutors (public endpoint)  
**Authentication:** Optional (public search, enhanced results when authenticated)

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page
- `subject_id` (int, optional): Filter by subject
- `min_rate` (float, optional): Minimum hourly rate
- `max_rate` (float, optional): Maximum hourly rate
- `experience_years` (int, optional): Minimum years of experience
- `languages` (string, optional): Comma-separated language codes
- `search` (string, optional): Search in name, bio, headline
- `sort` (string, optional): Sort field (rating, rate, experience)

**Response (200):**
```json
{
  "items": [
    {
      "id": 5,
      "user_id": 10,
      "title": "Experienced Math Tutor",
      "headline": "10+ years teaching calculus and algebra",
      "bio": "Passionate about helping students excel...",
      "hourly_rate": 45.00,
      "currency": "USD",
      "experience_years": 10,
      "education": "Master's in Education",
      "languages": ["English", "Spanish"],
      "subjects": [
        {"id": 1, "name": "Mathematics", "category": "STEM"}
      ],
      "avatar_url": "https://api.valsa.solutions/api/avatars/10.jpg",
      "average_rating": 4.8,
      "total_reviews": 42,
      "is_approved": true,
      "is_online": false
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

### GET /api/tutors/{tutor_id}/public
**Summary:** Get public tutor profile  
**Authentication:** None required

**Response (200):** Single tutor profile object (same structure as search results)

---

### GET /api/tutors/{tutor_id}
**Summary:** Get detailed tutor profile (authenticated)  
**Authentication:** Required

**Response (200):** Extended tutor profile with availability and private details

---

### GET /api/tutors/{tutor_id}/reviews
**Summary:** Get tutor reviews  
**Authentication:** None required

**Response (200):**
```json
[
  {
    "id": 1,
    "student_name": "Jane Doe",
    "rating": 5,
    "comment": "Excellent tutor! Very patient and knowledgeable.",
    "created_at": "2025-01-20T15:30:00.000Z",
    "tutor_response": "Thank you for the kind words!",
    "booking_id": 123
  }
]
```

---

### GET /api/tutors/me/profile
**Summary:** Get own tutor profile (tutor only)  
**Authentication:** Required (tutor role)

**Response (200):**
```json
{
  "id": 10,
  "user_id": 5,
  "title": "Expert Math & Physics Tutor",
  "headline": "15 years of teaching experience",
  "bio": "I specialize in making complex topics simple...",
  "teaching_philosophy": "I focus on building intuition first, then practice.",
  "hourly_rate": 55.00,
  "experience_years": 15,
  "languages": ["en", "es"],
  "profile_status": "approved",
  "average_rating": 4.9,
  "total_reviews": 120
}
```

---

### PATCH /api/tutors/me/about
**Summary:** Update tutor about section  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "title": "Expert Math & Physics Tutor",
  "headline": "15 years of teaching experience",
  "bio": "I specialize in making complex topics simple...",
  "teaching_philosophy": "I focus on building intuition first, then practice.",
  "experience_years": 12,
  "languages": ["en", "es"]
}
```

---

### PUT /api/tutors/me/subjects
**Summary:** Update tutor subjects/specializations  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "subject_ids": [1, 2, 5]
}
```

---

### PATCH /api/tutors/me/pricing
**Summary:** Update tutor hourly rate  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "hourly_rate": 55.00,
  "currency": "USD"
}
```

---

### PUT /api/tutors/me/availability
**Summary:** Update tutor availability schedule  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "timezone": "America/New_York",
  "weekly_schedule": [
    {
      "day_of_week": "monday",
      "start_time": "09:00",
      "end_time": "17:00"
    }
  ]
}
```

---

### POST /api/tutors/me/submit
**Summary:** Submit profile for admin approval  
**Authentication:** Required (tutor role)

**Response (200):**
```json
{
  "message": "Profile submitted for review",
  "status": "pending_approval"
}
```

---

### PUT /api/tutors/me/certifications
**Summary:** Update tutor certifications  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "certifications": [
    {
      "title": "Certified Math Educator",
      "issuer": "National Board",
      "year": 2020
    }
  ]
}
```

---

### PUT /api/tutors/me/education
**Summary:** Update tutor education history  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "education": [
    {
      "degree": "Master of Education",
      "institution": "University of Example",
      "year": 2015
    }
  ]
}
```

---

### PATCH /api/tutors/me/description
**Summary:** Update tutor short description  
**Authentication:** Required (tutor role)

---

### PATCH /api/tutors/me/video
**Summary:** Update tutor intro video URL  
**Authentication:** Required (tutor role)

---

### PATCH /api/tutors/me/photo
**Summary:** Update tutor profile photo  
**Authentication:** Required (tutor role)

---

## Tutor Availability

### GET /api/tutors/{tutor_id}/available-slots
**Summary:** Get tutor available time slots  
**Authentication:** Required

**Query Parameters:**
- `start_date` (date, required): Start date (YYYY-MM-DD)
- `end_date` (date, required): End date (YYYY-MM-DD)
- `duration_minutes` (int, default: 60): Session duration

**Response (200):**
```json
[
  {
    "start_time": "2025-01-25T09:00:00Z",
    "end_time": "2025-01-25T10:00:00Z",
    "is_available": true
  }
]
```

---

### GET /api/tutors/availability
**Summary:** Get tutor's own availability schedule  
**Authentication:** Required (tutor role)

**Response (200):**
```json
[
  {
    "id": 1,
    "day_of_week": "monday",
    "start_time": "09:00",
    "end_time": "17:00",
    "is_recurring": true
  }
]
```

---

### POST /api/tutors/availability
**Summary:** Add availability slot  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "day_of_week": "tuesday",
  "start_time": "14:00",
  "end_time": "18:00",
  "is_recurring": true
}
```

---

### DELETE /api/tutors/availability/{availability_id}
**Summary:** Delete availability slot  
**Authentication:** Required (tutor role)

**Response (204):** No content

---

### POST /api/tutors/availability/bulk
**Summary:** Bulk create availability slots  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "slots": [
    {
      "day_of_week": "monday",
      "start_time": "09:00",
      "end_time": "12:00"
    },
    {
      "day_of_week": "wednesday",
      "start_time": "14:00",
      "end_time": "17:00"
    }
  ]
}
```

---

## Student Profiles

### GET /api/profile/student/me
**Summary:** Get own student profile  
**Authentication:** Required (student role)

**Response (200):**
```json
{
  "id": 1,
  "user_id": 42,
  "phone": "+1-555-123-4567",
  "bio": "Busy high-schooler prepping for SAT math.",
  "grade_level": "High School",
  "school_name": "Roosevelt High",
  "learning_goals": "Improve calculus skills for college entrance",
  "interests": "Math club, robotics",
  "preferred_language": "en",
  "timezone": "America/New_York",
  "total_sessions": 12,
  "created_at": "2025-01-10T12:00:00Z",
  "updated_at": "2025-01-24T09:15:00Z"
}
```

---

### PATCH /api/profile/student/me
**Summary:** Update student profile  
**Authentication:** Required (student role)

**Request Body:**
```json
{
  "learning_goals": "Master linear algebra",
  "grade_level": "Undergraduate",
  "preferred_language": "en",
  "timezone": "America/Los_Angeles"
}
```

**Notes:**
- `timezone` is sourced from the `users` table and returned for convenience; it is not stored on `student_profiles`.
- `preferred_learning_style` and `education_level` are not persisted and have been removed.

---

### POST /api/students/favorites/{tutor_id}
**Summary:** Add tutor to favorites  
**Authentication:** Required (student role)

**Response (201):**
```json
{
  "message": "Tutor added to favorites"
}
```

---

### DELETE /api/students/favorites/{tutor_id}
**Summary:** Remove tutor from favorites  
**Authentication:** Required (student role)

**Response (204):** No content

---

### GET /api/students/favorites
**Summary:** Get favorite tutors  
**Authentication:** Required (student role)

**Response (200):** List of favorite tutor profiles

---

## Bookings

### POST /api/bookings
**Summary:** Create new booking (student only)  
**Authentication:** Required (student role)

**Request Body:**
```json
{
  "tutor_profile_id": 5,
  "start_at": "2025-01-25T14:00:00Z",
  "duration_minutes": 60,
  "lesson_type": "online",
  "subject_id": 1,
  "notes_student": "Need help with quadratic equations",
  "use_package_id": 10
}
```

**Response (201):**
```json
{
  "id": 123,
  "student_id": 42,
  "tutor_profile_id": 5,
  "start_time": "2025-01-25T14:00:00Z",
  "end_time": "2025-01-25T15:00:00Z",
  "status": "PENDING",
  "lesson_type": "online",
  "price_student": 45.00,
  "currency": "USD",
  "subject": {
    "id": 1,
    "name": "Mathematics"
  },
  "tutor": {
    "name": "John Tutor",
    "avatar_url": "https://api.valsa.solutions/api/avatars/10.jpg"
  },
  "created_at": "2025-01-24T10:30:00Z"
}
```

**Errors:**
- `400`: Invalid request (time conflict, tutor not available)
- `404`: Tutor not found
- `402`: Insufficient package credits

---

### GET /api/bookings
**Summary:** List user bookings with filtering  
**Authentication:** Required

**Query Parameters:**
- `status` (string, optional): Filter by status (upcoming, pending, completed, cancelled)
- `role` (string, default: student): View as student or tutor
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page

**Response (200):**
```json
{
  "bookings": [
    {
      "id": 123,
      "tutor_name": "John Tutor",
      "student_name": "Jane Student",
      "start_time": "2025-01-25T14:00:00Z",
      "status": "CONFIRMED",
      "price": 45.00
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

### GET /api/bookings/{booking_id}
**Summary:** Get booking details  
**Authentication:** Required (student or tutor of booking)

**Response (200):** Full booking details

---

### POST /api/bookings/{booking_id}/cancel
**Summary:** Cancel booking  
**Authentication:** Required (student or tutor of booking)

**Request Body:**
```json
{
  "reason": "Schedule conflict"
}
```

**Response (200):** Updated booking with status CANCELLED

---

### POST /api/bookings/{booking_id}/reschedule
**Summary:** Request booking reschedule  
**Authentication:** Required (student or tutor of booking)

**Request Body:**
```json
{
  "new_start_time": "2025-01-26T14:00:00Z",
  "reason": "Emergency conflict"
}
```

**Response (200):** Updated booking

---

### POST /api/tutor/bookings/{booking_id}/confirm
**Summary:** Tutor confirms booking  
**Authentication:** Required (tutor role)

**Response (200):** Updated booking with status CONFIRMED

---

### POST /api/tutor/bookings/{booking_id}/decline
**Summary:** Tutor declines booking  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "reason": "Not available at this time"
}
```

---

### POST /api/tutor/bookings/{booking_id}/mark-no-show-student
**Summary:** Mark student as no-show  
**Authentication:** Required (tutor role)

**Response (200):** Updated booking

---

### POST /api/tutor/bookings/{booking_id}/mark-no-show-tutor
**Summary:** Mark tutor as no-show (system/admin use)  
**Authentication:** Required (admin role)

---

## Reviews

### POST /api/reviews
**Summary:** Create review for completed session  
**Authentication:** Required (student role)

**Request Body:**
```json
{
  "booking_id": 123,
  "rating": 5,
  "comment": "Excellent session! Very helpful and patient."
}
```

**Response (201):**
```json
{
  "id": 1,
  "booking_id": 123,
  "tutor_id": 5,
  "student_id": 42,
  "rating": 5,
  "comment": "Excellent session!",
  "created_at": "2025-01-24T10:30:00Z"
}
```

**Errors:**
- `400`: Booking not completed or already reviewed
- `404`: Booking not found

---

### GET /api/reviews/tutors/{tutor_id}
**Summary:** Get reviews for a tutor  
**Authentication:** None required

**Response (200):** List of reviews

---

## Messages

### POST /api/messages
**Summary:** Send message to another user  
**Authentication:** Required

**Request Body:**
```json
{
  "recipient_id": 10,
  "message": "Hi! I'd like to book a session.",
  "booking_id": 123
}
```

**Response (201):**
```json
{
  "id": 1,
  "sender_id": 42,
  "recipient_id": 10,
  "message": "Hi! I'd like to book a session.",
  "is_read": false,
  "created_at": "2025-01-24T10:30:00Z"
}
```

---

### GET /api/messages/threads
**Summary:** Get message threads list  
**Authentication:** Required

**Response (200):**
```json
[
  {
    "other_user_id": 10,
    "other_user_name": "John Tutor",
    "other_user_avatar": "https://api.valsa.solutions/api/avatars/10.jpg",
    "last_message": "See you tomorrow!",
    "last_message_at": "2025-01-24T10:30:00Z",
    "unread_count": 2
  }
]
```

---

### GET /api/messages/threads/{other_user_id}
**Summary:** Get conversation with specific user  
**Authentication:** Required

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50): Messages per page

**Response (200):**
```json
{
  "messages": [
    {
      "id": 1,
      "sender_id": 42,
      "recipient_id": 10,
      "message": "Hello!",
      "is_read": true,
      "created_at": "2025-01-24T09:00:00Z"
    }
  ],
  "total": 45,
  "page": 1
}
```

---

### GET /api/messages/search
**Summary:** Search messages  
**Authentication:** Required

**Query Parameters:**
- `query` (string, required): Search term
- `user_id` (int, optional): Filter by user

**Response (200):** Matching messages

---

### PATCH /api/messages/{message_id}/read
**Summary:** Mark message as read  
**Authentication:** Required

**Response (200):** Updated message

---

### PATCH /api/messages/threads/{other_user_id}/read-all
**Summary:** Mark all messages in thread as read  
**Authentication:** Required

**Response (200):** Success message

---

### POST /api/messages/with-attachment
**Summary:** Send message with file attachment  
**Authentication:** Required

**Request:** Multipart form-data
- `recipient_id` (int)
- `message` (string)
- `file` (file)

---

### GET /api/messages/attachments/{attachment_id}/download
**Summary:** Download message attachment  
**Authentication:** Required

**Response (200):** File download

---

### GET /api/messages/unread/count
**Summary:** Get unread messages count  
**Authentication:** Required

**Response (200):**
```json
{
  "unread_count": 5
}
```

---

### PATCH /api/messages/{message_id}
**Summary:** Edit message  
**Authentication:** Required (sender only)

**Request Body:**
```json
{
  "message": "Updated message content"
}
```

---

### DELETE /api/messages/{message_id}
**Summary:** Delete message  
**Authentication:** Required (sender only)

**Response (204):** No content

---

## Notifications

### GET /api/notifications
**Summary:** Get user notifications  
**Authentication:** Required

**Response (200):**
```json
[
  {
    "id": 1,
    "type": "booking_confirmed",
    "title": "Booking Confirmed",
    "message": "Your session with John Tutor is confirmed",
    "is_read": false,
    "created_at": "2025-01-24T10:30:00Z",
    "data": {
      "booking_id": 123
    }
  }
]
```

---

### PATCH /api/notifications/{notification_id}/read
**Summary:** Mark notification as read  
**Authentication:** Required

**Response (200):** Updated notification

---

### PATCH /api/notifications/mark-all-read
**Summary:** Mark all notifications as read  
**Authentication:** Required

**Response (200):** Success message

---

### DELETE /api/notifications/{notification_id}
**Summary:** Delete notification  
**Authentication:** Required

**Response (204):** No content

---

## Packages

### POST /api/packages
**Summary:** Create tutor package (tutor only)  
**Authentication:** Required (tutor role)

**Request Body:**
```json
{
  "name": "5-Session Math Package",
  "description": "5 one-hour sessions at discounted rate",
  "session_count": 5,
  "price": 200.00,
  "duration_minutes": 60,
  "validity_days": 90
}
```

**Response (201):**
```json
{
  "id": 10,
  "tutor_profile_id": 5,
  "name": "5-Session Math Package",
  "session_count": 5,
  "price": 200.00,
  "price_per_session": 40.00,
  "is_active": true
}
```

---

### GET /api/packages
**Summary:** List packages  
**Authentication:** Required

**Query Parameters:**
- `tutor_id` (int, optional): Filter by tutor

**Response (200):** List of packages

---

### PATCH /api/packages/{package_id}/use-credit
**Summary:** Use one package credit (internal)  
**Authentication:** Required

**Response (200):** Updated package with remaining credits

---

## Subjects

### GET /api/subjects
**Summary:** List all subjects  
**Authentication:** None required

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Mathematics",
    "category": "STEM",
    "description": "All math topics from basic to advanced"
  }
]
```

---

### POST /api/subjects
**Summary:** Create new subject (admin only)  
**Authentication:** Required (admin role)

**Request Body:**
```json
{
  "name": "Advanced Physics",
  "category": "STEM",
  "description": "University-level physics"
}
```

---

### PUT /api/subjects/{subject_id}
**Summary:** Update subject (admin only)  
**Authentication:** Required (admin role)

---

### DELETE /api/subjects/{subject_id}
**Summary:** Delete subject (admin only)  
**Authentication:** Required (admin role)

**Response (204):** No content

---

## Admin Panel

### GET /api/admin/users
**Summary:** List all users (admin only)  
**Authentication:** Required (admin role)

**Query Parameters:**
- `page` (int, default: 1)
- `page_size` (int, default: 100)
- `role` (string, optional): Filter by role
- `search` (string, optional): Search by email/name

**Response (200):**
```json
{
  "items": [
    {
      "id": 42,
      "email": "user@example.com",
      "role": "student",
      "is_active": true,
      "created_at": "2025-01-20T10:00:00Z"
    }
  ],
  "total": 500,
  "page": 1
}
```

---

### PUT /api/admin/users/{user_id}
**Summary:** Update user (admin only)  
**Authentication:** Required (admin role)

**Request Body:**
```json
{
  "role": "tutor",
  "is_active": true
}
```

---

### DELETE /api/admin/users/{user_id}
**Summary:** Soft-delete user (admin only)  
**Authentication:** Required (admin role)

**Response (204):** No content

---

### PATCH /api/admin/users/{user_id}/avatar
**Summary:** Update user avatar (admin only)  
**Authentication:** Required (admin role)

---

### GET /api/admin/tutors/pending
**Summary:** Get pending tutor approvals  
**Authentication:** Required (admin role)

**Response (200):** List of pending tutor profiles

---

### GET /api/admin/tutors/approved
**Summary:** Get approved tutors  
**Authentication:** Required (admin role)

**Response (200):** List of approved tutors

---

### POST /api/admin/tutors/{tutor_id}/approve
**Summary:** Approve tutor profile  
**Authentication:** Required (admin role)

**Response (200):**
```json
{
  "message": "Tutor approved successfully",
  "tutor_id": 5,
  "status": "approved"
}
```

---

### POST /api/admin/tutors/{tutor_id}/reject
**Summary:** Reject tutor profile  
**Authentication:** Required (admin role)

**Request Body:**
```json
{
  "rejection_reason": "Incomplete profile information"
}
```

---

### GET /api/admin/dashboard/stats
**Summary:** Get dashboard statistics  
**Authentication:** Required (admin role)

**Response (200):**
```json
{
  "total_users": 1000,
  "total_tutors": 150,
  "total_students": 800,
  "pending_approvals": 5,
  "total_bookings": 5000,
  "revenue_this_month": 25000.00
}
```

---

### GET /api/admin/dashboard/recent-activities
**Summary:** Get recent platform activities  
**Authentication:** Required (admin role)

**Query Parameters:**
- `limit` (int, default: 50)

---

### GET /api/admin/dashboard/upcoming-sessions
**Summary:** Get upcoming sessions  
**Authentication:** Required (admin role)

**Query Parameters:**
- `limit` (int, default: 50)

---

### GET /api/admin/dashboard/session-metrics
**Summary:** Get session metrics  
**Authentication:** Required (admin role)

**Response (200):**
```json
{
  "total_sessions": 5000,
  "completed_sessions": 4500,
  "cancelled_sessions": 300,
  "no_show_rate": 0.04
}
```

---

### GET /api/admin/dashboard/subject-distribution
**Summary:** Get subject popularity distribution  
**Authentication:** Required (admin role)

---

### GET /api/admin/dashboard/monthly-revenue
**Summary:** Get monthly revenue data  
**Authentication:** Required (admin role)

**Query Parameters:**
- `months` (int, default: 6): Number of months to include

---

### GET /api/admin/dashboard/user-growth
**Summary:** Get user growth metrics  
**Authentication:** Required (admin role)

**Query Parameters:**
- `months` (int, default: 6)

---

## Audit Logs

### GET /api/audit/logs
**Summary:** Get audit logs (admin only)  
**Authentication:** Required (admin role)

**Query Parameters:**
- `page` (int, default: 1)
- `page_size` (int, default: 50)
- `action_type` (string, optional): Filter by action type
- `user_id` (int, optional): Filter by user

**Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "action": "user_role_changed",
    "details": {
      "old_role": "student",
      "new_role": "tutor"
    },
    "ip_address": "192.168.1.1",
    "created_at": "2025-01-24T10:30:00Z"
  }
]
```

---

### POST /api/audit/soft-delete-user
**Summary:** Soft delete user with audit  
**Authentication:** Required (admin role)

---

### POST /api/audit/restore-user
**Summary:** Restore soft-deleted user  
**Authentication:** Required (admin role)

---

### GET /api/audit/deleted-users
**Summary:** List soft-deleted users  
**Authentication:** Required (admin role)

---

### POST /api/audit/purge-old-deletes
**Summary:** Permanently delete old soft-deleted records  
**Authentication:** Required (admin role)

---

## Utilities

### GET /api/utils/countries
**Summary:** Get list of countries  
**Authentication:** None required

**Response (200):**
```json
[
  {"code": "US", "name": "United States"},
  {"code": "GB", "name": "United Kingdom"}
]
```

---

### GET /api/utils/languages
**Summary:** Get list of languages  
**Authentication:** None required

**Response (200):**
```json
[
  {"code": "en", "name": "English"},
  {"code": "es", "name": "Spanish"}
]
```

---

### GET /api/utils/proficiency-levels
**Summary:** Get language proficiency levels  
**Authentication:** None required

**Response (200):**
```json
["Beginner", "Intermediate", "Advanced", "Native"]
```

---

### GET /api/utils/phone-codes
**Summary:** Get country phone codes  
**Authentication:** None required

**Response (200):**
```json
[
  {"country": "United States", "code": "+1"},
  {"country": "United Kingdom", "code": "+44"}
]
```

---

## Health & Monitoring

### GET /health
**Summary:** System health check  
**Authentication:** None required

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T10:30:00.000Z",
  "database": "connected"
}
```

**Response (503):** Service unavailable
```json
{
  "status": "unhealthy",
  "timestamp": "2025-01-24T10:30:00.000Z",
  "database": "disconnected",
  "error": "Connection timeout"
}
```

---

### GET /api/health/integrity
**Summary:** Data integrity check (admin only)  
**Authentication:** Required (admin role)

**Query Parameters:**
- `repair` (bool, default: false): Auto-repair inconsistencies

**Response (200):**
```json
{
  "status": "healthy",
  "report": {
    "health_status": "healthy",
    "total_users": 1000,
    "role_counts": {
      "student": 800,
      "tutor": 150,
      "admin": 50
    },
    "issues": [],
    "timestamp": "2025-01-24T10:30:00Z"
  }
}
```

---

## WebSocket Endpoints

### WS /ws/{user_id}
**Summary:** WebSocket connection for real-time updates  
**Authentication:** Required (token via query param or first message)

**Connection URL:**
```
ws://localhost:8000/ws/42?token=<jwt_token>
```

**Message Types Received:**
- `new_message`: New message received
- `message_sent`: Message sent from another device
- `booking_update`: Booking status changed
- `notification`: New notification

**Example Message:**
```json
{
  "type": "new_message",
  "message_id": 1,
  "sender_id": 10,
  "sender_email": "tutor@example.com",
  "message": "Hello!",
  "created_at": "2025-01-24T10:30:00Z"
}
```

---

## Rate Limits

| Endpoint Pattern | Limit | Window |
|-----------------|-------|--------|
| `/auth/register` | 5 requests | 1 minute |
| `/auth/login` | 10 requests | 1 minute |
| All other endpoints | 100 requests | 1 minute |

---

## Error Response Format

All errors follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `204`: No Content (success, no response body)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `409`: Conflict (duplicate resource)
- `422`: Unprocessable Entity (validation error)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable

---

## Authentication Flow Example

```javascript
// 1. Register
const registerResponse = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'student@example.com',
    password: 'password123',
    first_name: 'John',
    last_name: 'Doe',
    role: 'student'
  })
});

// 2. Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'student@example.com',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();

// 3. Use token for authenticated requests
const profileResponse = await fetch('http://localhost:8000/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

---

## Additional Resources

- **Interactive API Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

**Last Updated:** January 24, 2026  
**API Version:** 1.0.0
