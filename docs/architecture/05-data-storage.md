# Data & Storage Design

## 1. Database Selection

### Decision: PostgreSQL 17

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **PostgreSQL** | ACID, JSON, full-text search, mature | Scaling complexity | **Selected** |
| MySQL | Widespread, simple | Weaker JSON, fewer features | Rejected |
| MongoDB | Flexible schema | No ACID for payments | Rejected |
| CockroachDB | Distributed | Overhead for MVP | Rejected |

### Justification

1. **ACID Compliance**: Financial transactions require strong consistency
2. **JSON/JSONB**: Flexible metadata storage without schema changes
3. **Full-Text Search**: Native tsvector for tutor discovery
4. **Extensions**: uuid-ossp, btree_gist for advanced features
5. **Ecosystem**: Excellent tooling, community, and hosting options

## 2. Schema Overview

### Table Count: 45+

| Category | Tables | Examples |
|----------|--------|----------|
| Identity | 3 | users, user_profiles, user_notification_preferences |
| Tutoring | 10 | tutor_profiles, tutor_subjects, tutor_certifications, tutor_availabilities |
| Students | 4 | student_profiles, student_packages, favorite_tutors, student_notes |
| Bookings | 2 | bookings, session_materials |
| Payments | 3 | payments, refunds, payouts |
| Communication | 4 | messages, message_attachments, notifications, notification_templates |
| Reviews | 1 | reviews |
| Admin | 2 | audit_log, reports |
| Reference | 4 | subjects, supported_currencies, supported_languages, currency_rates |

## 3. Core Tables

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('student', 'tutor', 'admin', 'owner')),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(64) DEFAULT 'UTC',

    -- Google OAuth
    google_id VARCHAR(255),
    google_calendar_access_token TEXT,
    google_calendar_refresh_token TEXT,

    -- Soft delete
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_users_email_lower ON users(LOWER(email));
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;
CREATE INDEX idx_users_deleted_at ON users(id) WHERE deleted_at IS NULL;
```

### Bookings Table (Four-Field State)

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,

    -- Relationships
    tutor_profile_id INTEGER REFERENCES tutor_profiles(id),
    student_id INTEGER REFERENCES users(id),
    subject_id INTEGER REFERENCES subjects(id),

    -- Time
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_booking_time_order CHECK (start_time < end_time),

    -- Four-field state machine
    session_state VARCHAR(30) NOT NULL,
    session_outcome VARCHAR(30),
    payment_state VARCHAR(30) DEFAULT 'PENDING',
    dispute_state VARCHAR(30) DEFAULT 'NONE',

    -- Cancellation tracking
    cancelled_by_role VARCHAR(20),
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,

    -- Dispute tracking
    dispute_reason TEXT,
    disputed_at TIMESTAMPTZ,
    disputed_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolved_by INTEGER REFERENCES users(id),
    resolution_notes TEXT,

    -- Pricing (snapshot at booking time)
    rate_cents INTEGER,
    currency CHAR(3) DEFAULT 'USD',
    platform_fee_pct NUMERIC(5,2) DEFAULT 20.0,
    platform_fee_cents INTEGER DEFAULT 0,
    tutor_earnings_cents INTEGER DEFAULT 0,

    -- Meeting
    join_url TEXT,
    zoom_meeting_id VARCHAR(255),
    google_calendar_event_id VARCHAR(255),

    -- Soft delete
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

-- Key indexes
CREATE INDEX idx_bookings_tutor_time ON bookings(tutor_profile_id, start_time DESC);
CREATE INDEX idx_bookings_student_time ON bookings(student_id, start_time DESC);
CREATE INDEX idx_bookings_session_state ON bookings(session_state, start_time, end_time)
    WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE');
CREATE INDEX idx_bookings_disputes ON bookings(dispute_state, disputed_at)
    WHERE dispute_state = 'OPEN';
```

### Tutor Profiles Table

```sql
CREATE TABLE tutor_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Profile content
    title VARCHAR(200) NOT NULL,
    headline VARCHAR(255),
    bio TEXT,
    teaching_philosophy TEXT,

    -- Rates
    hourly_rate NUMERIC(10,2) CHECK (hourly_rate > 0),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Status
    is_approved BOOLEAN DEFAULT FALSE,
    profile_status VARCHAR(20) DEFAULT 'incomplete',
    rejected_reason TEXT,

    -- Ratings (denormalized)
    average_rating NUMERIC(3,2) CHECK (average_rating BETWEEN 0 AND 5),
    total_reviews INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,

    -- Stripe Connect
    stripe_account_id VARCHAR(255),
    stripe_charges_enabled BOOLEAN DEFAULT FALSE,
    stripe_payouts_enabled BOOLEAN DEFAULT FALSE,

    -- Full-text search
    search_vector tsvector,

    -- Soft delete
    deleted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

-- Full-text search index
CREATE INDEX idx_tutor_profiles_search ON tutor_profiles USING GIN(search_vector);
```

## 4. Schema Design Patterns

### 4.1 Soft Delete

12+ tables implement soft delete for audit trails:

```sql
-- Pattern
deleted_at TIMESTAMPTZ,
deleted_by INTEGER REFERENCES users(id)

-- Index optimization
CREATE INDEX idx_tablename_deleted_at ON tablename(id) WHERE deleted_at IS NULL;
```

**Tables with soft delete**: users, user_profiles, student_profiles, tutor_profiles, bookings, reviews, messages, message_attachments

### 4.2 Denormalization for Performance

```sql
-- Cached metrics on tutor_profiles
average_rating NUMERIC(3,2),  -- Calculated from reviews
total_reviews INTEGER,        -- Count from reviews
total_sessions INTEGER        -- Count from bookings

-- Snapshots on bookings
tutor_name VARCHAR(200),      -- Copied at booking time
student_name VARCHAR(200),
subject_name VARCHAR(100),
pricing_snapshot JSONB        -- Full pricing info frozen
```

### 4.3 Monetary Values

All money stored as integers (cents) to avoid floating-point issues:

```sql
rate_cents INTEGER,
platform_fee_cents INTEGER,
tutor_earnings_cents INTEGER,
amount_cents INTEGER
```

### 4.4 Consistent Naming

```
*_cents     Monetary values (integer cents)
*_at        Timestamps (created_at, updated_at, deleted_at)
*_pct       Percentages (platform_fee_pct)
*_id        Foreign keys (user_id, tutor_profile_id)
is_*        Booleans (is_active, is_approved)
```

## 5. Transaction Boundaries

### Strong Consistency Required

| Operation | Scope | Justification |
|-----------|-------|---------------|
| Create booking + deduct package | Single TX | Credits must match |
| Accept booking + update metrics | Single TX | Consistency |
| Cancel + refund + restore credits | Single TX | Financial integrity |
| Create payment + update booking | Single TX | Payment state sync |

### Eventual Consistency Acceptable

| Operation | Scope | Justification |
|-----------|-------|---------------|
| Send notification | Separate TX | Can retry |
| Update tutor metrics | Separate TX | Aggregated data |
| Full-text search index | Async | Not real-time critical |
| Analytics dashboard | Async | Aggregate queries |

## 6. Index Strategy

### Total Indexes: 150+

#### Partial Indexes (WHERE clause)

```sql
-- Only active records (30-40% smaller)
CREATE INDEX idx_users_active WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_pending WHERE session_state IN ('REQUESTED', 'SCHEDULED');
CREATE INDEX idx_messages_unread WHERE is_read = FALSE;
```

#### Composite Indexes

```sql
-- Common query patterns
CREATE INDEX idx_bookings_tutor_time ON bookings(tutor_profile_id, start_time DESC);
CREATE INDEX idx_messages_conversation ON messages(sender_id, recipient_id, created_at DESC);
CREATE INDEX idx_student_packages_lookup ON student_packages(student_id, tutor_profile_id, status);
```

#### GIN Indexes (Arrays, Full-text)

```sql
CREATE INDEX idx_tutor_profiles_badges USING GIN(badges);
CREATE INDEX idx_tutor_profiles_search USING GIN(search_vector);
```

## 7. Constraints

### Check Constraints

```sql
-- Role validation
CONSTRAINT valid_role CHECK (role IN ('student', 'tutor', 'admin', 'owner'))

-- Currency format
CONSTRAINT valid_currency CHECK (currency ~ '^[A-Z]{3}$')

-- Time ordering
CONSTRAINT chk_booking_time_order CHECK (start_time < end_time)

-- State validity
CONSTRAINT valid_session_state CHECK (session_state IN ('REQUESTED', ...))

-- Rating range
CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5)

-- Package consistency
CONSTRAINT chk_sessions_consistency CHECK (sessions_remaining = sessions_purchased - sessions_used)
```

### Unique Constraints

```sql
-- Prevent duplicate favorites
CONSTRAINT uq_favorite UNIQUE (student_id, tutor_profile_id)

-- Prevent tutor double-booking
CREATE UNIQUE INDEX idx_bookings_no_overlap
    ON bookings(tutor_profile_id, start_time, end_time)
    WHERE session_state IN ('REQUESTED', 'SCHEDULED');

-- One review per booking
CONSTRAINT uq_review_booking UNIQUE (booking_id)
```

## 8. Connection Pooling

```python
# database.py
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # Validate before use
    pool_size=10,           # Base connections
    max_overflow=20,        # Additional on demand
    pool_recycle=3600,      # Recycle hourly
    pool_timeout=30,        # Wait timeout
)
```

### Pool Sizing Guidelines

| Scenario | pool_size | max_overflow | Total |
|----------|-----------|--------------|-------|
| Development | 5 | 10 | 15 |
| Production (MVP) | 10 | 20 | 30 |
| Production (Scale) | 20 | 40 | 60 |

## 9. Migration Strategy

### Current: Sequential SQL Files

```
database/migrations/
+-- 001_add_message_features.sql
+-- 002_add_message_attachments.sql
+-- ...
+-- 034_booking_status_redesign.sql
```

### Migration Tracking

```sql
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ,
    description TEXT,
    checksum VARCHAR(64)
);
```

### Migration Best Practices

1. **Idempotent**: Can re-run safely (IF NOT EXISTS)
2. **Backward compatible**: Old code works during deploy
3. **Small changes**: One concern per migration
4. **Tested**: Run against staging first
5. **Versioned**: Checked into git

### Recommended: Alembic Migration

```bash
# Future migration workflow
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
alembic downgrade -1  # Rollback support
```

## 10. File Storage (MinIO)

### Bucket Structure

```
user-avatars/
+-- {user_id}/
    +-- avatar.jpg
    +-- avatar_thumb.jpg

tutor-assets/
+-- {tutor_profile_id}/
    +-- certifications/
    +-- education/
    +-- profile_photos/

message-attachments/
+-- {message_id}/
    +-- {filename}
```

### Storage Configuration

```python
# core/storage.py
AVATAR_STORAGE_BUCKET = "user-avatars"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
URL_TTL_SECONDS = 300  # Signed URL expiry
```

### Future: S3 Migration

MinIO is S3-compatible, enabling seamless migration:

```python
# Change only endpoint configuration
STORAGE_ENDPOINT = "s3.amazonaws.com"  # Instead of minio:9000
```

## 11. Backup Strategy

### Recommended Backup Schedule

| Type | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| Full | Daily | 30 days | pg_dump |
| WAL Archives | Continuous | 7 days | pg_archivecleanup |
| Point-in-time | Continuous | 7 days | WAL shipping |

### Backup Commands

```bash
# Full backup
pg_dump -Fc -f backup_$(date +%Y%m%d).dump authapp

# Restore
pg_restore -d authapp backup_20260129.dump

# WAL archiving (in postgresql.conf)
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
```
