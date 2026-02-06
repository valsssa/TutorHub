-- ============================================================================
-- Migration 001: Baseline Schema
-- EduStream Student-Tutor Booking Platform
--
-- This baseline consolidates all previous migrations (001-056) into a single
-- schema file. Fresh databases run only this migration.
--
-- Date: 2026-02-06
-- Consolidates: Original migrations 001-056
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table with role-based access
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    avatar_key VARCHAR(255),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    timezone VARCHAR(64) DEFAULT 'UTC' NOT NULL,
    preferred_language CHAR(2) DEFAULT 'en',
    detected_language CHAR(2),
    locale VARCHAR(10) DEFAULT 'en-US',
    detected_locale VARCHAR(10),
    locale_detection_confidence NUMERIC(3,2),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER,
    password_changed_at TIMESTAMPTZ,
    -- Fraud detection fields
    registration_ip INET,
    trial_restricted BOOLEAN DEFAULT FALSE NOT NULL,
    fraud_flags JSONB DEFAULT '[]'::JSONB,
    -- Google OAuth/Calendar integration
    google_id VARCHAR(255),
    google_calendar_access_token TEXT,
    google_calendar_refresh_token TEXT,
    google_calendar_token_expires TIMESTAMPTZ,
    google_calendar_email VARCHAR(255),
    google_calendar_connected_at TIMESTAMPTZ,
    -- Profile completion tracking
    profile_incomplete BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_role CHECK (role IN ('student', 'tutor', 'admin', 'owner')),
    CONSTRAINT valid_email_length CHECK (char_length(email) <= 254),
    CONSTRAINT valid_currency CHECK (currency ~ '^[A-Z]{3}$')
);

-- Performance indexes for users
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_avatar_key ON users(avatar_key) WHERE avatar_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_currency ON users(currency);
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone);
CREATE INDEX IF NOT EXISTS idx_users_language ON users(preferred_language);
CREATE INDEX IF NOT EXISTS idx_users_locale ON users(locale);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_users_registration_ip ON users(registration_ip) WHERE registration_ip IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_trial_restricted ON users(trial_restricted) WHERE trial_restricted = TRUE;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;

-- Extended user profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    bio TEXT,
    timezone VARCHAR(64) DEFAULT 'UTC',
    country_of_birth VARCHAR(2),
    phone_country_code VARCHAR(5),
    date_of_birth DATE,
    age_confirmed BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_country_of_birth_format CHECK (
        country_of_birth IS NULL OR (country_of_birth ~ '^[A-Z]{2}$')
    ),
    CONSTRAINT chk_phone_country_code_format CHECK (
        phone_country_code IS NULL OR (phone_country_code ~ '^\+[0-9]{1,3}$')
    ),
    CONSTRAINT chk_age_18_plus CHECK (
        date_of_birth IS NULL OR (date_of_birth <= CURRENT_DATE - INTERVAL '18 years')
    )
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country_of_birth) WHERE country_of_birth IS NOT NULL;

-- Subjects catalog
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_subjects_active ON subjects(is_active);

-- ============================================================================
-- TUTOR-RELATED TABLES
-- ============================================================================

-- Tutor profiles
CREATE TABLE IF NOT EXISTS tutor_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    headline VARCHAR(255),
    bio TEXT,
    description TEXT,
    hourly_rate NUMERIC(10,2) NOT NULL CHECK (hourly_rate > 0),
    experience_years INTEGER NOT NULL DEFAULT 0 CHECK (experience_years >= 0),
    education VARCHAR(255),
    languages TEXT[],
    video_url VARCHAR(500),
    is_approved BOOLEAN DEFAULT FALSE NOT NULL,
    profile_status VARCHAR(20) DEFAULT 'incomplete' NOT NULL,
    rejection_reason TEXT,
    approved_at TIMESTAMPTZ,
    approved_by INTEGER,
    average_rating NUMERIC(3,2) DEFAULT 0.00 CHECK (average_rating BETWEEN 0 AND 5),
    total_reviews INTEGER DEFAULT 0 NOT NULL CHECK (total_reviews >= 0),
    total_sessions INTEGER DEFAULT 0 NOT NULL CHECK (total_sessions >= 0),
    timezone VARCHAR(64) DEFAULT 'UTC',
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    pricing_model VARCHAR(20) DEFAULT 'hourly' NOT NULL,
    instant_book_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    instant_book_requirements TEXT,
    auto_confirm_threshold_hours INTEGER DEFAULT 24,
    auto_confirm BOOLEAN DEFAULT FALSE,
    badges TEXT[] DEFAULT ARRAY[]::TEXT[],
    is_identity_verified BOOLEAN DEFAULT FALSE,
    is_education_verified BOOLEAN DEFAULT FALSE,
    is_background_checked BOOLEAN DEFAULT FALSE,
    verification_notes TEXT,
    profile_completeness_score INTEGER DEFAULT 0 CHECK (profile_completeness_score BETWEEN 0 AND 100),
    last_completeness_check TIMESTAMPTZ,
    cancellation_strikes INTEGER DEFAULT 0 CHECK (cancellation_strikes >= 0),
    trial_price_cents INTEGER CHECK (trial_price_cents >= 0),
    payout_method JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1,
    -- Video provider preference
    preferred_video_provider VARCHAR(20) DEFAULT 'zoom',
    custom_meeting_url_template VARCHAR(500),
    video_provider_configured BOOLEAN DEFAULT FALSE,
    -- Additional fields
    teaching_philosophy TEXT,
    search_vector tsvector,
    stripe_account_id VARCHAR(255),
    stripe_charges_enabled BOOLEAN DEFAULT FALSE,
    stripe_payouts_enabled BOOLEAN DEFAULT FALSE,
    stripe_onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_profile_status CHECK (profile_status IN ('incomplete', 'pending_approval', 'under_review', 'approved', 'rejected', 'archived')),
    CONSTRAINT valid_tutor_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT valid_pricing_model CHECK (pricing_model IN ('hourly', 'package', 'session', 'hybrid')),
    CONSTRAINT valid_video_provider CHECK (preferred_video_provider IN ('zoom', 'google_meet', 'teams', 'custom', 'manual'))
);

CREATE INDEX IF NOT EXISTS idx_tutor_profiles_user_id ON tutor_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_approved ON tutor_profiles(is_approved);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_rate ON tutor_profiles(hourly_rate);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_rating ON tutor_profiles(average_rating DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_status ON tutor_profiles(profile_status);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_pending_review ON tutor_profiles(profile_status, created_at DESC) WHERE profile_status IN ('pending_approval', 'under_review');
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_currency ON tutor_profiles(currency);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_instant_book ON tutor_profiles(instant_book_enabled, is_approved) WHERE instant_book_enabled = TRUE AND is_approved = TRUE;
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_badges ON tutor_profiles USING GIN (badges);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_verified ON tutor_profiles(is_identity_verified, is_education_verified);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_completeness ON tutor_profiles(profile_completeness_score DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_deleted_at ON tutor_profiles(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_timezone ON tutor_profiles(timezone);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_user_status ON tutor_profiles(user_id, profile_status, is_approved);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_archived ON tutor_profiles(user_id) WHERE profile_status = 'archived';
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_version ON tutor_profiles(id, version);
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_search ON tutor_profiles USING GIN(search_vector);

-- Tutor subject specializations
CREATE TABLE IF NOT EXISTS tutor_subjects (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(20) NOT NULL DEFAULT 'B2',
    years_experience INTEGER CHECK (years_experience IS NULL OR years_experience >= 0),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_tutor_subject UNIQUE (tutor_profile_id, subject_id),
    CONSTRAINT valid_proficiency CHECK (proficiency_level IN ('NATIVE', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1'))
);

CREATE INDEX IF NOT EXISTS idx_tutor_subjects_profile ON tutor_subjects(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_tutor_subjects_subject ON tutor_subjects(subject_id);
CREATE INDEX IF NOT EXISTS idx_tutor_subjects_active ON tutor_subjects(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_subjects_deleted_at ON tutor_subjects(deleted_at) WHERE deleted_at IS NOT NULL;

-- Tutor availability slots
CREATE TABLE IF NOT EXISTS tutor_availabilities (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT TRUE,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_availability_time_order CHECK (start_time < end_time),
    CONSTRAINT uq_tutor_availability_slot UNIQUE (tutor_profile_id, day_of_week, start_time, end_time)
);

CREATE INDEX IF NOT EXISTS idx_tutor_availability_profile_day ON tutor_availabilities(tutor_profile_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_tutor_availability_timezone ON tutor_availabilities(timezone);
CREATE INDEX IF NOT EXISTS idx_tutor_availabilities_active ON tutor_availabilities(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_availabilities_deleted_at ON tutor_availabilities(deleted_at) WHERE deleted_at IS NOT NULL;

-- Tutor blackouts (vacation/temporary blocks)
CREATE TABLE IF NOT EXISTS tutor_blackouts (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_blackout_time CHECK (start_at < end_at)
);

CREATE INDEX IF NOT EXISTS idx_blackouts_tutor ON tutor_blackouts(tutor_id);
CREATE INDEX IF NOT EXISTS idx_blackouts_period ON tutor_blackouts(start_at, end_at);

-- Tutor certifications
CREATE TABLE IF NOT EXISTS tutor_certifications (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiration_date DATE,
    credential_id VARCHAR(100),
    credential_url VARCHAR(500),
    document_url VARCHAR(500),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tutor_certifications_profile ON tutor_certifications(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_tutor_certifications_active ON tutor_certifications(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_certifications_deleted_at ON tutor_certifications(deleted_at) WHERE deleted_at IS NOT NULL;

-- Tutor education history
CREATE TABLE IF NOT EXISTS tutor_education (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    institution VARCHAR(255) NOT NULL,
    degree VARCHAR(255),
    field_of_study VARCHAR(255),
    start_year INTEGER,
    end_year INTEGER,
    description TEXT,
    document_url VARCHAR(500),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tutor_education_profile ON tutor_education(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_tutor_education_active ON tutor_education(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_education_deleted_at ON tutor_education(deleted_at) WHERE deleted_at IS NOT NULL;

-- Tutor pricing options
CREATE TABLE IF NOT EXISTS tutor_pricing_options (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    price NUMERIC(10,2) NOT NULL CHECK (price > 0),
    pricing_type VARCHAR(20) DEFAULT 'package' NOT NULL,
    sessions_included INTEGER,
    validity_days INTEGER,
    is_popular BOOLEAN DEFAULT FALSE NOT NULL,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    extend_on_use BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_pricing_type CHECK (pricing_type IN ('hourly', 'session', 'package', 'subscription'))
);

CREATE INDEX IF NOT EXISTS idx_tutor_pricing_options_profile ON tutor_pricing_options(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_tutor_pricing_popular ON tutor_pricing_options(is_popular DESC, sort_order ASC);
CREATE INDEX IF NOT EXISTS idx_tutor_pricing_sort ON tutor_pricing_options(tutor_profile_id, sort_order ASC);

-- ============================================================================
-- STUDENT-RELATED TABLES
-- ============================================================================

-- Student profiles
CREATE TABLE IF NOT EXISTS student_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(50),
    bio TEXT,
    interests TEXT,
    grade_level VARCHAR(50),
    school_name VARCHAR(200),
    learning_goals TEXT,
    total_sessions INTEGER DEFAULT 0 NOT NULL CHECK (total_sessions >= 0),
    credit_balance_cents INTEGER DEFAULT 0 CHECK (credit_balance_cents >= 0),
    preferred_language VARCHAR(10),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);

-- Student notes - Private notes tutors keep about students
CREATE TABLE IF NOT EXISTS student_notes (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unique_tutor_student_note UNIQUE (tutor_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_student_notes_tutor ON student_notes(tutor_id);
CREATE INDEX IF NOT EXISTS idx_student_notes_student ON student_notes(student_id);

COMMENT ON TABLE student_notes IS 'Private notes that tutors can keep about their students';
COMMENT ON COLUMN student_notes.notes IS 'Private notes visible only to the tutor';

-- Student package credits/subscriptions
CREATE TABLE IF NOT EXISTS student_packages (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    pricing_option_id INTEGER NOT NULL REFERENCES tutor_pricing_options(id) ON DELETE CASCADE,
    sessions_purchased INTEGER NOT NULL CHECK (sessions_purchased > 0),
    sessions_remaining INTEGER NOT NULL CHECK (sessions_remaining >= 0),
    sessions_used INTEGER DEFAULT 0 NOT NULL CHECK (sessions_used >= 0),
    purchase_price NUMERIC(10,2) NOT NULL CHECK (purchase_price > 0),
    purchased_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    payment_intent_id VARCHAR(255),
    expiry_warning_sent BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_package_status CHECK (status IN ('active', 'expired', 'exhausted', 'refunded'))
);

CREATE INDEX IF NOT EXISTS idx_student_packages_student ON student_packages(student_id, status);
CREATE INDEX IF NOT EXISTS idx_student_packages_tutor ON student_packages(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_student_packages_expires ON student_packages(expires_at) WHERE expires_at IS NOT NULL AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_student_packages_active ON student_packages(student_id, tutor_profile_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_student_packages_expiry ON student_packages(expires_at) WHERE sessions_remaining > 0;
CREATE INDEX IF NOT EXISTS idx_student_packages_soft_delete_active ON student_packages(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_student_packages_deleted_at ON student_packages(deleted_at) WHERE deleted_at IS NOT NULL;

-- ============================================================================
-- BOOKING & SESSION TABLES
-- ============================================================================

-- Bookings between students and tutors
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER REFERENCES tutor_profiles(id) ON DELETE SET NULL,
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    -- Four-field status system
    session_state VARCHAR(20) NOT NULL DEFAULT 'REQUESTED',
    session_outcome VARCHAR(30),
    payment_state VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    dispute_state VARCHAR(30) NOT NULL DEFAULT 'NONE',
    -- Dispute tracking
    dispute_reason TEXT,
    disputed_at TIMESTAMPTZ,
    disputed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    cancelled_by_role VARCHAR(20),
    topic VARCHAR(255),
    notes TEXT,
    notes_student TEXT,
    notes_tutor TEXT,
    meeting_url VARCHAR(500),
    join_url TEXT,
    hourly_rate NUMERIC(10,2) NOT NULL CHECK (hourly_rate > 0),
    total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0),
    rate_cents INTEGER NOT NULL CHECK (rate_cents >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),
    platform_fee_pct NUMERIC(5,2) DEFAULT 20.00,
    platform_fee_cents INTEGER NOT NULL DEFAULT 0 CHECK (platform_fee_cents >= 0),
    tutor_earnings_cents INTEGER NOT NULL DEFAULT 0 CHECK (tutor_earnings_cents >= 0),
    pricing_option_id INTEGER REFERENCES tutor_pricing_options(id) ON DELETE SET NULL,
    package_id INTEGER REFERENCES student_packages(id) ON DELETE SET NULL,
    package_sessions_remaining INTEGER,
    pricing_type VARCHAR(20) DEFAULT 'hourly' NOT NULL,
    lesson_type VARCHAR(20) DEFAULT 'REGULAR',
    student_tz VARCHAR(64) DEFAULT 'UTC',
    tutor_tz VARCHAR(64) DEFAULT 'UTC',
    created_by VARCHAR(20) DEFAULT 'STUDENT',
    tutor_name VARCHAR(200),
    tutor_title VARCHAR(200),
    student_name VARCHAR(200),
    subject_name VARCHAR(100),
    pricing_snapshot JSONB,
    agreement_terms TEXT,
    is_instant_booking BOOLEAN DEFAULT FALSE,
    confirmed_at TIMESTAMPTZ,
    confirmed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    is_rebooked BOOLEAN DEFAULT FALSE,
    original_booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1,
    -- Session attendance tracking
    tutor_joined_at TIMESTAMPTZ,
    student_joined_at TIMESTAMPTZ,
    -- Video provider tracking
    video_provider VARCHAR(20),
    google_meet_link VARCHAR(500),
    -- External integrations
    stripe_checkout_session_id VARCHAR(255),
    zoom_meeting_id VARCHAR(255),
    zoom_meeting_pending BOOLEAN DEFAULT FALSE,
    google_calendar_event_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_booking_time_order CHECK (start_time < end_time),
    CONSTRAINT valid_session_state CHECK (
        session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED', 'EXPIRED')
    ),
    CONSTRAINT valid_session_outcome CHECK (
        session_outcome IS NULL OR session_outcome IN ('COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR')
    ),
    CONSTRAINT valid_payment_state CHECK (
        payment_state IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'REFUNDED', 'PARTIALLY_REFUNDED')
    ),
    CONSTRAINT valid_dispute_state CHECK (
        dispute_state IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED')
    ),
    CONSTRAINT valid_cancelled_by_role CHECK (
        cancelled_by_role IS NULL OR cancelled_by_role IN ('STUDENT', 'TUTOR', 'ADMIN', 'SYSTEM')
    ),
    CONSTRAINT valid_booking_pricing_type CHECK (pricing_type IN ('hourly', 'session', 'package', 'subscription')),
    CONSTRAINT valid_lesson_type CHECK (lesson_type IN ('TRIAL', 'REGULAR', 'PACKAGE')),
    CONSTRAINT valid_created_by CHECK (created_by IN ('STUDENT', 'TUTOR', 'ADMIN'))
);

CREATE INDEX IF NOT EXISTS idx_bookings_tutor_time ON bookings(tutor_profile_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_student_time ON bookings(student_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_session_state ON bookings(session_state);
CREATE INDEX IF NOT EXISTS idx_bookings_subject ON bookings(subject_id);
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_name ON bookings(tutor_name);
CREATE INDEX IF NOT EXISTS idx_bookings_student_name ON bookings(student_name);
CREATE INDEX IF NOT EXISTS idx_bookings_subject_name ON bookings(subject_name);
CREATE INDEX IF NOT EXISTS idx_bookings_deleted_at ON bookings(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_pricing_option ON bookings(pricing_option_id);
CREATE INDEX IF NOT EXISTS idx_bookings_instant ON bookings(is_instant_booking, session_state);
CREATE INDEX IF NOT EXISTS idx_bookings_confirmed_at ON bookings(confirmed_at);
CREATE INDEX IF NOT EXISTS idx_bookings_rebooked ON bookings(is_rebooked, original_booking_id);
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_state_time ON bookings(tutor_profile_id, session_state, start_time, end_time) WHERE session_state IN ('REQUESTED', 'SCHEDULED');
CREATE INDEX IF NOT EXISTS idx_bookings_lesson_type ON bookings(lesson_type);
CREATE INDEX IF NOT EXISTS idx_bookings_student_tz ON bookings(student_tz);
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_tz ON bookings(tutor_tz);
CREATE INDEX IF NOT EXISTS idx_bookings_package ON bookings(package_id);
CREATE INDEX IF NOT EXISTS idx_bookings_created_by ON bookings(created_by);
CREATE INDEX IF NOT EXISTS idx_bookings_join_url ON bookings(join_url) WHERE join_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_session_state_times ON bookings(session_state, start_time, end_time) WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE');
CREATE INDEX IF NOT EXISTS idx_bookings_requested_created ON bookings(created_at) WHERE session_state = 'REQUESTED';
CREATE INDEX IF NOT EXISTS idx_bookings_disputes_open ON bookings(dispute_state, disputed_at) WHERE dispute_state = 'OPEN';
CREATE INDEX IF NOT EXISTS idx_bookings_payment_state ON bookings(payment_state) WHERE payment_state IN ('AUTHORIZED', 'PENDING');
CREATE INDEX IF NOT EXISTS idx_bookings_version ON bookings(id, version);
CREATE INDEX IF NOT EXISTS idx_bookings_attendance_check ON bookings(session_state, tutor_joined_at, student_joined_at) WHERE session_state = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_bookings_stripe_checkout ON bookings(stripe_checkout_session_id) WHERE stripe_checkout_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_zoom_meeting ON bookings(zoom_meeting_id) WHERE zoom_meeting_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_google_calendar ON bookings(google_calendar_event_id) WHERE google_calendar_event_id IS NOT NULL;

-- Prevent tutor double-booking with GIST exclusion constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_no_time_overlap'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_no_time_overlap
        EXCLUDE USING gist (
            tutor_profile_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE') AND deleted_at IS NULL);
    END IF;
END $$;

-- Supporting GIST index for time range queries
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_time_range
ON bookings USING gist (tutor_profile_id, tstzrange(start_time, end_time, '[)'))
WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE') AND deleted_at IS NULL;

-- Session materials
CREATE TABLE IF NOT EXISTS session_materials (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_materials_booking ON session_materials(booking_id);
CREATE INDEX IF NOT EXISTS idx_session_materials_created_at ON session_materials(created_at DESC);

-- ============================================================================
-- PAYMENT TABLES
-- ============================================================================

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    archived_student_id INTEGER,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
    provider_payment_id TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'REQUIRES_ACTION',
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_payment_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT valid_payment_provider CHECK (provider IN ('stripe', 'adyen', 'paypal', 'test')),
    CONSTRAINT valid_payment_status CHECK (status IN ('REQUIRES_ACTION', 'AUTHORIZED', 'CAPTURED', 'REFUNDED', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_provider_id ON payments(provider_payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_archived_student ON payments(archived_student_id) WHERE archived_student_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payments_student_status_created ON payments(student_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_active ON payments(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_payments_deleted_at ON payments(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON COLUMN payments.archived_student_id IS 'Preserves original student_id after user deletion for financial records';

-- Refunds
CREATE TABLE IF NOT EXISTS refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    reason VARCHAR(30) NOT NULL,
    provider_refund_id TEXT,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_refund_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT valid_refund_reason CHECK (reason IN ('STUDENT_CANCEL', 'TUTOR_CANCEL', 'NO_SHOW_TUTOR', 'GOODWILL', 'OTHER'))
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment ON refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_booking ON refunds(booking_id);
CREATE INDEX IF NOT EXISTS idx_refunds_reason ON refunds(reason);
CREATE INDEX IF NOT EXISTS idx_refunds_created ON refunds(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_refunds_active ON refunds(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_refunds_deleted_at ON refunds(deleted_at) WHERE deleted_at IS NOT NULL;

-- Webhook events for Stripe idempotency
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_stripe_event_id ON webhook_events(stripe_event_id);

COMMENT ON TABLE webhook_events IS 'Tracks processed Stripe webhook events for idempotency';
COMMENT ON COLUMN webhook_events.stripe_event_id IS 'Unique Stripe event ID (e.g., evt_xxx)';
COMMENT ON COLUMN webhook_events.event_type IS 'Stripe event type (e.g., checkout.session.completed)';
COMMENT ON COLUMN webhook_events.processed_at IS 'Timestamp when the event was processed';

-- Wallets table
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance_cents INTEGER NOT NULL DEFAULT 0,
    pending_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_wallet_per_currency UNIQUE (user_id, currency),
    CONSTRAINT non_negative_wallet_balance CHECK (balance_cents >= 0),
    CONSTRAINT non_negative_pending_balance CHECK (pending_cents >= 0)
);

CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_active ON wallets(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_wallets_deleted_at ON wallets(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE wallets IS 'User wallets for storing credits and making payments';
COMMENT ON COLUMN wallets.balance_cents IS 'Available balance in cents';
COMMENT ON COLUMN wallets.pending_cents IS 'Balance pending release (e.g., in escrow)';

-- Wallet transactions table
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    description TEXT,
    reference_id VARCHAR(255) NOT NULL UNIQUE,
    transaction_metadata JSONB,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CONSTRAINT valid_transaction_type CHECK (
        type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'REFUND', 'PAYOUT', 'PAYMENT', 'FEE')
    ),
    CONSTRAINT valid_transaction_status CHECK (
        status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')
    )
);

CREATE INDEX IF NOT EXISTS idx_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_reference_id ON wallet_transactions(reference_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_status ON wallet_transactions(status);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_wallet_type_status ON wallet_transactions(wallet_id, type, status);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_active ON wallet_transactions(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_deleted_at ON wallet_transactions(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE wallet_transactions IS 'Transaction history for wallet operations';
COMMENT ON COLUMN wallet_transactions.reference_id IS 'External reference for idempotency checks';

-- Payouts
CREATE TABLE IF NOT EXISTS payouts (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    archived_tutor_id INTEGER,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    transfer_reference TEXT,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_payout_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT valid_payout_status CHECK (status IN ('PENDING', 'SUBMITTED', 'PAID', 'FAILED')),
    CONSTRAINT valid_payout_period CHECK (period_start <= period_end)
);

CREATE INDEX IF NOT EXISTS idx_payouts_tutor ON payouts(tutor_id, status);
CREATE INDEX IF NOT EXISTS idx_payouts_period ON payouts(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_payouts_status ON payouts(status);
CREATE INDEX IF NOT EXISTS idx_payouts_created ON payouts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payouts_archived_tutor ON payouts(archived_tutor_id) WHERE archived_tutor_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payouts_active ON payouts(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_payouts_deleted_at ON payouts(deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON COLUMN payouts.archived_tutor_id IS 'Preserves original tutor_id after user deletion for financial records';

-- ============================================================================
-- REVIEW & RATING TABLES
-- ============================================================================

-- Reviews for tutors
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER UNIQUE REFERENCES bookings(id) ON DELETE SET NULL,
    tutor_profile_id INTEGER REFERENCES tutor_profiles(id) ON DELETE SET NULL,
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    is_public BOOLEAN DEFAULT TRUE NOT NULL,
    booking_snapshot JSONB,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_tutor ON reviews(tutor_profile_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_student ON reviews(student_id);
CREATE INDEX IF NOT EXISTS idx_reviews_booking ON reviews(booking_id);
CREATE INDEX IF NOT EXISTS idx_reviews_deleted_at ON reviews(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- COMMUNICATION TABLES
-- ============================================================================

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    last_message_at TIMESTAMPTZ,
    student_unread_count INTEGER NOT NULL DEFAULT 0,
    tutor_unread_count INTEGER NOT NULL DEFAULT 0,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_conversation_participants UNIQUE (student_id, tutor_id, booking_id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_student ON conversations(student_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tutor ON conversations(tutor_id);
CREATE INDEX IF NOT EXISTS idx_conversations_booking ON conversations(booking_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NOT NULL;

-- Messages between users
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    recipient_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    is_edited BOOLEAN DEFAULT FALSE NOT NULL,
    edited_at TIMESTAMPTZ,
    is_system_message BOOLEAN NOT NULL DEFAULT FALSE,
    attachment_url VARCHAR(500),
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_booking ON messages(booking_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(sender_id, recipient_id, booking_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_unread ON messages(recipient_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_messages_edited ON messages(is_edited) WHERE is_edited = TRUE;
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC) WHERE deleted_at IS NULL;

-- Message attachments
CREATE TABLE IF NOT EXISTS message_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_key VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_category VARCHAR(50) NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    is_scanned BOOLEAN DEFAULT FALSE NOT NULL,
    scan_result VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    width INTEGER,
    height INTEGER,
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT valid_file_category CHECK (file_category IN ('image', 'document', 'video', 'audio', 'other')),
    CONSTRAINT valid_scan_result CHECK (scan_result IS NULL OR scan_result IN ('clean', 'infected', 'pending'))
);

CREATE INDEX IF NOT EXISTS idx_message_attachments_message ON message_attachments(message_id);
CREATE INDEX IF NOT EXISTS idx_message_attachments_file_key ON message_attachments(file_key);
CREATE INDEX IF NOT EXISTS idx_message_attachments_uploaded_by ON message_attachments(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_message_attachments_created_at ON message_attachments(created_at DESC);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    action_url VARCHAR(500),
    action_label VARCHAR(100),
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    extra_data JSONB DEFAULT '{}'::JSONB,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON notifications(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_active ON notifications(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_deleted_at ON notifications(deleted_at) WHERE deleted_at IS NOT NULL;

-- ============================================================================
-- ADDITIONAL FEATURE TABLES
-- ============================================================================

-- Favorite tutors
CREATE TABLE IF NOT EXISTS favorite_tutors (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_favorite UNIQUE (student_id, tutor_profile_id)
);

CREATE INDEX IF NOT EXISTS idx_favorite_tutors_student ON favorite_tutors(student_id);
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_created_at ON favorite_tutors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_active ON favorite_tutors(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_deleted_at ON favorite_tutors(deleted_at) WHERE deleted_at IS NOT NULL;

-- User reports for moderation
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    reason VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_report_status CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed'))
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- Popular topics tracking
CREATE TABLE IF NOT EXISTS popular_topics (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    usage_count INTEGER DEFAULT 1 NOT NULL,
    last_used TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_subject_topic UNIQUE (subject_id, topic)
);

CREATE INDEX IF NOT EXISTS idx_popular_topics_subject ON popular_topics(subject_id, usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_topics_usage ON popular_topics(usage_count DESC, last_used DESC);

-- Rebooking metrics
CREATE TABLE IF NOT EXISTS rebooking_metrics (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    original_booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    rebooked_booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    time_to_rebook_hours INTEGER,
    rebooking_source VARCHAR(50) DEFAULT 'one_click',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rebooking_metrics_tutor ON rebooking_metrics(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_rebooking_metrics_student ON rebooking_metrics(student_id);

-- ============================================================================
-- FRAUD DETECTION TABLES
-- ============================================================================

-- Registration fraud signals
CREATE TABLE IF NOT EXISTS registration_fraud_signals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    signal_type VARCHAR(50) NOT NULL,
    signal_value TEXT NOT NULL,
    confidence_score NUMERIC(3,2) DEFAULT 0.50 CHECK (confidence_score BETWEEN 0 AND 1),
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMPTZ,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    review_outcome VARCHAR(20),
    review_notes TEXT,
    CONSTRAINT valid_signal_type CHECK (signal_type IN ('ip_address', 'device_fingerprint', 'email_pattern', 'browser_fingerprint', 'behavioral')),
    CONSTRAINT valid_review_outcome CHECK (review_outcome IS NULL OR review_outcome IN ('legitimate', 'fraudulent', 'suspicious'))
);

CREATE INDEX IF NOT EXISTS idx_fraud_signals_user ON registration_fraud_signals(user_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_fraud_signals_value ON registration_fraud_signals(signal_type, signal_value, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_fraud_signals_pending_review ON registration_fraud_signals(reviewed_at, detected_at DESC) WHERE reviewed_at IS NULL;

COMMENT ON TABLE registration_fraud_signals IS 'Tracks fraud signals detected during registration for trial abuse prevention';
COMMENT ON COLUMN registration_fraud_signals.signal_type IS 'Type of signal: ip_address, device_fingerprint, email_pattern, browser_fingerprint, behavioral';
COMMENT ON COLUMN registration_fraud_signals.signal_value IS 'The actual value (e.g., IP address, fingerprint hash)';
COMMENT ON COLUMN registration_fraud_signals.confidence_score IS 'Confidence that this signal indicates fraud (0-1)';

-- ============================================================================
-- AUDIT & ANALYTICS TABLES
-- ============================================================================

-- Audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    CONSTRAINT valid_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'SOFT_DELETE', 'RESTORE'))
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Tutor field history
CREATE TABLE IF NOT EXISTS tutor_profile_field_history (
    id BIGSERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    change_reason TEXT,
    CONSTRAINT field_history_has_change CHECK (old_value IS DISTINCT FROM new_value)
);

CREATE INDEX IF NOT EXISTS idx_tutor_field_history_profile ON tutor_profile_field_history(tutor_profile_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_field_history_field ON tutor_profile_field_history(field_name);
CREATE INDEX IF NOT EXISTS idx_tutor_field_history_changed_by ON tutor_profile_field_history(changed_by);

-- Tutor performance metrics
CREATE TABLE IF NOT EXISTS tutor_metrics (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER UNIQUE NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    avg_response_time_minutes INTEGER DEFAULT 0,
    response_rate_24h NUMERIC(5,2) DEFAULT 0.00,
    total_bookings INTEGER DEFAULT 0,
    completed_bookings INTEGER DEFAULT 0,
    cancelled_bookings INTEGER DEFAULT 0,
    no_show_bookings INTEGER DEFAULT 0,
    completion_rate NUMERIC(5,2) DEFAULT 0.00,
    total_unique_students INTEGER DEFAULT 0,
    returning_students INTEGER DEFAULT 0,
    student_retention_rate NUMERIC(5,2) DEFAULT 0.00,
    avg_sessions_per_student NUMERIC(5,2) DEFAULT 0.00,
    total_revenue NUMERIC(12,2) DEFAULT 0.00,
    avg_session_value NUMERIC(10,2) DEFAULT 0.00,
    profile_views_30d INTEGER DEFAULT 0,
    booking_conversion_rate NUMERIC(5,2) DEFAULT 0.00,
    avg_rating NUMERIC(3,2) DEFAULT 0.00,
    total_reviews INTEGER DEFAULT 0,
    response_time_percentile INTEGER,
    retention_rate_percentile INTEGER,
    rating_percentile INTEGER,
    last_calculated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_percentiles CHECK (
        (response_time_percentile IS NULL OR response_time_percentile BETWEEN 0 AND 100) AND
        (retention_rate_percentile IS NULL OR retention_rate_percentile BETWEEN 0 AND 100) AND
        (rating_percentile IS NULL OR rating_percentile BETWEEN 0 AND 100)
    )
);

CREATE INDEX IF NOT EXISTS idx_tutor_metrics_response_time ON tutor_metrics(avg_response_time_minutes);
CREATE INDEX IF NOT EXISTS idx_tutor_metrics_retention ON tutor_metrics(student_retention_rate DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_metrics_rating ON tutor_metrics(avg_rating DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_metrics_last_calculated ON tutor_metrics(last_calculated);

-- Tutor response log
CREATE TABLE IF NOT EXISTS tutor_response_log (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    booking_created_at TIMESTAMPTZ NOT NULL,
    tutor_responded_at TIMESTAMPTZ,
    response_time_minutes INTEGER,
    response_action VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_response_action CHECK (response_action IN ('confirmed', 'cancelled', 'ignored', 'auto_confirmed'))
);

CREATE INDEX IF NOT EXISTS idx_response_log_tutor ON tutor_response_log(tutor_profile_id, booking_created_at DESC);
CREATE INDEX IF NOT EXISTS idx_response_log_time ON tutor_response_log(response_time_minutes) WHERE response_time_minutes IS NOT NULL;

-- Notification templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    action_label VARCHAR(100),
    action_url_template VARCHAR(500),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    delivery_channels TEXT[] DEFAULT ARRAY['in_app']::TEXT[],
    timing_rules JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_templates_key ON notification_templates(template_key);
CREATE INDEX IF NOT EXISTS idx_notification_templates_category ON notification_templates(category);

-- Notification queue
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_key VARCHAR(100) NOT NULL REFERENCES notification_templates(template_key),
    scheduled_for TIMESTAMPTZ NOT NULL,
    variables JSONB DEFAULT '{}'::JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_notification_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled ON notification_queue(scheduled_for, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_notification_queue_user ON notification_queue(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notification_queue_template ON notification_queue(template_key);

-- User notification preferences
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    session_reminders_enabled BOOLEAN DEFAULT TRUE,
    booking_requests_enabled BOOLEAN DEFAULT TRUE,
    learning_nudges_enabled BOOLEAN DEFAULT TRUE,
    review_prompts_enabled BOOLEAN DEFAULT TRUE,
    achievements_enabled BOOLEAN DEFAULT TRUE,
    marketing_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    preferred_notification_time TIME DEFAULT '09:00:00',
    max_daily_notifications INTEGER DEFAULT 10,
    max_weekly_nudges INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_notification_prefs_user ON user_notification_preferences(user_id);

-- Notification analytics
CREATE TABLE IF NOT EXISTS notification_analytics (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    delivery_channel VARCHAR(20),
    was_actionable BOOLEAN DEFAULT FALSE,
    action_taken BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_analytics_template ON notification_analytics(template_key, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_user ON notification_analytics(user_id);

-- ============================================================================
-- LOCALIZATION TABLES
-- ============================================================================

-- Supported languages
CREATE TABLE IF NOT EXISTS supported_languages (
    language_code CHAR(2) PRIMARY KEY,
    language_name_en VARCHAR(50) NOT NULL,
    language_name_native VARCHAR(50) NOT NULL,
    is_rtl BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    translation_completeness INTEGER DEFAULT 0 CHECK (translation_completeness BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Supported currencies
CREATE TABLE IF NOT EXISTS supported_currencies (
    currency_code CHAR(3) PRIMARY KEY,
    currency_name VARCHAR(50) NOT NULL,
    currency_symbol VARCHAR(10) NOT NULL,
    decimal_places INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Currency exchange rates
CREATE TABLE IF NOT EXISTS currency_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL,
    to_currency CHAR(3) NOT NULL,
    exchange_rate NUMERIC(12,6) NOT NULL,
    valid_from TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    valid_until TIMESTAMPTZ,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_currency_pair_date UNIQUE (from_currency, to_currency, valid_from)
);

CREATE INDEX IF NOT EXISTS idx_currency_rates_pair ON currency_rates(from_currency, to_currency, valid_from DESC);
CREATE INDEX IF NOT EXISTS idx_currency_rates_valid ON currency_rates(valid_until) WHERE valid_until IS NOT NULL;

-- Subject localizations
CREATE TABLE IF NOT EXISTS subject_localizations (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    language_code CHAR(2) NOT NULL,
    localized_name VARCHAR(100) NOT NULL,
    localized_description TEXT,
    is_machine_translated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_subject_language UNIQUE (subject_id, language_code)
);

CREATE INDEX IF NOT EXISTS idx_subject_localizations_subject ON subject_localizations(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_localizations_language ON subject_localizations(language_code);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Basic subjects
INSERT INTO subjects (name, description, is_active) VALUES
    ('Mathematics', 'Algebra, Geometry, Calculus, Statistics', true),
    ('Science', 'Physics, Chemistry, Biology', true),
    ('English', 'Literature, Writing, Grammar', true),
    ('History', 'World History, US History, European History', true),
    ('Computer Science', 'Programming, Algorithms, Data Structures', true),
    ('Languages', 'Spanish, French, German, Mandarin', true),
    ('Arts', 'Music, Drawing, Painting', true),
    ('Business', 'Economics, Accounting, Management', true)
ON CONFLICT (name) DO NOTHING;

-- Supported languages
INSERT INTO supported_languages (language_code, language_name_en, language_name_native, is_rtl, translation_completeness) VALUES
    ('en', 'English', 'English', FALSE, 100),
    ('es', 'Spanish', 'Español', FALSE, 100),
    ('fr', 'French', 'Français', FALSE, 100),
    ('de', 'German', 'Deutsch', FALSE, 80),
    ('pt', 'Portuguese', 'Português', FALSE, 80),
    ('it', 'Italian', 'Italiano', FALSE, 60),
    ('zh', 'Chinese', '中文', FALSE, 60),
    ('ja', 'Japanese', '日本語', FALSE, 60),
    ('ko', 'Korean', '한국어', FALSE, 40),
    ('ar', 'Arabic', 'العربية', TRUE, 40),
    ('ru', 'Russian', 'Русский', FALSE, 40),
    ('hi', 'Hindi', 'हिन्दी', FALSE, 20)
ON CONFLICT (language_code) DO NOTHING;

-- Supported currencies
INSERT INTO supported_currencies (currency_code, currency_name, currency_symbol, decimal_places) VALUES
    ('USD', 'US Dollar', '$', 2),
    ('EUR', 'Euro', '€', 2),
    ('GBP', 'British Pound', '£', 2),
    ('CAD', 'Canadian Dollar', 'C$', 2),
    ('AUD', 'Australian Dollar', 'A$', 2),
    ('JPY', 'Japanese Yen', '¥', 0),
    ('CNY', 'Chinese Yuan', '¥', 2),
    ('BRL', 'Brazilian Real', 'R$', 2),
    ('INR', 'Indian Rupee', '₹', 2),
    ('MXN', 'Mexican Peso', 'Mex$', 2),
    ('KRW', 'South Korean Won', '₩', 0),
    ('RUB', 'Russian Ruble', '₽', 2)
ON CONFLICT (currency_code) DO NOTHING;

-- Currency exchange rates (base rates)
INSERT INTO currency_rates (from_currency, to_currency, exchange_rate, valid_from) VALUES
    ('USD', 'EUR', 0.92, CURRENT_TIMESTAMP),
    ('USD', 'GBP', 0.79, CURRENT_TIMESTAMP),
    ('USD', 'CAD', 1.36, CURRENT_TIMESTAMP),
    ('USD', 'AUD', 1.52, CURRENT_TIMESTAMP),
    ('USD', 'JPY', 149.50, CURRENT_TIMESTAMP),
    ('USD', 'BRL', 4.98, CURRENT_TIMESTAMP),
    ('USD', 'INR', 83.12, CURRENT_TIMESTAMP),
    ('EUR', 'USD', 1.09, CURRENT_TIMESTAMP),
    ('EUR', 'GBP', 0.86, CURRENT_TIMESTAMP),
    ('GBP', 'USD', 1.27, CURRENT_TIMESTAMP),
    ('GBP', 'EUR', 1.16, CURRENT_TIMESTAMP)
ON CONFLICT (from_currency, to_currency, valid_from) DO NOTHING;

-- ============================================================================
-- SELF-REFERENTIAL FOREIGN KEY
-- ============================================================================

-- Add foreign key for deleted_by after users table exists
ALTER TABLE users
DROP CONSTRAINT IF EXISTS users_deleted_by_fkey;

ALTER TABLE users
ADD CONSTRAINT users_deleted_by_fkey
FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- VIEWS (Read-only data access patterns)
-- ============================================================================

CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_profiles AS
SELECT * FROM tutor_profiles WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_bookings AS
SELECT * FROM bookings WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_payments AS
SELECT * FROM payments WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_refunds AS
SELECT * FROM refunds WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_wallets AS
SELECT * FROM wallets WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_wallet_transactions AS
SELECT * FROM wallet_transactions WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_payouts AS
SELECT * FROM payouts WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_notifications AS
SELECT * FROM notifications WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_conversations AS
SELECT * FROM conversations WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_favorite_tutors AS
SELECT * FROM favorite_tutors WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_student_packages AS
SELECT * FROM student_packages WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_subjects AS
SELECT * FROM tutor_subjects WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_availabilities AS
SELECT * FROM tutor_availabilities WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_certifications AS
SELECT * FROM tutor_certifications WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_education AS
SELECT * FROM tutor_education WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_reviews AS
SELECT * FROM reviews WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_messages AS
SELECT * FROM messages WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_message_attachments AS
SELECT * FROM message_attachments WHERE deleted_at IS NULL;

-- ============================================================================
-- SCHEMA MIGRATIONS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT,
    checksum VARCHAR(64)
);

-- ============================================================================
-- INITIALIZATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  EduStream Database Schema Initialized Successfully';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Migration: 001_baseline_schema.sql';
    RAISE NOTICE '  Consolidated from: Original migrations 001-056';
    RAISE NOTICE '  Architecture: Pure Data Storage (No DB Logic)';
    RAISE NOTICE '  Tables: 50+';
    RAISE NOTICE '  Indexes: 140+';
    RAISE NOTICE '';
    RAISE NOTICE '  All business logic handled in application code';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
END $$;
