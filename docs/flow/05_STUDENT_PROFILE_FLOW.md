# Student Profile Flow

This document traces the student profile management flow, including profile customization, favorite tutors, package purchases, and learning preferences.

## Table of Contents
- [Profile Creation and Setup](#profile-creation-and-setup)
- [Profile Customization](#profile-customization)
- [Favorites Management](#favorites-management)
- [Package Purchase Flow](#package-purchase-flow)
- [Learning Preferences](#learning-preferences)
- [Booking History](#booking-history)

---

## Profile Creation and Setup

### 1. Initial Registration

**Frontend Component:** `frontend/app/(public)/register/page.tsx`

```typescript
const handleRegister = async () => {
  const user = await auth.register(
    email,
    password,
    firstName,
    lastName,
    "student",  // Default role
    timezone,
    currency
  );
  
  // Redirect to dashboard
  router.push('/dashboard');
};
```

### 2. Backend Creates Student Profile

**File:** `backend/modules/auth/application/services.py`

**Automatic Profile Creation:**

When a user registers with role "student", the system automatically:
1. Creates User record
2. Creates StudentProfile record with defaults

**Database Operations:**
```sql
-- Insert user
INSERT INTO users (
  email, hashed_password, role,
  first_name, last_name, timezone, currency
) VALUES (
  'student@example.com', '$2b$12$...', 'student',
  'John', 'Doe', 'UTC', 'USD'
);

-- Create student profile
INSERT INTO student_profile (
  user_id, bio, learning_goals,
  preferred_learning_style, created_at
) VALUES (
  42, NULL, NULL,
  NULL, NOW()
);
```

**Default Values:**
- `bio`: NULL (to be filled by student)
- `learning_goals`: NULL
- `preferred_learning_style`: NULL
- All fields optional, encouraging gradual profile completion

---

## Profile Customization

### 1. Student Accesses Profile Settings

**Frontend Component:** `frontend/app/profile/page.tsx` or `frontend/app/settings/account/page.tsx`

```typescript
useEffect(() => {
  const loadProfile = async () => {
    const profile = await students.getProfile();
    setProfile(profile);
  };
  loadProfile();
}, []);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 1024-1028)

**Method:** `students.getProfile()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/profile/student/me`
- **Headers:** `Authorization: Bearer <token>`

### 3. Backend Returns Profile

**File:** `backend/modules/students/presentation/api.py`

**Endpoint:** `GET /api/profile/student/me`

**Authorization:** Student role required

**SQL Query:**
```sql
SELECT 
  sp.id, sp.user_id, sp.bio, sp.learning_goals,
  sp.preferred_learning_style, sp.interests,
  sp.created_at, sp.updated_at,
  u.email, u.first_name, u.last_name,
  u.timezone, u.currency, u.avatar_url
FROM student_profile sp
JOIN users u ON u.id = sp.user_id
WHERE sp.user_id = 42;
```

**Response:**
```json
{
  "id": 1,
  "user_id": 42,
  "bio": "High school student interested in STEM",
  "learning_goals": "Improve math skills for SAT",
  "preferred_learning_style": "visual",
  "interests": ["mathematics", "physics", "computer_science"],
  "created_at": "2025-10-15T08:00:00Z",
  "updated_at": "2025-10-21T10:00:00Z"
}
```

### 4. Update Profile

**Frontend:** User edits profile fields

```typescript
const handleUpdate = async () => {
  const updated = await students.updateProfile({
    bio: bioText,
    learning_goals: goalsText,
    preferred_learning_style: learningStyle,
    interests: selectedInterests
  });
};
```

### 5. API Client Request

**File:** `frontend/lib/api.ts` (lines 1030-1039)

**Method:** `students.updateProfile()`

**HTTP Request:**
- **Method:** `PATCH`
- **URL:** `/api/profile/student/me`
- **Body:**
```json
{
  "bio": "High school senior passionate about mathematics and science",
  "learning_goals": "Prepare for SAT Math (target: 750+) and AP Calculus",
  "preferred_learning_style": "visual",
  "interests": ["mathematics", "physics", "computer_science", "robotics"]
}
```

### 6. Backend Updates Profile

**File:** `backend/modules/students/presentation/api.py`

**Endpoint:** `PATCH /api/profile/student/me`

**Validation:**
- Bio: Max 1000 characters
- Learning goals: Max 500 characters
- Learning style: Enum (visual, auditory, kinesthetic, reading_writing, mixed)
- Interests: Array of strings, max 10 items

**Database Operations:**
```sql
UPDATE student_profile 
SET bio = 'High school senior passionate...',
    learning_goals = 'Prepare for SAT Math...',
    preferred_learning_style = 'visual',
    interests = '["mathematics", "physics", "computer_science", "robotics"]',
    updated_at = NOW()
WHERE user_id = 42;
```

---

## Favorites Management

### 1. Add Tutor to Favorites

**Frontend Component:** Tutor profile page

```typescript
const handleAddFavorite = async (tutorProfileId: number) => {
  const favorite = await favorites.addFavorite(tutorProfileId);
  showSuccess("Tutor added to favorites!");
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 1094-1097)

**Method:** `favorites.addFavorite()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/favorites`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
- **Body:**
```json
{
  "tutor_profile_id": 10
}
```

### 3. Backend Creates Favorite

**File:** `backend/modules/profiles/presentation/api.py` (or similar favorites API)

**Endpoint:** `POST /api/favorites`

**Authorization:** Student role required

**Validation:**
1. **Tutor exists** - Verify tutor_profile_id exists
2. **Tutor approved** - Only approved tutors can be favorited
3. **No duplicate** - Check if already favorited
4. **Self-favorite prevention** - Can't favorite yourself (if user is also a tutor)

**Database Operations:**
```sql
-- Check for duplicate
SELECT id FROM favorite_tutors 
WHERE student_id = 42 AND tutor_profile_id = 10;

-- Insert favorite
INSERT INTO favorite_tutors (
  student_id, tutor_profile_id, created_at
) VALUES (
  42, 10, NOW()
);
```

**Response:**
```json
{
  "id": 5,
  "student_id": 42,
  "tutor_profile_id": 10,
  "tutor_name": "Jane Smith",
  "tutor_title": "Mathematics Expert",
  "tutor_hourly_rate": 50.00,
  "tutor_average_rating": 4.8,
  "created_at": "2025-10-21T10:30:00Z"
}
```

### 4. View Favorites List

**Frontend Component:** `frontend/app/saved-tutors/page.tsx`

```typescript
useEffect(() => {
  const loadFavorites = async () => {
    const favs = await favorites.getFavorites();
    setFavorites(favs);
  };
  loadFavorites();
}, []);
```

### 5. API Client Request

**File:** `frontend/lib/api.ts` (lines 1089-1092)

**Method:** `favorites.getFavorites()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/favorites`
- **Headers:** `Authorization: Bearer <token>`

### 6. Backend Returns Favorites

**Endpoint:** `GET /api/favorites`

**SQL Query:**
```sql
SELECT 
  ft.id, ft.student_id, ft.tutor_profile_id, ft.created_at,
  tp.title as tutor_title, tp.headline, tp.hourly_rate,
  tp.average_rating, tp.total_sessions, tp.profile_photo_url,
  u.first_name, u.last_name, u.email,
  ARRAY_AGG(s.name) as subjects
FROM favorite_tutors ft
JOIN tutor_profile tp ON tp.id = ft.tutor_profile_id
JOIN users u ON u.id = tp.user_id
LEFT JOIN tutor_subjects ts ON ts.tutor_profile_id = tp.id
LEFT JOIN subjects s ON s.id = ts.subject_id
WHERE ft.student_id = 42
  AND tp.is_approved = true
  AND u.is_active = true
GROUP BY ft.id, tp.id, u.id
ORDER BY ft.created_at DESC;
```

**Response:**
```json
[
  {
    "id": 5,
    "student_id": 42,
    "tutor_profile_id": 10,
    "tutor_name": "Jane Smith",
    "tutor_title": "Mathematics Expert",
    "tutor_headline": "10+ years teaching calculus",
    "tutor_hourly_rate": 50.00,
    "tutor_average_rating": 4.8,
    "tutor_total_sessions": 127,
    "tutor_subjects": ["Mathematics", "Physics"],
    "tutor_photo_url": "https://...",
    "created_at": "2025-10-21T10:30:00Z"
  }
]
```

### 7. Remove from Favorites

**Frontend:** Click unfavorite button

```typescript
const handleRemove = async (tutorProfileId: number) => {
  await favorites.removeFavorite(tutorProfileId);
  showSuccess("Removed from favorites");
};
```

### 8. API Client Request

**File:** `frontend/lib/api.ts` (lines 1099-1101)

**Method:** `favorites.removeFavorite()`

**HTTP Request:**
- **Method:** `DELETE`
- **URL:** `/api/favorites/10`
- **Headers:** `Authorization: Bearer <token>`

### 9. Backend Deletes Favorite

**Endpoint:** `DELETE /api/favorites/{tutor_profile_id}`

**Database Operations:**
```sql
DELETE FROM favorite_tutors 
WHERE student_id = 42 
  AND tutor_profile_id = 10;
```

**Response:** `204 No Content`

---

## Package Purchase Flow

### 1. Browse Available Packages

**Frontend Component:** Tutor profile page or packages page

```typescript
useEffect(() => {
  const loadPackages = async () => {
    const pkgs = await packages.list();
    setPackages(pkgs);
  };
  loadPackages();
}, []);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 837-843)

**Method:** `packages.list()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/packages?status_filter=active`
- **Headers:** `Authorization: Bearer <token>`

### 3. Backend Returns Packages

**Endpoint:** `GET /api/packages`

**Query Parameters:**
- `status_filter`: "active" | "expired" | "used" | "all"

**SQL Query:**
```sql
SELECT 
  sp.id, sp.student_id, sp.tutor_profile_id,
  sp.pricing_option_id, sp.session_count,
  sp.remaining_credits, sp.total_price,
  sp.status, sp.expires_at, sp.purchased_at,
  tp.title as tutor_title, tp.hourly_rate,
  u.first_name as tutor_first_name,
  po.description as package_description
FROM student_packages sp
JOIN tutor_profile tp ON tp.id = sp.tutor_profile_id
JOIN users u ON u.id = tp.user_id
JOIN tutor_pricing_options po ON po.id = sp.pricing_option_id
WHERE sp.student_id = 42
  AND (sp.status = 'active' OR 'all' = 'all')
ORDER BY sp.purchased_at DESC;
```

**Response:**
```json
[
  {
    "id": 12,
    "student_id": 42,
    "tutor_profile_id": 10,
    "session_count": 10,
    "remaining_credits": 7,
    "total_price": 400.00,
    "status": "active",
    "expires_at": "2026-01-21T00:00:00Z",
    "purchased_at": "2025-10-21T10:00:00Z",
    "tutor_name": "Jane Smith",
    "tutor_title": "Mathematics Expert",
    "package_description": "10-session package (20% discount)"
  }
]
```

### 4. Purchase Package

**Frontend:** Select package and proceed to checkout

```typescript
const handlePurchase = async () => {
  const pkg = await packages.purchase({
    tutor_profile_id: tutorId,
    pricing_option_id: selectedOption.id,
    payment_intent_id: stripePaymentIntent,  // From Stripe
    agreed_terms: "I agree to the terms and conditions"
  });
};
```

### 5. API Client Request

**File:** `frontend/lib/api.ts` (lines 845-854)

**Method:** `packages.purchase()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/packages`
- **Body:**
```json
{
  "tutor_profile_id": 10,
  "pricing_option_id": 3,
  "payment_intent_id": "pi_1234567890",
  "agreed_terms": "I agree to the terms and conditions"
}
```

### 6. Backend Processes Purchase

**File:** `backend/modules/packages/presentation/api.py`

**Endpoint:** `POST /api/packages`

**Authorization:** Student role required

**Validation:**
1. **Tutor exists** - Verify tutor profile
2. **Pricing option valid** - Belongs to this tutor
3. **Payment verified** - Check Stripe payment intent status
4. **Terms agreed** - Required for purchase

**Payment Verification:**
```python
# Verify Stripe payment
stripe_payment = stripe.PaymentIntent.retrieve(payment_intent_id)

if stripe_payment.status != 'succeeded':
    raise HTTPException(
        status_code=400,
        detail="Payment not completed"
    )

if stripe_payment.amount != int(total_price * 100):
    raise HTTPException(
        status_code=400,
        detail="Payment amount mismatch"
    )
```

**Database Operations:**
```sql
-- Create package
INSERT INTO student_packages (
  student_id, tutor_profile_id, pricing_option_id,
  session_count, remaining_credits, total_price,
  status, payment_intent_id, expires_at, purchased_at
) VALUES (
  42, 10, 3,
  10, 10, 400.00,
  'active', 'pi_1234567890',
  NOW() + INTERVAL '3 months', NOW()
);

-- Record transaction
INSERT INTO transactions (
  user_id, type, amount, status,
  payment_method, payment_intent_id, description
) VALUES (
  42, 'package_purchase', 400.00, 'completed',
  'stripe', 'pi_1234567890', '10-session package with Jane Smith'
);
```

### 7. Package Usage on Booking

**Automatic Deduction:**

When creating a booking with a package:

```typescript
const booking = await bookings.create({
  tutor_profile_id: 10,
  start_at: selectedTime,
  duration_minutes: 60,
  use_package_id: 12  // Use this package
});
```

**Backend Processing:**

```sql
-- Deduct credit
UPDATE student_packages 
SET remaining_credits = remaining_credits - 1,
    updated_at = NOW()
WHERE id = 12 
  AND student_id = 42
  AND remaining_credits > 0;

-- If no credits left, mark as used
UPDATE student_packages 
SET status = 'used',
    used_at = NOW()
WHERE id = 12 
  AND remaining_credits = 0;
```

### 8. Package Expiration

**Background Job:** Runs daily

```python
# Mark expired packages
UPDATE student_packages 
SET status = 'expired'
WHERE status = 'active'
  AND expires_at < NOW();

# Notify students of upcoming expirations
SELECT sp.id, u.email, sp.remaining_credits, sp.expires_at
FROM student_packages sp
JOIN users u ON u.id = sp.student_id
WHERE sp.status = 'active'
  AND sp.expires_at BETWEEN NOW() AND NOW() + INTERVAL '7 days';
```

---

## Learning Preferences

### 1. Set Preferences

**Frontend Component:** Settings page

```typescript
const preferences = {
  timezone: "America/New_York",
  currency: "USD",
  preferred_subjects: [5, 8, 12],
  notification_preferences: {
    email_booking_confirmations: true,
    email_message_notifications: false,
    sms_reminders: true
  }
};

await auth.updatePreferences(
  preferences.currency,
  preferences.timezone
);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 447-473)

**Method:** `auth.updatePreferences()`

**HTTP Requests:**
- **Currency:** `PATCH /api/users/currency` with `{ "currency": "USD" }`
- **Timezone:** `PATCH /api/users/preferences` with `{ "timezone": "America/New_York" }`

### 3. Backend Updates Preferences

**Database Operations:**
```sql
-- Update currency
UPDATE users 
SET currency = 'USD',
    updated_at = NOW()
WHERE id = 42;

-- Update timezone
UPDATE users 
SET timezone = 'America/New_York',
    updated_at = NOW()
WHERE id = 42;
```

**Effect:**
- All prices displayed in selected currency
- All times shown in user's timezone
- Tutor availability calculated with timezone offset

---

## Booking History

### 1. View Past Bookings

**Frontend Component:** Bookings page with filter

```typescript
const loadBookings = async () => {
  const result = await bookings.list({
    status: "completed",
    role: "student",
    page: 1,
    page_size: 20
  });
};
```

### 2. Backend Returns History

**Endpoint:** `GET /api/bookings?status=completed&role=student`

**SQL Query:**
```sql
SELECT 
  b.id, b.start_time, b.end_time, b.status,
  b.total_amount, b.lesson_type, b.join_url,
  tp.title as tutor_title, tp.hourly_rate,
  u.first_name as tutor_first_name,
  s.name as subject_name,
  r.rating, r.comment as review_comment
FROM bookings b
JOIN tutor_profile tp ON tp.id = b.tutor_profile_id
JOIN users u ON u.id = tp.user_id
JOIN subjects s ON s.id = b.subject_id
LEFT JOIN reviews r ON r.booking_id = b.id
WHERE b.student_id = 42
  AND b.status = 'COMPLETED'
ORDER BY b.start_time DESC
LIMIT 20 OFFSET 0;
```

---

## Related Files

### Frontend
- `frontend/app/profile/page.tsx` - Profile editor
- `frontend/app/saved-tutors/page.tsx` - Favorites list
- `frontend/app/packages/page.tsx` - Package management
- `frontend/app/bookings/page.tsx` - Booking history
- `frontend/lib/api.ts` - API client

### Backend
- `backend/modules/students/presentation/api.py` - Student endpoints
- `backend/modules/profiles/presentation/api.py` - Favorites endpoints
- `backend/modules/packages/presentation/api.py` - Package endpoints
- `backend/models.py` - Student profile model

### Database
- Tables: `student_profile`, `favorite_tutors`, `student_packages`, `bookings`, `reviews`
