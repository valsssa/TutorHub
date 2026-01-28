# Booking Flow

This document traces the complete booking flow from tutor discovery to session completion, including creation, confirmation, rescheduling, cancellation, and review.

## Table of Contents
- [Tutor Discovery Flow](#tutor-discovery-flow)
- [Booking Creation Flow](#booking-creation-flow)
- [Booking Confirmation Flow (Tutor)](#booking-confirmation-flow-tutor)
- [Booking Cancellation Flow](#booking-cancellation-flow)
- [Booking Rescheduling Flow](#booking-rescheduling-flow)
- [No-Show Management Flow](#no-show-management-flow)
- [Review Submission Flow](#review-submission-flow)

---

## Tutor Discovery Flow

### 1. Student Browses Tutors

**Frontend Component:** `frontend/app/tutors/page.tsx`

```typescript
// Component loads and fetches tutors with filters
useEffect(() => {
  const loadTutors = async () => {
    const result = await tutors.list({
      subject_id: selectedSubject,
      min_rate: minRate,
      max_rate: maxRate,
      search_query: searchText,
      page: currentPage
    });
    setTutors(result.items);
  };
  loadTutors();
}, [filters, currentPage]);
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 517-549)

**Method:** `tutors.list()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/tutors?page=1&page_size=20&subject_id=5&min_rate=20&max_rate=100`
- **Headers:** `Authorization: Bearer <token>` (optional for public browsing)

**Caching:** Results cached for 1 minute (line 531)

### 3. Backend Fetches Tutors

**File:** `backend/modules/tutor_profile/presentation/api.py`

**Endpoint:** `GET /api/tutors`

**Query Parameters:**
- `subject_id` - Filter by subject
- `min_rate`, `max_rate` - Price range
- `min_rating` - Minimum average rating
- `search_query` - Full-text search
- `page`, `page_size` - Pagination

**Process:**
1. Build query with filters
2. Join with user, subjects, reviews
3. Calculate average rating
4. Apply pagination
5. Return paginated results

**Response:**
```json
{
  "items": [
    {
      "id": 10,
      "user_id": 50,
      "title": "Math Expert",
      "headline": "10 years of teaching experience",
      "hourly_rate": 45.00,
      "average_rating": 4.8,
      "total_reviews": 24,
      "subjects": ["Math", "Physics"],
      "profile_photo_url": "https://...",
      "experience_years": 10
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

### 4. Student Views Tutor Profile

**Frontend Component:** `frontend/app/tutors/[id]/page.tsx`

**API Call:** `tutors.get(tutorId)` or `tutors.getPublic(tutorId)`

Gets full tutor profile including:
- Biography and experience
- Certifications and education
- Available subjects and rates
- Availability schedule
- Reviews and ratings

---

## Booking Creation Flow

### 1. Student Selects Time Slot

**Frontend Component:** `frontend/app/tutors/[id]/book/page.tsx`

```typescript
const handleBooking = async () => {
  const booking = await bookings.create({
    tutor_profile_id: tutorId,
    start_at: selectedDateTime,
    duration_minutes: 60,
    lesson_type: "video_call",
    subject_id: selectedSubject,
    notes_student: studentNotes,
    use_package_id: packageId  // optional
  });
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 744-748)

**Method:** `bookings.create()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/bookings`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
- **Body:**
```json
{
  "tutor_profile_id": 10,
  "start_at": "2025-10-25T14:00:00Z",
  "duration_minutes": 60,
  "lesson_type": "video_call",
  "subject_id": 5,
  "notes_student": "Need help with calculus homework",
  "use_package_id": 12
}
```

### 3. Backend Validates and Creates

**File:** `backend/modules/bookings/presentation/api.py` (lines 97-144)

**Endpoint:** `POST /api/bookings`

**Handler:** `create_booking()`

**Authorization:** Student role required (`_require_role(current_user, "student")`)

**Dependencies:**
- `BookingService` - Business logic layer
- `get_current_user` - Auth dependency
- `get_db` - Database session

### 4. Service Layer Processing

**File:** `backend/modules/bookings/service.py`

**Method:** `BookingService.create_booking()`

**Validation Steps:**
1. **Tutor existence** - Verify tutor profile exists and is approved
2. **Availability check** - Ensure tutor has availability at requested time
3. **Conflict detection** - Check for overlapping bookings
4. **Subject validation** - Verify tutor teaches the requested subject
5. **Package validation** - If using package, verify credits available

**Business Logic:**
1. **Calculate pricing** - Base rate + platform fee (15%)
2. **Deduct package credit** - If package used, decrement remaining_credits
3. **Set initial status** - "PENDING" or "CONFIRMED" (if auto_confirm enabled)
4. **Generate join URL** - Create unique meeting link
5. **Create booking record** - Insert into database

**Database Operations:**
```sql
-- Check conflicts
SELECT id FROM bookings 
WHERE tutor_profile_id = 10 
  AND status IN ('PENDING', 'CONFIRMED')
  AND start_time < '2025-10-25T15:00:00Z'
  AND end_time > '2025-10-25T14:00:00Z';

-- Insert booking
INSERT INTO bookings (
  student_id, tutor_profile_id, subject_id,
  start_time, end_time, duration_minutes,
  lesson_type, status, hourly_rate, platform_fee,
  total_amount, notes_student, join_url
) VALUES (
  42, 10, 5,
  '2025-10-25T14:00:00Z', '2025-10-25T15:00:00Z', 60,
  'video_call', 'PENDING', 45.00, 6.75,
  51.75, 'Need help with calculus', 'https://meet.valsa.solutions/abc123'
);

-- Deduct package credit (if applicable)
UPDATE student_packages 
SET remaining_credits = remaining_credits - 1,
    updated_at = NOW()
WHERE id = 12 AND student_id = 42;
```

### 5. Response Generation

**File:** `backend/modules/bookings/presentation/api.py` (line 134)

**Function:** `booking_to_dto(booking, db)`

Converts database model to DTO with:
- Student and tutor information
- Subject details
- Timing and duration
- Pricing breakdown
- Status and notes

**Response:**
```json
{
  "id": 100,
  "student_id": 42,
  "student_name": "John Doe",
  "student_email": "john@example.com",
  "tutor_profile_id": 10,
  "tutor_name": "Jane Smith",
  "tutor_email": "jane@example.com",
  "subject_id": 5,
  "subject_name": "Mathematics",
  "start_time": "2025-10-25T14:00:00Z",
  "end_time": "2025-10-25T15:00:00Z",
  "duration_minutes": 60,
  "lesson_type": "video_call",
  "status": "PENDING",
  "hourly_rate": 45.00,
  "platform_fee": 6.75,
  "total_amount": 51.75,
  "notes_student": "Need help with calculus",
  "join_url": "https://meet.valsa.solutions/abc123",
  "created_at": "2025-10-21T10:00:00Z",
  "updated_at": "2025-10-21T10:00:00Z"
}
```

### 6. Frontend Handles Success

**File:** `frontend/lib/api.ts` (line 746)

- Clears cache to refresh booking lists
- Component redirects to booking details page
- Shows success notification

---

## Booking Confirmation Flow (Tutor)

### 1. Tutor Views Pending Bookings

**Frontend Component:** `frontend/components/dashboards/TutorDashboard.tsx`

Lists all pending bookings awaiting tutor confirmation.

### 2. Tutor Confirms Booking

```typescript
const handleConfirm = async (bookingId: number) => {
  const confirmed = await bookings.confirm(bookingId, {
    notes_tutor: "Looking forward to our session!"
  });
};
```

### 3. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 771-777)

**Method:** `bookings.confirm()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/tutor/bookings/100/confirm`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
- **Body:**
```json
{
  "notes_tutor": "Looking forward to our session!"
}
```

### 4. Backend Confirms Booking

**File:** `backend/modules/bookings/presentation/api.py` (lines 353-414)

**Endpoint:** `POST /tutor/bookings/{booking_id}/confirm`

**Handler:** `confirm_booking()`

**Authorization:** Tutor profile required (`Depends(get_current_tutor_profile)`)

**Process:**
1. **Verify ownership** - Booking belongs to this tutor
2. **Check status** - Must be in "PENDING" status
3. **Update status** - Change to "CONFIRMED"
4. **Generate join URL** - Create meeting link if not exists
5. **Add tutor notes** - Store optional notes
6. **Update timestamp** - Set updated_at in application code

**Database Operations:**
```sql
UPDATE bookings 
SET status = 'CONFIRMED',
    join_url = 'https://meet.valsa.solutions/abc123',
    notes_tutor = 'Looking forward to our session!',
    updated_at = NOW()
WHERE id = 100 
  AND tutor_profile_id = 10
  AND status = 'PENDING';
```

### 5. Notification Sent

**File:** `backend/modules/bookings/service.py`

Triggers notification to student:
- Email notification (if configured)
- In-app notification
- WebSocket real-time update

---

## Booking Cancellation Flow

### 1. User Initiates Cancellation

**Frontend Component:** Booking details page

```typescript
const handleCancel = async () => {
  const cancelled = await bookings.cancel(bookingId, {
    reason: "Schedule conflict, need to reschedule"
  });
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 753-757)

**Method:** `bookings.cancel()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/bookings/100/cancel`
- **Body:**
```json
{
  "reason": "Schedule conflict, need to reschedule"
}
```

### 3. Backend Processes Cancellation

**File:** `backend/modules/bookings/presentation/api.py` (lines 225-262)

**Endpoint:** `POST /api/bookings/{booking_id}/cancel`

**Handler:** `cancel_booking()`

**Authorization:** Must be student or tutor of the booking

### 4. Service Layer Applies Policy

**File:** `backend/modules/bookings/service.py`

**Method:** `BookingService.cancel_booking()`

**Refund Policy:**
- **>= 12 hours before** - Full refund
- **< 12 hours before** - No refund

**Process:**
1. **Calculate hours until booking** - Compare current time to start_time
2. **Determine refund eligibility** - Apply 12-hour policy
3. **Update booking status** - Set to "CANCELLED_BY_STUDENT" or "CANCELLED_BY_TUTOR"
4. **Process refund** - Restore package credit or initiate payment refund
5. **Add cancellation note** - Store reason

**Database Operations:**
```sql
-- Update booking
UPDATE bookings 
SET status = 'CANCELLED_BY_STUDENT',
    cancellation_reason = 'Schedule conflict',
    cancelled_at = NOW(),
    updated_at = NOW()
WHERE id = 100;

-- Restore package credit (if full refund)
UPDATE student_packages 
SET remaining_credits = remaining_credits + 1,
    updated_at = NOW()
WHERE id = 12 AND student_id = 42;
```

---

## Booking Rescheduling Flow

### 1. Student Requests Reschedule

**Frontend Component:** Booking details page

```typescript
const handleReschedule = async () => {
  const rescheduled = await bookings.reschedule(bookingId, {
    new_start_at: newDateTime
  });
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 762-766)

**Method:** `bookings.reschedule()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/bookings/100/reschedule`
- **Body:**
```json
{
  "new_start_at": "2025-10-26T14:00:00Z"
}
```

### 3. Backend Validates and Reschedules

**File:** `backend/modules/bookings/presentation/api.py` (lines 264-346)

**Endpoint:** `POST /api/bookings/{booking_id}/reschedule`

**Handler:** `reschedule_booking()`

**Authorization:** Student only (`_require_role(current_user, "student")`)

### 4. Policy Engine Evaluation

**File:** `backend/modules/bookings/policy_engine.py`

**Class:** `ReschedulePolicy`

**Method:** `evaluate_reschedule()`

**Validation Rules:**
1. **Minimum notice** - Must be >= 12 hours before original time
2. **Future time** - New time must be in the future
3. **Reasonable timeframe** - New time within 30 days

**Process:**
```python
decision = ReschedulePolicy.evaluate_reschedule(
    booking_start_at=booking.start_time,
    now=datetime.utcnow(),
    new_start_at=request.new_start_at,
)

if not decision.allow:
    raise HTTPException(
        status_code=400,
        detail=decision.message
    )
```

### 5. Conflict Check

**File:** `backend/modules/bookings/service.py`

**Method:** `BookingService.check_conflicts()`

Checks for overlapping bookings at new time:
```sql
SELECT id FROM bookings 
WHERE tutor_profile_id = 10 
  AND id != 100  -- exclude current booking
  AND status IN ('PENDING', 'CONFIRMED')
  AND start_time < '2025-10-26T15:00:00Z'
  AND end_time > '2025-10-26T14:00:00Z';
```

### 6. Update Booking

```sql
UPDATE bookings 
SET start_time = '2025-10-26T14:00:00Z',
    end_time = '2025-10-26T15:00:00Z',
    notes = CONCAT(notes, '\n[Rescheduled at 2025-10-21T10:30:00Z]'),
    updated_at = NOW()
WHERE id = 100;
```

---

## No-Show Management Flow

### 1. Tutor Reports Student No-Show

**Frontend Component:** Booking details page

```typescript
const handleMarkNoShow = async () => {
  const updated = await bookings.markStudentNoShow(bookingId, {
    notes: "Student did not join session"
  });
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 793-799)

**Method:** `bookings.markStudentNoShow()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/tutor/bookings/100/mark-no-show-student`
- **Body:**
```json
{
  "notes": "Student did not join session"
}
```

### 3. Backend Validates Timing

**File:** `backend/modules/bookings/presentation/api.py` (lines 467-516)

**Endpoint:** `POST /tutor/bookings/{booking_id}/mark-no-show-student`

**Handler:** `mark_student_no_show()`

**Authorization:** Tutor profile required

### 4. Service Layer Validation

**File:** `backend/modules/bookings/service.py`

**Method:** `BookingService.mark_no_show()`

**Rules:**
- **Minimum wait time** - Must be >= 10 minutes after start_time
- **Maximum window** - Must report within 24 hours of start_time
- **Status check** - Booking must be in "CONFIRMED" status

**Process:**
1. Validate timing constraints
2. Update status to "NO_SHOW_STUDENT"
3. Tutor receives full payment (no refund to student)
4. Add notes
5. Update metrics (affects student reliability score)

**Database Operations:**
```sql
UPDATE bookings 
SET status = 'NO_SHOW_STUDENT',
    notes_tutor = 'Student did not join session',
    updated_at = NOW()
WHERE id = 100
  AND tutor_profile_id = 10
  AND status = 'CONFIRMED'
  AND start_time < NOW() - INTERVAL '10 minutes'
  AND start_time > NOW() - INTERVAL '24 hours';
```

### 5. Student Reports Tutor No-Show

**Similar process but:**
- Endpoint: `POST /tutor/bookings/{booking_id}/mark-no-show-tutor`
- Authorization: Student only
- Status: "NO_SHOW_TUTOR"
- Student receives full refund
- Affects tutor reliability score

---

## Review Submission Flow

### 1. Student Submits Review

**Frontend Component:** `frontend/app/bookings/[id]/review/page.tsx`

```typescript
const handleSubmit = async () => {
  const review = await reviews.create(
    bookingId,
    rating,  // 1-5 stars
    comment
  );
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 818-831)

**Method:** `reviews.create()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/reviews`
- **Body:**
```json
{
  "booking_id": 100,
  "rating": 5,
  "comment": "Excellent tutor, very helpful with calculus concepts!"
}
```

### 3. Backend Creates Review

**File:** `backend/modules/reviews/presentation/api.py`

**Endpoint:** `POST /api/reviews`

**Validation:**
1. **Booking exists** - Verify booking ID
2. **Authorization** - Only student of booking can review
3. **Booking completed** - Status must be "COMPLETED"
4. **No duplicate** - Student hasn't already reviewed this booking
5. **Rating range** - 1-5 stars

**Database Operations:**
```sql
-- Insert review
INSERT INTO reviews (
  booking_id, reviewer_id, tutor_profile_id,
  rating, comment, created_at
) VALUES (
  100, 42, 10,
  5, 'Excellent tutor!', NOW()
);

-- Update tutor average rating
UPDATE tutor_profile 
SET average_rating = (
  SELECT AVG(rating) 
  FROM reviews 
  WHERE tutor_profile_id = 10
),
total_reviews = total_reviews + 1
WHERE id = 10;
```

### 4. Cache Invalidation

**File:** `frontend/lib/api.ts` (line 828)

Clears cache to refresh tutor ratings and review lists.

---

## Error Handling

### Common Errors

**400 Bad Request**
- Invalid date/time format
- Duration not supported
- Subject not taught by tutor
- Reschedule too close to booking time

**403 Forbidden**
- Not your booking
- Wrong role (student vs tutor)
- Tutor profile not approved

**404 Not Found**
- Booking doesn't exist
- Tutor profile not found

**409 Conflict**
- Time slot already booked
- Tutor not available at requested time
- Conflicting booking exists

**422 Validation Error**
- Missing required fields
- Invalid enum values
- Booking in past

---

## Related Files

### Frontend
- `frontend/app/tutors/page.tsx` - Tutor listing
- `frontend/app/tutors/[id]/page.tsx` - Tutor profile
- `frontend/app/tutors/[id]/book/page.tsx` - Booking form
- `frontend/app/bookings/page.tsx` - Booking list
- `frontend/app/bookings/[id]/review/page.tsx` - Review form
- `frontend/lib/api.ts` - API client methods
- `frontend/types/booking.ts` - TypeScript types

### Backend
- `backend/modules/bookings/presentation/api.py` - Booking endpoints
- `backend/modules/bookings/service.py` - Business logic
- `backend/modules/bookings/schemas.py` - Request/response schemas
- `backend/modules/bookings/policy_engine.py` - Cancellation/reschedule policies
- `backend/modules/reviews/presentation/api.py` - Review endpoints
- `backend/modules/tutor_profile/presentation/api.py` - Tutor endpoints
- `backend/models.py` - Database models

### Database
- `database/init.sql` - Booking table schema
- Table: `bookings`, `reviews`, `tutor_profile`, `student_packages`
