# Tutor Onboarding Flow

This document traces the complete tutor onboarding flow from registration to profile approval and activation, including profile creation, document uploads, and admin review.

## Table of Contents
- [Initial Registration](#initial-registration)
- [Profile Builder Flow](#profile-builder-flow)
- [Subject and Pricing Configuration](#subject-and-pricing-configuration)
- [Document Upload Flow](#document-upload-flow)
- [Availability Setup](#availability-setup)
- [Profile Submission](#profile-submission)
- [Admin Review and Approval](#admin-review-and-approval)

---

## Initial Registration

### 1. User Registers as Tutor

**Frontend Component:** `frontend/app/(public)/register/page.tsx`

```typescript
const handleRegister = async () => {
  const user = await auth.register(
    email,
    password,
    firstName,
    lastName,
    "tutor",  // Role selection
    timezone,
    currency
  );
  
  // Redirect to onboarding
  router.push('/tutor/onboarding');
};
```

### 2. Backend Creates Tutor Profile

**File:** `backend/modules/auth/application/services.py`

**Method:** `AuthService.register_user()`

When role is "tutor":
1. Creates User record
2. Automatically creates TutorProfile record with default status

**Database Operations:**
```sql
-- Insert user
INSERT INTO users (email, hashed_password, role, first_name, last_name)
VALUES ('tutor@example.com', '$2b$12$...', 'tutor', 'Jane', 'Smith');

-- Create tutor profile
INSERT INTO tutor_profile (
  user_id, approval_status, is_verified,
  hourly_rate, completion_percentage
) VALUES (
  42, 'draft', false,
  0, 0  -- Default values
);
```

**Initial Profile Status:**
- `approval_status`: "draft"
- `is_verified`: false
- `completion_percentage`: 0%

---

## Profile Builder Flow

### 1. Tutor Accesses Onboarding

**Frontend Component:** `frontend/app/tutor/onboarding/page.tsx`

Multi-step form with progress indicator:
- Step 1: Personal Information
- Step 2: Teaching Experience
- Step 3: Subjects & Pricing
- Step 4: Documents (Certifications & Education)
- Step 5: Availability
- Step 6: Review & Submit

### 2. Step 1: Personal Information

**Form Fields:**
```typescript
{
  title: string;           // e.g., "Math Tutor"
  headline: string;        // Short tagline
  bio: string;            // Full biography
  experience_years: number;  // Years of teaching
  languages: Array<{
    language: string;      // Language code
    level: string;         // CEFR level (Native, C2, C1, B2, B1, A2, A1)
  }>;
  country_of_birth: string;
}
```

**API Call:** `tutors.updateAbout()`

**HTTP Request:**
- **Method:** `PATCH`
- **URL:** `/api/tutors/me/about`
- **Headers:** `Authorization: Bearer <token>`
- **Body:**
```json
{
  "title": "Experienced Mathematics Tutor",
  "headline": "10+ years teaching calculus and algebra",
  "bio": "I have a passion for making complex math concepts accessible...",
  "experience_years": 10,
  "languages": [
    {"language": "en", "level": "Native"},
    {"language": "es", "level": "B2"}
  ]
}
```

### 3. Backend Updates About Section

**File:** `backend/modules/tutor_profile/presentation/api.py` (lines 122-132)

**Endpoint:** `PATCH /api/tutors/me/about`

**Handler:** `update_about_section()`

**Rate Limit:** 10 requests/minute

**Authorization:** Must have 'tutor' role (`get_current_tutor_user` dependency)

### 4. Service Layer Processing

**File:** `backend/modules/tutor_profile/application/services.py`

**Method:** `TutorProfileService.update_about()`

**Validation:**
- Title: 1-200 characters
- Headline: Max 500 characters
- Bio: Max 2000 characters
- Experience: 0-50 years
- Languages: Valid ISO codes, valid CEFR levels

**Database Operations:**
```sql
UPDATE tutor_profile 
SET title = 'Experienced Mathematics Tutor',
    headline = '10+ years teaching calculus',
    bio = 'I have a passion for...',
    experience_years = 10,
    languages = '{"en": "Native", "es": "B2"}',
    updated_at = NOW()
WHERE user_id = 42;

-- Recalculate completion percentage
UPDATE tutor_profile
SET completion_percentage = calculate_completion_percentage(id)
WHERE id = 10;
```

**Completion Calculation:**
```python
def calculate_completion_percentage(profile_id):
    # Weighted scoring:
    # - About section: 20%
    # - At least 1 subject: 20%
    # - Pricing set: 15%
    # - At least 1 certification: 15%
    # - At least 1 education: 15%
    # - Availability set: 15%
    pass
```

---

## Subject and Pricing Configuration

### 1. Step 3: Subjects Selection

**Frontend:** Subject multiselect with hourly rate per subject

```typescript
const handleSubjectUpdate = async () => {
  const subjects = selectedSubjects.map(s => ({
    subject_id: s.id,
    hourly_rate: s.customRate || baseRate,
    is_featured: s.isFeatured
  }));
  
  await tutors.replaceSubjects(subjects);
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 581-590)

**Method:** `tutors.replaceSubjects()`

**HTTP Request:**
- **Method:** `PUT`
- **URL:** `/api/tutors/me/subjects`
- **Body:**
```json
[
  {
    "subject_id": 5,
    "hourly_rate": 50.00,
    "is_featured": true
  },
  {
    "subject_id": 8,
    "hourly_rate": 45.00,
    "is_featured": false
  }
]
```

### 3. Backend Replaces Subjects

**Endpoint:** `PUT /api/tutors/me/subjects`

**Process:**
1. **Delete existing** - Remove all current tutor_subjects entries
2. **Validate subjects** - Ensure subject IDs exist in subjects table
3. **Insert new subjects** - Bulk insert new selections
4. **Update profile** - Set hourly_rate to lowest subject rate

**Database Operations:**
```sql
-- Remove old subjects
DELETE FROM tutor_subjects 
WHERE tutor_profile_id = 10;

-- Insert new subjects
INSERT INTO tutor_subjects (
  tutor_profile_id, subject_id, hourly_rate, is_featured
) VALUES
  (10, 5, 50.00, true),
  (10, 8, 45.00, false);

-- Update profile base rate
UPDATE tutor_profile 
SET hourly_rate = (
  SELECT MIN(hourly_rate) 
  FROM tutor_subjects 
  WHERE tutor_profile_id = 10
)
WHERE id = 10;
```

### 4. Pricing Options

**Optional:** Package deals for bulk sessions

```typescript
const pricingOptions = [
  {
    session_count: 5,
    total_price: 225.00,  // 10% discount
    description: "5-session package"
  },
  {
    session_count: 10,
    total_price: 400.00,  // 20% discount
    description: "10-session package"
  }
];

await tutors.updatePricing({
  hourly_rate: 50.00,
  pricing_options: pricingOptions,
  version: profileVersion  // Optimistic locking
});
```

**Endpoint:** `PATCH /api/tutors/me/pricing`

**Validation:**
- Hourly rate: $10-$500
- Package prices must be < (session_count × hourly_rate)
- Version check for concurrent updates

---

## Document Upload Flow

### 1. Step 4: Certifications Upload

**Frontend:** File upload with metadata form

```typescript
const handleCertificationUpload = async () => {
  const formData = new FormData();
  
  // Certifications metadata
  const certifications = [
    {
      subject: "Mathematics",
      name: "Advanced Teaching Certificate",
      years_from: "2015",
      years_to: "2020"
    }
  ];
  formData.append('certifications', JSON.stringify(certifications));
  
  // Files (mapped by index)
  formData.append('file_0', file);
  
  await tutors.replaceCertifications({ certifications, files: { 0: file } });
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 592-614)

**Method:** `tutors.replaceCertifications()`

**HTTP Request:**
- **Method:** `PUT`
- **URL:** `/api/tutors/me/certifications`
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** FormData with JSON + files

### 3. Backend Processes Upload

**File:** `backend/modules/tutor_profile/presentation/api.py` (lines 134-189)

**Endpoint:** `PUT /api/tutors/me/certifications`

**Handler:** `replace_certifications_section()`

**Process:**
1. **Parse form data** - Extract JSON and files
2. **Validate files** - Check size (max 5MB), type (PDF, JPG, PNG)
3. **Upload to storage** - S3/MinIO with unique keys
4. **Delete old certifications** - Remove existing entries
5. **Insert new certifications** - With file URLs

**File Storage:**
```python
# Generate unique key
file_key = f"certifications/{user_id}/{uuid4()}_{filename}"

# Upload to S3
s3_client.upload_fileobj(
    file,
    bucket="tutor-documents",
    key=file_key,
    ExtraArgs={
        'ContentType': mime_type,
        'ServerSideEncryption': 'AES256'
    }
)

# Generate presigned URL (expires in 7 days)
file_url = generate_presigned_url(file_key, expiry=7*24*3600)
```

**Database Operations:**
```sql
-- Delete old certifications
DELETE FROM tutor_certifications 
WHERE tutor_profile_id = 10;

-- Insert new certifications
INSERT INTO tutor_certifications (
  tutor_profile_id, subject, name, 
  years_from, years_to, file_url, file_key
) VALUES (
  10, 'Mathematics', 'Advanced Teaching Certificate',
  2015, 2020, 'https://s3...', 'certifications/42/uuid_cert.pdf'
);
```

### 4. Education Upload

**Similar process:**
- Endpoint: `PUT /api/tutors/me/education`
- Fields: university, degree, degree_type, specialization, years_from, years_to
- File upload: Diploma/transcript scans

**Degree Types:**
- Bachelor's Degree
- Master's Degree
- PhD
- Associate Degree
- Diploma
- Certificate

---

## Availability Setup

### 1. Step 5: Schedule Configuration

**Frontend:** Weekly schedule grid with time slots

```typescript
const availability = [
  {
    day_of_week: 1,  // Monday
    start_time: "09:00",
    end_time: "17:00",
    is_available: true
  },
  {
    day_of_week: 2,  // Tuesday
    start_time: "09:00",
    end_time: "12:00",
    is_available: true
  }
];

await tutors.replaceAvailability({
  availability,
  timezone: "America/New_York",
  version: profileVersion
});
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 673-684)

**Method:** `tutors.replaceAvailability()`

**HTTP Request:**
- **Method:** `PUT`
- **URL:** `/api/tutors/me/availability`
- **Body:**
```json
{
  "availability": [
    {
      "day_of_week": 1,
      "start_time": "09:00",
      "end_time": "17:00",
      "is_available": true
    }
  ],
  "timezone": "America/New_York",
  "version": 5
}
```

### 3. Backend Updates Availability

**Endpoint:** `PUT /api/tutors/me/availability`

**Validation:**
- Day of week: 0 (Sunday) - 6 (Saturday)
- Time format: HH:MM (24-hour)
- start_time < end_time
- Valid timezone (pytz)
- No overlapping slots for same day

**Database Operations:**
```sql
-- Delete old availability
DELETE FROM tutor_availability 
WHERE tutor_profile_id = 10;

-- Insert new availability
INSERT INTO tutor_availability (
  tutor_profile_id, day_of_week, 
  start_time, end_time, is_available, timezone
) VALUES
  (10, 1, '09:00', '17:00', true, 'America/New_York'),
  (10, 2, '09:00', '12:00', true, 'America/New_York');

-- Update profile timezone
UPDATE tutor_profile 
SET timezone = 'America/New_York'
WHERE id = 10;
```

**Conflict Detection:**
```python
# Check for overlaps
overlaps = db.query(TutorAvailability).filter(
    TutorAvailability.tutor_profile_id == profile_id,
    TutorAvailability.day_of_week == new_slot.day_of_week,
    or_(
        and_(
            TutorAvailability.start_time <= new_slot.start_time,
            TutorAvailability.end_time > new_slot.start_time
        ),
        and_(
            TutorAvailability.start_time < new_slot.end_time,
            TutorAvailability.end_time >= new_slot.end_time
        )
    )
).count()

if overlaps > 0:
    raise ValidationError("Overlapping time slots detected")
```

---

## Profile Submission

### 1. Step 6: Review and Submit

**Frontend:** Summary of all entered data

```typescript
const handleSubmit = async () => {
  // Final validation
  if (completionPercentage < 80) {
    showError("Profile must be at least 80% complete");
    return;
  }
  
  // Submit for review
  const profile = await tutors.submitForReview();
  
  // Redirect to confirmation page
  router.push('/tutor/profile/submitted');
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 686-690)

**Method:** `tutors.submitForReview()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/tutors/me/submit`
- **Headers:** `Authorization: Bearer <token>`
- **Body:** `{}`

### 3. Backend Validates and Submits

**Endpoint:** `POST /api/tutors/me/submit`

**Pre-Submit Validation:**
1. **Completion check** - Must be >= 80%
2. **Required sections:**
   - About section filled
   - At least 1 subject
   - Pricing configured
   - At least 1 certification OR education
   - Availability set for at least 3 days
3. **Document verification** - All uploaded files accessible
4. **Profile photo** - Optional but recommended

**Database Operations:**
```sql
UPDATE tutor_profile 
SET approval_status = 'pending_approval',
    submitted_at = NOW(),
    updated_at = NOW()
WHERE id = 10 
  AND approval_status = 'draft'
  AND completion_percentage >= 80;
```

### 4. Notification Sent

**Recipients:**
- Admin users (email notification)
- Tutor (confirmation email)

**Admin Notification:**
```
Subject: New Tutor Profile Awaiting Review

Tutor: Jane Smith (jane@example.com)
Subjects: Mathematics, Physics
Experience: 10 years
Completion: 95%

Review profile: https://platform.com/admin/tutors/pending/10
```

---

## Admin Review and Approval

### 1. Admin Views Pending Profiles

**Frontend Component:** `frontend/app/admin/page.tsx`

```typescript
useEffect(() => {
  const loadPending = async () => {
    const pending = await admin.listPendingTutors(page, pageSize);
    setPendingTutors(pending.items);
  };
  loadPending();
}, [page]);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 1133-1138)

**Method:** `admin.listPendingTutors()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/admin/tutors/pending?page=1&page_size=20`
- **Headers:** `Authorization: Bearer <admin_token>`

### 3. Backend Returns Pending List

**File:** `backend/modules/admin/presentation/api.py`

**Endpoint:** `GET /api/admin/tutors/pending`

**Authorization:** Admin role required

**SQL Query:**
```sql
SELECT 
  tp.id, tp.user_id, tp.title, tp.headline,
  tp.experience_years, tp.hourly_rate,
  tp.completion_percentage, tp.submitted_at,
  u.email, u.first_name, u.last_name,
  COUNT(ts.id) as subject_count,
  COUNT(tc.id) as certification_count,
  COUNT(te.id) as education_count
FROM tutor_profile tp
JOIN users u ON u.id = tp.user_id
LEFT JOIN tutor_subjects ts ON ts.tutor_profile_id = tp.id
LEFT JOIN tutor_certifications tc ON tc.tutor_profile_id = tp.id
LEFT JOIN tutor_education te ON te.tutor_profile_id = tp.id
WHERE tp.approval_status = 'pending_approval'
GROUP BY tp.id, u.id
ORDER BY tp.submitted_at ASC
LIMIT 20 OFFSET 0;
```

### 4. Admin Reviews Profile

**Admin checks:**
- Profile completeness and quality
- Document authenticity (certifications, education)
- Teaching experience claims
- Subject expertise
- Professional presentation

### 5. Approval Decision

**Option A: Approve**

```typescript
const handleApprove = async (tutorId: number) => {
  await admin.approveTutor(tutorId);
  showSuccess("Tutor approved successfully");
};
```

**API Call:** `admin.approveTutor()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/admin/tutors/10/approve`
- **Body:** `{}`

**Backend Processing:**

**File:** `backend/modules/admin/presentation/api.py`

**Endpoint:** `POST /api/admin/tutors/{tutor_id}/approve`

```sql
UPDATE tutor_profile 
SET approval_status = 'approved',
    is_verified = true,
    approved_at = NOW(),
    approved_by = 1,  -- Admin user ID
    updated_at = NOW()
WHERE id = 10;
```

**Notification to Tutor:**
```
Subject: Your Tutor Profile Has Been Approved!

Congratulations! Your profile is now live on our platform.
Students can now find and book sessions with you.

View your profile: https://platform.com/tutors/10
Update availability: https://platform.com/tutor/schedule
```

**Option B: Reject**

```typescript
const handleReject = async (tutorId: number, reason: string) => {
  await admin.rejectTutor(tutorId, reason);
};
```

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/admin/tutors/10/reject`
- **Body:**
```json
{
  "rejection_reason": "Please provide proof of certification. The submitted document appears incomplete."
}
```

**Backend Processing:**
```sql
UPDATE tutor_profile 
SET approval_status = 'rejected',
    rejection_reason = 'Please provide proof...',
    rejected_at = NOW(),
    rejected_by = 1,
    updated_at = NOW()
WHERE id = 10;
```

**Notification to Tutor:**
```
Subject: Profile Review - Action Required

Your tutor profile requires revision before approval.

Reason: Please provide proof of certification...

Update your profile: https://platform.com/tutor/profile
Resubmit for review: https://platform.com/tutor/onboarding
```

### 6. Profile Goes Live

**Once approved:**
- Profile visible in tutor search (`/api/tutors`)
- Tutor can receive bookings
- Students can message tutor
- Reviews enabled after first session

**Profile Status Tracking:**
```typescript
type ApprovalStatus = 
  | "draft"              // Incomplete, not submitted
  | "pending_approval"   // Submitted, awaiting review
  | "approved"           // Live on platform
  | "rejected"           // Needs revision
  | "suspended"          // Temporarily disabled
```

---

## Error Handling

### Common Errors

**400 Bad Request**
- Invalid file type/size
- Missing required fields
- Invalid CEFR level
- Overlapping availability slots

**403 Forbidden**
- Not tutor role
- Profile already approved (can't resubmit without rejection)

**409 Conflict**
- Concurrent update (version mismatch)
- Duplicate certification entry

**413 Payload Too Large**
- File exceeds 5MB limit

---

## Related Files

### Frontend
- `frontend/app/tutor/onboarding/page.tsx` - Multi-step onboarding form
- `frontend/app/tutor/profile/page.tsx` - Profile editor
- `frontend/app/tutor/profile/submitted/page.tsx` - Submission confirmation
- `frontend/components/StepIndicator.tsx` - Progress indicator
- `frontend/lib/api.ts` - API client methods

### Backend
- `backend/modules/tutor_profile/presentation/api.py` - Tutor endpoints
- `backend/modules/tutor_profile/application/services.py` - Business logic
- `backend/modules/tutor_profile/infrastructure/repositories.py` - Data access
- `backend/modules/admin/presentation/api.py` - Admin approval endpoints
- `backend/core/storage.py` - Document upload utilities

### Database
- Tables: `tutor_profile`, `tutor_subjects`, `tutor_certifications`, `tutor_education`, `tutor_availability`, `tutor_pricing_options`
