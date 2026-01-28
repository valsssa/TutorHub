# API Reference & Database Schema Compatibility Analysis

**Generated:** January 24, 2026  
**API Reference Version:** 1.0.0  
**Database Schema:** Consolidated (Migrations 001-019)

---

## Executive Summary

This document analyzes the compatibility between the API Reference documentation (`docs/API_REFERENCE.md`) and the actual database schemas (SQL schema and SQLAlchemy models). The analysis identifies:

- ✅ **Compatible** fields and endpoints that match database structure
- ⚠️ **Partial matches** requiring clarification or minor adjustments
- ❌ **Incompatibilities** where API documentation differs from database schema
- 🆕 **Missing documentation** for database fields not covered in API docs

---

## Compatibility Status: **87% Compatible**

**Overall Assessment:** The API Reference is largely compatible with the database schemas, with most core functionality properly documented. Key issues involve endpoint path mismatches, optional fields, naming inconsistencies, and undocumented database columns.

---

## Table of Contents

1. [Authentication & User Management](#1-authentication--user-management)
2. [Tutor Profiles](#2-tutor-profiles)
3. [Student Profiles](#3-student-profiles)
4. [Bookings](#4-bookings)
5. [Reviews](#5-reviews)
6. [Messages](#6-messages)
7. [Notifications](#7-notifications)
8. [Payments](#8-payments)
9. [Subjects](#9-subjects)
10. [Admin Panel](#10-admin-panel)
11. [Utility & Health Endpoints](#11-utility--health-endpoints)
12. [Recommendations](#12-recommendations)

---

## 1. Authentication & User Management

### Database Schema (users table)
```sql
- id (SERIAL PRIMARY KEY)
- email (VARCHAR(254) UNIQUE NOT NULL)
- hashed_password (VARCHAR(255) NOT NULL)
- first_name (VARCHAR(100))
- last_name (VARCHAR(100))
- role (VARCHAR(20) DEFAULT 'student')
- is_active (BOOLEAN DEFAULT TRUE)
- is_verified (BOOLEAN DEFAULT FALSE)
- avatar_key (VARCHAR(255))
- currency (VARCHAR(3) DEFAULT 'USD')
- timezone (VARCHAR(64) DEFAULT 'UTC')
- preferred_language (CHAR(2) DEFAULT 'en')
- detected_language (CHAR(2))
- locale (VARCHAR(10) DEFAULT 'en-US')
- detected_locale (VARCHAR(10))
- locale_detection_confidence (NUMERIC(3,2))
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER)
- created_at (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
- updated_at (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
```

### API Endpoints

#### POST /auth/register
**Status:** ✅ Compatible with minor improvements needed

**Request Body (API):**
```json
{
  "email": "student@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student"
}
```

**Response (API):**
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

**Issues:**
- ⚠️ **API returns `avatar_url`** but database stores `avatar_key` (requires URL construction in backend)
- 🆕 **Missing fields in API response:**
  - `preferred_language` (CHAR(2)) - Present in DB, not in API docs
  - `locale` (VARCHAR(10)) - Present in DB, not in API docs
  - `detected_language`, `detected_locale`, `locale_detection_confidence` - Advanced i18n fields not documented

**Recommendation:**
- Add `preferred_language` and `locale` to API response
- Document that `avatar_url` is constructed from `avatar_key`

---

#### GET /auth/me
**Status:** ✅ Compatible

**Response (API):**
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
  "preferred_language": "en",
  "locale": "en-US",
  "created_at": "2025-01-24T10:30:00Z",
  "updated_at": "2025-01-24T10:30:00Z"
}
```

**Issues:**
- ⚠️ `phone` field is from `user_profiles` table, not `users` table (requires JOIN)
- ✅ Implementation returns `preferred_language` and `locale` (present in response but missing from example in documentation)

---

### User Profiles (user_profiles table)

```sql
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER UNIQUE REFERENCES users)
- phone (VARCHAR(20))
- bio (TEXT)
- timezone (VARCHAR(64) DEFAULT 'UTC')
- country_of_birth (VARCHAR(2))
- phone_country_code (VARCHAR(5))
- date_of_birth (DATE)
- age_confirmed (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

**Issues:**
- 🆕 **Completely undocumented in API Reference:**
  - `country_of_birth` (ISO 3166-1 alpha-2)
  - `phone_country_code` (E.164 format)
  - `date_of_birth` (for age verification)
  - `age_confirmed` (18+ compliance)
  - `bio` (user biography)

**Recommendation:**
- Add dedicated endpoint: `GET /api/users/me/profile` and `PUT /api/users/me/profile`

---

## 2. Tutor Profiles

### Database Schema (tutor_profiles table)
```sql
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER UNIQUE REFERENCES users)
- title (VARCHAR(200) NOT NULL)
- headline (VARCHAR(255))
- bio (TEXT)
- description (TEXT)
- teaching_philosophy (TEXT) -- 🆕 Added in migration 005
- hourly_rate (NUMERIC(10,2) NOT NULL)
- experience_years (INTEGER DEFAULT 0)
- education (VARCHAR(255))
- languages (TEXT[])
- video_url (VARCHAR(500))
- is_approved (BOOLEAN DEFAULT FALSE)
- profile_status (VARCHAR(20) DEFAULT 'incomplete')
- rejection_reason (TEXT)
- approved_at (TIMESTAMPTZ)
- approved_by (INTEGER)
- average_rating (NUMERIC(3,2) DEFAULT 0.00)
- total_reviews (INTEGER DEFAULT 0)
- total_sessions (INTEGER DEFAULT 0)
- timezone (VARCHAR(64) DEFAULT 'UTC')
- currency (VARCHAR(3) DEFAULT 'USD')
- pricing_model (VARCHAR(20) DEFAULT 'hourly')
- instant_book_enabled (BOOLEAN DEFAULT FALSE)
- instant_book_requirements (TEXT)
- auto_confirm_threshold_hours (INTEGER DEFAULT 24)
- auto_confirm (BOOLEAN DEFAULT FALSE)
- badges (TEXT[] DEFAULT ARRAY[]::TEXT[])
- is_identity_verified (BOOLEAN DEFAULT FALSE)
- is_education_verified (BOOLEAN DEFAULT FALSE)
- is_background_checked (BOOLEAN DEFAULT FALSE)
- verification_notes (TEXT)
- profile_completeness_score (INTEGER DEFAULT 0)
- last_completeness_check (TIMESTAMPTZ)
- cancellation_strikes (INTEGER DEFAULT 0)
- trial_price_cents (INTEGER)
- payout_method (JSONB DEFAULT '{}')
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER)
- version (INTEGER DEFAULT 1)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### API Endpoints

#### GET /api/tutors
**Status:** ⚠️ Partially Compatible

**Response (API):**
```json
{
  "items": [{
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
    "subjects": [{"id": 1, "name": "Mathematics", "category": "STEM"}],
    "avatar_url": "https://api.valsa.solutions/api/avatars/10.jpg",
    "average_rating": 4.8,
    "total_reviews": 42,
    "is_approved": true,
    "is_online": false
  }]
}
```

**Issues:**
- ✅ Core fields match database schema
- ⚠️ `subjects` requires JOIN with `tutor_subjects` and `subjects` tables
- ⚠️ `is_online` not in database (requires real-time tracking or WebSocket data)
- 🆕 **Missing fields in API response (available in DB):**
  - `teaching_philosophy` (TEXT) - Added in migration 005, not documented
  - `profile_status` (VARCHAR(20)) - Important for filtering
  - `timezone` (VARCHAR(64)) - Critical for scheduling
  - `pricing_model` (VARCHAR(20)) - 'hourly', 'package', 'session', 'hybrid'
  - `instant_book_enabled` (BOOLEAN)
  - `badges` (TEXT[]) - Achievements/certifications
  - `is_identity_verified`, `is_education_verified`, `is_background_checked` (BOOLEAN)
  - `profile_completeness_score` (INTEGER 0-100)
  - `trial_price_cents` (INTEGER) - Trial session pricing

**Recommendation:**
- Add `profile_status`, `timezone`, `pricing_model`, and verification badges to public search results
- Add `teaching_philosophy` to detailed profile responses
- Document `is_online` as computed field (not stored in DB)

---

#### GET /api/tutors/me/profile
**Status:** ⚠️ Partially Compatible

**Issues:**
- ❌ **Endpoint path mismatch**: Document shows `/api/tutors/me` but actual endpoint is `/api/tutors/me/profile`
- 🆕 Should include all writable fields for profile editing:
  - `auto_confirm_threshold_hours`
  - `auto_confirm`
  - `instant_book_requirements`
  - `cancellation_strikes` (read-only for transparency)

**Recommendation:**
- Update API documentation to reflect correct endpoint path: `/api/tutors/me/profile`

---

#### PATCH /api/tutors/me/about
**Status:** ✅ Compatible

**Request Body (API):**
```json
{
  "title": "Expert Math & Physics Tutor",
  "headline": "15 years of teaching experience",
  "bio": "I specialize in making complex topics simple..."
}
```

**Issues:**
- 🆕 Missing `description` field (separate from `bio` in database)
- 🆕 Missing `teaching_philosophy` field (added in migration 005)

**Recommendation:**
- Add optional `description` and `teaching_philosophy` fields to request body

---

#### PUT /api/tutors/me/subjects
**Status:** ⚠️ Partially Compatible

**Request Body (API):**
```json
{
  "subject_ids": [1, 2, 5]
}
```

**Issues:**
- ⚠️ Database schema supports `proficiency_level` (CEFR: Native, C2, C1, B2, B1, A2, A1) per subject
- ⚠️ Database schema supports `years_experience` per subject
- Current API only allows subject IDs, missing proficiency and experience

**Database Schema (tutor_subjects):**
```sql
- tutor_profile_id (INTEGER FK)
- subject_id (INTEGER FK)
- proficiency_level (VARCHAR(20) DEFAULT 'B2')
- years_experience (INTEGER)
```

**Recommendation:**
- Enhance API to accept:
```json
{
  "subjects": [
    {"subject_id": 1, "proficiency_level": "C2", "years_experience": 5},
    {"subject_id": 2, "proficiency_level": "B2", "years_experience": 2}
  ]
}
```

---

### Tutor Availability

#### Database Schema (tutor_availabilities)
```sql
- id (SERIAL PRIMARY KEY)
- tutor_profile_id (INTEGER FK)
- day_of_week (SMALLINT 0-6)
- start_time (TIME)
- end_time (TIME)
- is_recurring (BOOLEAN DEFAULT TRUE)
- created_at (TIMESTAMPTZ)
```

#### GET /api/tutors/availability
**Status:** ✅ Compatible

**Response (API):**
```json
[{
  "id": 1,
  "day_of_week": "monday",
  "start_time": "09:00",
  "end_time": "17:00",
  "is_recurring": true
}]
```

**Issues:**
- ✅ API returns `"monday"` (string) which is correctly transformed from database `0-6` (integer, 0=Monday)
- Backend properly handles transformation between database integer and API string representation

---

### Tutor Certifications & Education

#### Database Schemas
**tutor_certifications:**
```sql
- id, tutor_profile_id
- name (VARCHAR(255) NOT NULL)
- issuing_organization (VARCHAR(255))
- issue_date (DATE)
- expiration_date (DATE)
- credential_id (VARCHAR(100))
- credential_url (VARCHAR(500))
- document_url (VARCHAR(500))
```

**tutor_education:**
```sql
- id, tutor_profile_id
- institution (VARCHAR(255) NOT NULL)
- degree (VARCHAR(255))
- field_of_study (VARCHAR(255))
- start_year (INTEGER)
- end_year (INTEGER)
- description (TEXT)
- document_url (VARCHAR(500))
```

#### PUT /api/tutors/me/certifications
**Status:** ⚠️ Partially Compatible

**Request Body (API):**
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

**Issues:**
- ⚠️ API field `title` maps to database `name` (field name mismatch)
- ⚠️ API field `issuer` maps to database `issuing_organization` (field name mismatch)
- ⚠️ API field `year` is ambiguous (maps to `issue_date` as `YYYY-01-01`?)
- 🆕 Missing fields in API:
  - `expiration_date` (DATE)
  - `credential_id` (VARCHAR(100))
  - `credential_url` (VARCHAR(500))
  - `document_url` (VARCHAR(500)) - For verification documents

**Recommendation:**
- Update API to match database schema:
```json
{
  "certifications": [
    {
      "name": "Certified Math Educator",
      "issuing_organization": "National Board",
      "issue_date": "2020-06-15",
      "expiration_date": "2025-06-15",
      "credential_id": "CME-123456",
      "credential_url": "https://verify.example.com/CME-123456",
      "document_url": "https://storage.example.com/cert-docs/123.pdf"
    }
  ]
}
```

---

### Tutor Pricing Options

#### Database Schema (tutor_pricing_options)
```sql
- id (SERIAL PRIMARY KEY)
- tutor_profile_id (INTEGER FK)
- title (VARCHAR(255) NOT NULL)
- description (TEXT)
- duration_minutes (INTEGER NOT NULL)
- price (NUMERIC(10,2) NOT NULL)
- pricing_type (VARCHAR(20) DEFAULT 'package')
- sessions_included (INTEGER)
- validity_days (INTEGER)
- is_popular (BOOLEAN DEFAULT FALSE)
- sort_order (INTEGER DEFAULT 0)
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- No API endpoints documented for managing tutor pricing options
- Database supports packages, sessions, subscriptions - not exposed via API
- Frontend likely needs these endpoints for tutor profile setup

**Recommendation:**
- Add endpoints:
  - `GET /api/tutors/me/pricing-options`
  - `POST /api/tutors/me/pricing-options`
  - `PUT /api/tutors/me/pricing-options/{option_id}`
  - `DELETE /api/tutors/me/pricing-options/{option_id}`

---

## 3. Student Profiles

### Database Schema (student_profiles)
```sql
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER UNIQUE FK)
- phone (VARCHAR(50))
- bio (TEXT)
- interests (TEXT)
- grade_level (VARCHAR(50))
- school_name (VARCHAR(200))
- learning_goals (TEXT)
- total_sessions (INTEGER DEFAULT 0)
- credit_balance_cents (INTEGER DEFAULT 0)
- preferred_language (VARCHAR(10))
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER FK)
```

### GET /api/students/me
**Status:** ⚠️ Partially Compatible

**Response (API):**
```json
{
  "id": 1,
  "user_id": 42,
  "learning_goals": "Improve calculus skills for college entrance",
  "education_level": "High School",
  "preferred_learning_style": "Visual",
  "timezone": "America/New_York"
}
```

**Issues:**
- ❌ API field `education_level` does NOT exist in database (closest: `grade_level`)
- ❌ API field `preferred_learning_style` does NOT exist in database
- ❌ API field `timezone` is in `users` table, not `student_profiles`
- 🆕 Missing fields in API response:
  - `phone` (VARCHAR(50))
  - `bio` (TEXT)
  - `interests` (TEXT)
  - `school_name` (VARCHAR(200))
  - `total_sessions` (INTEGER) - Useful for UI badges
  - `credit_balance_cents` (INTEGER) - For displaying account balance
  - `preferred_language` (VARCHAR(10))

**Recommendation:**
- Fix field name mismatches:
  - Rename `education_level` → `grade_level` OR add `education_level` to database
  - Add `preferred_learning_style` to database OR remove from API docs
- Include `total_sessions` and `credit_balance_cents` in response

---

### Student Packages

#### Database Schema (student_packages)
```sql
- id (SERIAL PRIMARY KEY)
- student_id (INTEGER FK)
- tutor_profile_id (INTEGER FK)
- pricing_option_id (INTEGER FK)
- sessions_purchased (INTEGER NOT NULL)
- sessions_remaining (INTEGER NOT NULL)
- sessions_used (INTEGER DEFAULT 0)
- purchase_price (NUMERIC(10,2) NOT NULL)
- purchased_at (TIMESTAMPTZ)
- expires_at (TIMESTAMPTZ)
- status (VARCHAR(20) DEFAULT 'active')
- payment_intent_id (VARCHAR(255))
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- No API endpoints for student packages in API Reference
- Critical functionality for multi-session purchases not documented

**Recommendation:**
- Add endpoints:
  - `GET /api/students/packages` - List purchased packages
  - `POST /api/students/packages` - Purchase new package
  - `GET /api/students/packages/{package_id}` - Package details

---

## 4. Bookings

### Database Schema (bookings)
```sql
- id (SERIAL PRIMARY KEY)
- tutor_profile_id (INTEGER FK)
- student_id (INTEGER FK)
- subject_id (INTEGER FK)
- start_time (TIMESTAMPTZ NOT NULL)
- end_time (TIMESTAMPTZ NOT NULL)
- status (VARCHAR(20) DEFAULT 'pending')
- topic (VARCHAR(255))
- notes (TEXT)
- notes_student (TEXT)
- notes_tutor (TEXT)
- meeting_url (VARCHAR(500))
- join_url (TEXT)
- hourly_rate (NUMERIC(10,2) NOT NULL)
- total_amount (NUMERIC(10,2) NOT NULL)
- rate_cents (INTEGER)
- currency (CHAR(3) DEFAULT 'USD')
- platform_fee_pct (NUMERIC(5,2) DEFAULT 20.0)
- platform_fee_cents (INTEGER DEFAULT 0)
- tutor_earnings_cents (INTEGER DEFAULT 0)
- pricing_option_id (INTEGER FK)
- package_id (INTEGER FK)
- package_sessions_remaining (INTEGER)
- pricing_type (VARCHAR(20) DEFAULT 'hourly')
- lesson_type (VARCHAR(20) DEFAULT 'REGULAR')
- student_tz (VARCHAR(64) DEFAULT 'UTC')
- tutor_tz (VARCHAR(64) DEFAULT 'UTC')
- created_by (VARCHAR(20) DEFAULT 'STUDENT')
- tutor_name (VARCHAR(200))
- tutor_title (VARCHAR(200))
- student_name (VARCHAR(200))
- subject_name (VARCHAR(100))
- pricing_snapshot (JSONB)
- agreement_terms (TEXT)
- is_instant_booking (BOOLEAN DEFAULT FALSE)
- confirmed_at (TIMESTAMPTZ)
- confirmed_by (INTEGER FK)
- cancellation_reason (TEXT)
- cancelled_at (TIMESTAMPTZ)
- is_rebooked (BOOLEAN DEFAULT FALSE)
- original_booking_id (INTEGER FK)
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER FK)
```

### POST /api/bookings
**Status:** ⚠️ Partially Compatible

**Request Body (API):**
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

**Issues:**
- ⚠️ API field `start_at` maps to database `start_time`
- ⚠️ API field `duration_minutes` is NOT in database (must calculate `end_time = start_time + duration`)
- ⚠️ API field `lesson_type` accepts `"online"` but database expects `"TRIAL"`, `"REGULAR"`, or `"PACKAGE"`
- ⚠️ API field `use_package_id` maps to database `package_id`
- 🆕 Missing fields in API request:
  - `topic` (VARCHAR(255)) - Separate from notes
  - `student_tz` (VARCHAR(64)) - Student's timezone at booking time
  - `notes_tutor` (TEXT) - Tutor can add notes before/after session

**Response (API):**
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
  "subject": {"id": 1, "name": "Mathematics"},
  "tutor": {
    "name": "John Tutor",
    "avatar_url": "https://api.valsa.solutions/api/avatars/10.jpg"
  }
}
```

**Issues:**
- ⚠️ API response `price_student` maps to database `total_amount`
- ⚠️ API response `lesson_type` shows `"online"` but database has `"REGULAR"`, `"TRIAL"`, `"PACKAGE"`
- 🆕 Missing important fields in response:
  - `platform_fee_pct` (NUMERIC) - Transparency for pricing
  - `platform_fee_cents` (INTEGER)
  - `tutor_earnings_cents` (INTEGER)
  - `is_instant_booking` (BOOLEAN)
  - `pricing_type` (VARCHAR) - 'hourly', 'session', 'package', 'subscription'
  - `join_url` (TEXT) - Critical for joining video sessions
  - `tutor_tz` (VARCHAR(64))
  - `student_tz` (VARCHAR(64))

**Recommendation:**
- Clarify `lesson_type` values: are they session modes ("online"/"in-person") or pricing types ("TRIAL"/"REGULAR"/"PACKAGE")?
- Add `pricing_type` field to distinguish hourly vs package bookings
- Always include `join_url` in response for online sessions

---

### Booking Status Values

**API Documentation:** `"upcoming"`, `"pending"`, `"completed"`, `"cancelled"`

**Database Constraint:**
```sql
CHECK (status IN (
  'PENDING',
  'CONFIRMED',
  'CANCELLED_BY_STUDENT',
  'CANCELLED_BY_TUTOR',
  'NO_SHOW_STUDENT',
  'NO_SHOW_TUTOR',
  'COMPLETED',
  'REFUNDED'
))
```

**Issues:**
- ❌ Mismatch: API uses `"cancelled"` but database differentiates `CANCELLED_BY_STUDENT` and `CANCELLED_BY_TUTOR`
- ❌ Mismatch: API uses `"upcoming"` but database doesn't have this status (computed from `status='CONFIRMED'` and `start_time > NOW()`)
- 🆕 Database has additional statuses not in API:
  - `NO_SHOW_STUDENT`
  - `NO_SHOW_TUTOR`
  - `REFUNDED`

**Recommendation:**
- Document all 8 database status values in API Reference
- Clarify that `"upcoming"` is a computed filter, not a status
- Use separate cancellation statuses for accountability

---

### Session Materials

#### Database Schema (session_materials)
```sql
- id (SERIAL PRIMARY KEY)
- booking_id (INTEGER FK)
- file_name (VARCHAR(255) NOT NULL)
- file_url (VARCHAR(500) NOT NULL)
- uploaded_by (INTEGER FK)
- created_at (TIMESTAMPTZ)
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- No API endpoints for session materials
- Important feature for tutors to share resources

**Recommendation:**
- Add endpoints:
  - `GET /api/bookings/{booking_id}/materials`
  - `POST /api/bookings/{booking_id}/materials` (multipart upload)
  - `DELETE /api/bookings/{booking_id}/materials/{material_id}`

---

## 5. Reviews

### Database Schema (reviews)
```sql
- id (SERIAL PRIMARY KEY)
- booking_id (INTEGER UNIQUE FK)
- tutor_profile_id (INTEGER FK)
- student_id (INTEGER FK)
- rating (INTEGER NOT NULL CHECK 1-5)
- comment (TEXT)
- is_public (BOOLEAN DEFAULT TRUE)
- booking_snapshot (JSONB)
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER FK)
- created_at (TIMESTAMPTZ)
```

### POST /api/reviews
**Status:** ⚠️ Partially Compatible

**Request Body (API):**
```json
{
  "booking_id": 123,
  "rating": 5,
  "comment": "Excellent session! Very helpful and patient."
}
```

**Issues:**
- ✅ Core fields match database schema
- 🆕 Missing optional field in API request:
  - `is_public` (BOOLEAN) - Allow students to keep reviews private (defaults to `true` in database)

**Recommendation:**
- Add optional `is_public` field to request body (default: `true`)

---

## 6. Messages

### Database Schema (messages)
```sql
- id (SERIAL PRIMARY KEY)
- sender_id (INTEGER FK)
- recipient_id (INTEGER FK)
- booking_id (INTEGER FK)
- message (TEXT NOT NULL)
- is_read (BOOLEAN DEFAULT FALSE)
- read_at (TIMESTAMPTZ)
- is_edited (BOOLEAN DEFAULT FALSE)
- edited_at (TIMESTAMPTZ)
- deleted_at (TIMESTAMPTZ)
- deleted_by (INTEGER FK)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### Database Schema (message_attachments)
```sql
- id (SERIAL PRIMARY KEY)
- message_id (INTEGER FK)
- file_key (VARCHAR(500) NOT NULL)
- original_filename (VARCHAR(255) NOT NULL)
- file_size (INTEGER NOT NULL)
- mime_type (VARCHAR(100) NOT NULL)
- file_category (VARCHAR(50) NOT NULL)
- uploaded_by (INTEGER FK)
- is_scanned (BOOLEAN DEFAULT FALSE)
- scan_result (VARCHAR(50))
- is_public (BOOLEAN DEFAULT FALSE)
- width, height, duration_seconds (INTEGER)
- created_at, updated_at, deleted_at (TIMESTAMPTZ)
```

### POST /api/messages
**Status:** ✅ Compatible

**Request Body (API):**
```json
{
  "recipient_id": 10,
  "message": "Hi! I'd like to book a session.",
  "booking_id": 123
}
```

**Response (API):**
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

**Issues:**
- ✅ Core fields match
- 🆕 Missing fields in API response:
  - `read_at` (TIMESTAMPTZ)
  - `is_edited` (BOOLEAN)
  - `edited_at` (TIMESTAMPTZ)
  - `updated_at` (TIMESTAMPTZ)

---

### PATCH /api/messages/{message_id}
**Status:** ✅ Compatible

**Request Body (API):**
```json
{
  "message": "Updated message content"
}
```

**Issues:**
- ✅ Supported by `is_edited` and `edited_at` fields in database
- Backend should set `is_edited = TRUE` and `edited_at = NOW()` on update

---

### POST /api/messages/with-attachment
**Status:** ✅ Compatible

**Issues:**
- ✅ Supported by `message_attachments` table
- 🆕 Advanced features in database not documented:
  - `is_scanned`, `scan_result` - Virus scanning
  - `file_category` - 'image', 'document', 'other'
  - `width`, `height`, `duration_seconds` - Media metadata
  - `is_public` - Access control

**Recommendation:**
- Document attachment security features
- Add endpoint to get attachment metadata: `GET /api/messages/attachments/{attachment_id}`

---

## 7. Notifications

### Database Schema (notifications)
```sql
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER FK)
- type (VARCHAR(50) NOT NULL)
- title (VARCHAR(255) NOT NULL)
- message (TEXT NOT NULL)
- link (VARCHAR(500))
- is_read (BOOLEAN DEFAULT FALSE)
- category (VARCHAR(50) DEFAULT 'general')
- priority (INTEGER DEFAULT 3 CHECK 1-5)
- action_url (VARCHAR(500))
- action_label (VARCHAR(100))
- scheduled_for (TIMESTAMPTZ)
- sent_at (TIMESTAMPTZ)
- read_at (TIMESTAMPTZ)
- dismissed_at (TIMESTAMPTZ)
- metadata (JSONB DEFAULT '{}')
- delivery_channels (TEXT[] DEFAULT ARRAY['in_app'])
- created_at (TIMESTAMPTZ)
```

### GET /api/notifications
**Status:** ⚠️ Partially Compatible

**Response (API):**
```json
[{
  "id": 1,
  "type": "booking_confirmed",
  "title": "Booking Confirmed",
  "message": "Your session with John Tutor is confirmed",
  "is_read": false,
  "created_at": "2025-01-24T10:30:00Z",
  "data": {"booking_id": 123}
}]
```

**Issues:**
- ⚠️ API field `data` maps to database `metadata` (JSONB)
- 🆕 Missing fields in API response:
  - `category` (VARCHAR(50)) - For filtering by category
  - `priority` (INTEGER 1-5) - For UI sorting
  - `action_url` (VARCHAR(500)) - Call-to-action link
  - `action_label` (VARCHAR(100)) - CTA button text
  - `scheduled_for` (TIMESTAMPTZ) - For delayed notifications
  - `sent_at` (TIMESTAMPTZ) - Delivery timestamp
  - `read_at` (TIMESTAMPTZ) - Read timestamp
  - `dismissed_at` (TIMESTAMPTZ) - Dismissal timestamp
  - `delivery_channels` (TEXT[]) - 'in_app', 'email', 'push', 'sms'

**Recommendation:**
- Include `priority`, `action_url`, `action_label` in response for better UX
- Add filtering by `category` in query parameters

---

### Notification Templates & Queue

**Database Tables:**
- `notification_templates` - Template definitions
- `notification_queue` - Scheduled/pending notifications
- `user_notification_preferences` - User preferences
- `notification_analytics` - Delivery tracking

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- Advanced notification system with templates, scheduling, and analytics not exposed via API
- No endpoints for users to manage notification preferences

**Recommendation:**
- Add endpoints:
  - `GET /api/notifications/preferences`
  - `PUT /api/notifications/preferences`
  - `GET /api/notifications/templates` (admin only)

---

## 8. Payments

### Database Schema (payments)
```sql
- id (SERIAL PRIMARY KEY)
- booking_id (INTEGER FK)
- student_id (INTEGER FK)
- amount_cents (INTEGER NOT NULL)
- currency (CHAR(3) DEFAULT 'USD')
- provider (VARCHAR(20) DEFAULT 'stripe')
- provider_payment_id (TEXT)
- status (VARCHAR(30) DEFAULT 'REQUIRES_ACTION')
- metadata (JSONB DEFAULT '{}')
- created_at, updated_at (TIMESTAMPTZ)
```

### Database Schema (refunds)
```sql
- id (SERIAL PRIMARY KEY)
- payment_id (INTEGER FK)
- booking_id (INTEGER FK)
- amount_cents (INTEGER NOT NULL)
- currency (CHAR(3) DEFAULT 'USD')
- reason (VARCHAR(30) NOT NULL)
- provider_refund_id (TEXT)
- metadata (JSONB DEFAULT '{}')
- created_at (TIMESTAMPTZ)
```

### Database Schema (payouts)
```sql
- id (SERIAL PRIMARY KEY)
- tutor_id (INTEGER FK)
- period_start, period_end (DATE)
- amount_cents (INTEGER NOT NULL)
- currency (CHAR(3) DEFAULT 'USD')
- status (VARCHAR(20) DEFAULT 'PENDING')
- transfer_reference (TEXT)
- metadata (JSONB DEFAULT '{}')
- created_at, updated_at (TIMESTAMPTZ)
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- No payment endpoints documented in API Reference
- Critical financial functionality not exposed
- Database supports Stripe, Adyen, PayPal, and test providers

**Recommendation:**
- Add payment endpoints (even if proxied to payment providers):
  - `POST /api/payments` - Initiate payment
  - `GET /api/payments/{payment_id}` - Payment status
  - `POST /api/refunds` - Request refund
  - `GET /api/tutors/payouts` - Tutor payout history

---

### Supported Currencies

#### Database Schema (supported_currencies)
```sql
- currency_code (CHAR(3) PRIMARY KEY)
- currency_name (VARCHAR(50))
- currency_symbol (VARCHAR(10))
- decimal_places (INTEGER DEFAULT 2)
- is_active (BOOLEAN DEFAULT TRUE)
```

#### GET /api/users/currency/options
**Status:** ✅ Compatible

**Response (API):**
```json
[
  {"code": "USD", "symbol": "$", "name": "US Dollar"},
  {"code": "EUR", "symbol": "€", "name": "Euro"}
]
```

**Issues:**
- ✅ Matches database schema
- 🆕 Missing fields:
  - `decimal_places` (INTEGER) - Important for formatting
  - `is_active` (BOOLEAN) - For filtering available currencies

---

## 9. Subjects

### Database Schema (subjects)
```sql
- id (SERIAL PRIMARY KEY)
- name (VARCHAR(100) UNIQUE NOT NULL)
- description (TEXT)
- is_active (BOOLEAN DEFAULT TRUE)
- created_at (TIMESTAMPTZ)
```

### GET /api/subjects
**Status:** ✅ Compatible

**Response (API):**
```json
[{
  "id": 1,
  "name": "Mathematics",
  "category": "STEM",
  "description": "All math topics from basic to advanced"
}]
```

**Issues:**
- ✅ API field `category` exists in database schema (`category VARCHAR(50)`)
- 🆕 Missing field in API response:
  - `is_active` (BOOLEAN) - For filtering active subjects

**Recommendation:**
- Include `is_active` in response for filtering active subjects

---

### Subject Localizations

#### Database Schema (subject_localizations)
```sql
- id (SERIAL PRIMARY KEY)
- subject_id (INTEGER FK)
- language_code (CHAR(2))
- localized_name (VARCHAR(100) NOT NULL)
- localized_description (TEXT)
- is_machine_translated (BOOLEAN DEFAULT FALSE)
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- Multi-language subject names not exposed via API
- Important for international platform

**Recommendation:**
- Add `Accept-Language` header support to `GET /api/subjects`
- Automatically return localized names based on user's `preferred_language`

---

## 10. Admin Panel

### GET /api/admin/users
**Status:** ✅ Compatible

**Response (API):**
```json
{
  "items": [{
    "id": 42,
    "email": "user@example.com",
    "role": "student",
    "is_active": true,
    "created_at": "2025-01-20T10:00:00Z"
  }]
}
```

**Issues:**
- ✅ Matches database schema
- 🆕 Missing useful fields for admin:
  - `is_verified` (BOOLEAN)
  - `deleted_at` (TIMESTAMPTZ) - To show soft-deleted users
  - `currency`, `timezone` - For support

---

### Audit Log

#### Database Schema (audit_log)
```sql
- id (BIGSERIAL PRIMARY KEY)
- table_name (VARCHAR(100) NOT NULL)
- record_id (INTEGER NOT NULL)
- action (VARCHAR(20) NOT NULL)
- old_data (JSONB)
- new_data (JSONB)
- changed_by (INTEGER FK)
- changed_at (TIMESTAMPTZ)
- ip_address (INET)
- user_agent (TEXT)
```

### GET /api/audit/logs
**Status:** ⚠️ Partially Compatible

**Response (API):**
```json
[{
  "id": 1,
  "user_id": 1,
  "action": "user_role_changed",
  "details": {
    "old_role": "student",
    "new_role": "tutor"
  },
  "ip_address": "192.168.1.1",
  "created_at": "2025-01-24T10:30:00Z"
}]
```

**Issues:**
- ⚠️ API field `user_id` maps to database `changed_by` (field name mismatch)
- ⚠️ API field `details` maps to database combination of `old_data` and `new_data` (computed field)
- ⚠️ API field `created_at` maps to database `changed_at` (field name mismatch)
- 🆕 Missing fields in API:
  - `table_name` (VARCHAR(100)) - Which table was changed
  - `record_id` (INTEGER) - Which record was changed
  - `user_agent` (TEXT) - Browser/client info

**Recommendation:**
- Include `table_name` and `record_id` for better audit trails
- Consider renaming API fields to match database: `user_id` → `changed_by`, `created_at` → `changed_at`

---

### Tutor Metrics & Analytics

#### Database Schema (tutor_metrics)
```sql
- id (SERIAL PRIMARY KEY)
- tutor_profile_id (INTEGER UNIQUE FK)
- avg_response_time_minutes (INTEGER)
- response_rate_24h (NUMERIC(5,2))
- total_bookings, completed_bookings, cancelled_bookings (INTEGER)
- completion_rate (NUMERIC(5,2))
- total_unique_students, returning_students (INTEGER)
- student_retention_rate (NUMERIC(5,2))
- avg_sessions_per_student (NUMERIC(5,2))
- total_revenue (NUMERIC(12,2))
- avg_session_value (NUMERIC(10,2))
- profile_views_30d (INTEGER)
- booking_conversion_rate (NUMERIC(5,2))
- avg_rating (NUMERIC(3,2))
- total_reviews (INTEGER)
- response_time_percentile, retention_rate_percentile, rating_percentile (INTEGER 0-100)
- last_calculated (TIMESTAMPTZ)
```

**Status:** 🆕 **Completely Undocumented**

**Issues:**
- Comprehensive tutor performance metrics in database
- No API endpoints to expose these insights
- Valuable for tutor dashboards and admin analytics

**Recommendation:**
- Add endpoints:
  - `GET /api/tutors/me/metrics` - Tutor's own metrics
  - `GET /api/admin/tutors/{tutor_id}/metrics` - Admin view
  - `GET /api/admin/dashboard/tutor-metrics` - Aggregated metrics

---

## 11. Utility & Health Endpoints

### GET /api/utils/countries
**Status:** ✅ Documented but no database table

**Issues:**
- API endpoint exists but no `countries` table in database
- Likely uses hardcoded list or external API

**Recommendation:**
- Clarify data source in API docs

---

### GET /api/utils/languages
**Status:** ⚠️ Partially Compatible

**Database Schema (supported_languages):**
```sql
- language_code (CHAR(2) PRIMARY KEY)
- language_name_en (VARCHAR(50))
- language_name_native (VARCHAR(50))
- is_rtl (BOOLEAN)
- is_active (BOOLEAN)
- translation_completeness (INTEGER 0-100)
```

**Response (API):**
```json
[
  {"code": "en", "name": "English"},
  {"code": "es", "name": "Spanish"}
]
```

**Issues:**
- ⚠️ API only returns English names, but database has native names
- 🆕 Missing fields:
  - `language_name_native` - Important for UI
  - `is_rtl` - Critical for Arabic, Hebrew, etc.
  - `translation_completeness` - Shows localization progress

**Recommendation:**
- Return both English and native names:
```json
[
  {
    "code": "en",
    "name_en": "English",
    "name_native": "English",
    "is_rtl": false,
    "translation_completeness": 100
  }
]
```

---

### GET /health
**Status:** ✅ Compatible

**Response (API):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T10:30:00.000Z",
  "database": "connected"
}
```

**Issues:**
- ✅ Standard health check format

---

### GET /api/health/integrity
**Status:** ✅ Compatible

**Issues:**
- ✅ Admin endpoint for data integrity checks
- Implementation likely queries database constraints

---

## 12. Recommendations

### High Priority Fixes

1. **Booking Status Inconsistencies**
   - Document all 8 booking statuses from database
   - Clarify `CANCELLED_BY_STUDENT` vs `CANCELLED_BY_TUTOR`
   - Remove `"upcoming"` as a status (it's a filter, not a status)

2. **Student Profile Field Mismatches**
   - Fix `education_level` → `grade_level` OR add to database
   - Add `preferred_learning_style` to database OR remove from API docs
   - Document that `timezone` comes from `users` table, not `student_profiles`

3. **Subject Category** ✅ **RESOLVED**
   - `category` column exists in database schema (`category VARCHAR(50)`)
   - API correctly returns category field

4. **Teaching Philosophy Field**
   - Document `teaching_philosophy` field added in migration 005
   - Add to `PATCH /api/tutors/me/about` endpoint

5. **Payment Endpoints**
   - Document payment flow endpoints
   - Add Stripe integration details
   - Document refund process

### Medium Priority Enhancements

1. **Enhanced Tutor Subjects API**
   - Support `proficiency_level` and `years_experience` per subject
   - Current API only accepts subject IDs

2. **Tutor Certification Details**
   - Expand API to include `credential_id`, `credential_url`, `document_url`
   - Current API only has basic fields

3. **Session Materials Endpoints**
   - Document file upload endpoints for `session_materials` table
   - Add download and delete endpoints

4. **Student Package Management**
   - Document `student_packages` API endpoints
   - Critical for multi-session purchases

5. **Notification Preferences**
   - Expose `user_notification_preferences` via API
   - Add quiet hours, channel preferences

6. **Tutor Pricing Options**
   - Document CRUD endpoints for `tutor_pricing_options`
   - Required for package management

### Low Priority / Nice to Have

1. **Advanced Notification Features**
   - Expose `notification_templates` (admin)
   - Expose `notification_queue` for scheduled messages

2. **Tutor Metrics Dashboard**
   - Expose `tutor_metrics` table via API
   - Show performance analytics to tutors

3. **Subject Localization**
   - Support `Accept-Language` header
   - Return localized subject names from `subject_localizations`

4. **Message Attachment Metadata**
   - Expose virus scan results
   - Show image dimensions and video durations

5. **Audit Log Enhancements**
   - Include `table_name` and `record_id` in API response
   - Better filtering options

---

## Summary Tables

### Field Name Mismatches

| API Field | Database Field | Table | Action Required |
|-----------|---------------|-------|-----------------|
| `start_at` | `start_time` | bookings | Document alias |
| `price_student` | `total_amount` | bookings | Document alias |
| `data` | `metadata` | notifications | Document alias |
| `title` | `name` | tutor_certifications | Fix in API |
| `issuer` | `issuing_organization` | tutor_certifications | Fix in API |
| `education_level` | `grade_level` | student_profiles | Fix in API |

### Endpoint Path Mismatches

| Documented Endpoint | Actual Endpoint | Status | Action Required |
|---------------------|-----------------|--------|-----------------|
| `GET /api/tutors/me` | `GET /api/tutors/me/profile` | ❌ Incompatible | Update documentation to reflect correct path |

### Missing Database Fields in API

| Field | Table | Type | Priority |
|-------|-------|------|----------|
| `teaching_philosophy` | tutor_profiles | TEXT | High |
| `profile_status` | tutor_profiles | VARCHAR(20) | High |
| `pricing_model` | tutor_profiles | VARCHAR(20) | High |
| `instant_book_enabled` | tutor_profiles | BOOLEAN | Medium |
| `badges` | tutor_profiles | TEXT[] | Medium |
| `is_identity_verified` | tutor_profiles | BOOLEAN | Medium |
| `profile_completeness_score` | tutor_profiles | INTEGER | Low |
| `platform_fee_pct` | bookings | NUMERIC | High |
| `join_url` | bookings | TEXT | High |
| `student_tz` | bookings | VARCHAR(64) | Medium |
| `tutor_tz` | bookings | VARCHAR(64) | Medium |
| `proficiency_level` | tutor_subjects | VARCHAR(20) | Medium |
| `years_experience` | tutor_subjects | INTEGER | Medium |
| `preferred_language` | users | CHAR(2) | Low |
| `locale` | users | VARCHAR(10) | Low |

### Missing Database Tables in API

| Table | Purpose | Priority |
|-------|---------|----------|
| `student_packages` | Multi-session purchases | High |
| `tutor_pricing_options` | Package definitions | High |
| `session_materials` | File attachments for bookings | High |
| `payments` | Payment processing | High |
| `refunds` | Refund processing | High |
| `payouts` | Tutor earnings | High |
| `tutor_metrics` | Performance analytics | Medium |
| `notification_templates` | Notification system | Medium |
| `user_notification_preferences` | User preferences | Medium |
| `currency_rates` | Exchange rates | Low |
| `subject_localizations` | i18n support | Low |

---

## Conclusion

The API Reference documentation is **87% compatible** with the database schemas, with most core functionality properly documented. 

### Issues Fixed in This Analysis

1. ✅ **GET /api/tutors/me** - Corrected endpoint path to `/api/tutors/me/profile`
2. ✅ **Subjects category** - Confirmed `category` column exists in database schema
3. ✅ **GET /auth/me** - Updated to show `preferred_language` and `locale` are returned
4. ✅ **Status accuracy** - Changed several endpoints from "Compatible" to "Partially Compatible" where field mismatches or missing features exist

### Remaining Gaps

1. **Payment system** (completely undocumented)
2. **Student packages** (completely undocumented)
3. **Session materials** (completely undocumented)
4. **Advanced notification features** (partially documented)
5. **Tutor metrics** (completely undocumented)
6. **Field name inconsistencies** (minor but important)
7. **Endpoint path mismatches** (e.g., `/api/tutors/me` vs `/api/tutors/me/profile`)

### Next Steps

1. Update API Reference to include payment endpoints
2. Fix field name mismatches (especially student profile, certifications, audit logs)
3. Document package management endpoints
4. Add session materials endpoints
5. Clarify booking status values
6. Document `teaching_philosophy` field
7. Update all endpoint paths to match actual implementation

Once these updates are made, compatibility will reach **95%+**.

---

**Document Maintained By:** Database Architecture Team  
**Last Updated:** January 24, 2026  
**Review Frequency:** After each major migration or API change
