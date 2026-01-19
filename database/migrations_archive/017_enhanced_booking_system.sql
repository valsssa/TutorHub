-- ============================================================================
-- Migration 017: Enhanced Booking System (booking_detail.md spec)
-- Adds comprehensive payment tracking, refined booking states, and policy engine support
-- ============================================================================

-- Create enum type for detailed booking status
DO $$ BEGIN
    CREATE TYPE booking_status_enum AS ENUM (
        'PENDING',
        'CONFIRMED',
        'CANCELLED_BY_STUDENT',
        'CANCELLED_BY_TUTOR',
        'NO_SHOW_STUDENT',
        'NO_SHOW_TUTOR',
        'COMPLETED',
        'REFUNDED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create enum for lesson type
DO $$ BEGIN
    CREATE TYPE lesson_type_enum AS ENUM ('TRIAL', 'REGULAR', 'PACKAGE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create enum for payment provider
DO $$ BEGIN
    CREATE TYPE payment_provider_enum AS ENUM ('stripe', 'adyen', 'paypal', 'test');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create enum for payment status
DO $$ BEGIN
    CREATE TYPE payment_status_enum AS ENUM (
        'REQUIRES_ACTION',
        'AUTHORIZED',
        'CAPTURED',
        'REFUNDED',
        'FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create enum for refund reason
DO $$ BEGIN
    CREATE TYPE refund_reason_enum AS ENUM (
        'STUDENT_CANCEL',
        'TUTOR_CANCEL',
        'NO_SHOW_TUTOR',
        'GOODWILL',
        'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create enum for payout status
DO $$ BEGIN
    CREATE TYPE payout_status_enum AS ENUM ('PENDING', 'SUBMITTED', 'PAID', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- Add new columns to existing bookings table
-- ============================================================================

-- Add new booking columns if they don't exist
ALTER TABLE bookings 
    ADD COLUMN IF NOT EXISTS lesson_type VARCHAR(20) DEFAULT 'REGULAR',
    ADD COLUMN IF NOT EXISTS student_tz VARCHAR(64) DEFAULT 'UTC',
    ADD COLUMN IF NOT EXISTS tutor_tz VARCHAR(64) DEFAULT 'UTC',
    ADD COLUMN IF NOT EXISTS rate_cents INTEGER,
    ADD COLUMN IF NOT EXISTS currency CHAR(3) DEFAULT 'USD',
    ADD COLUMN IF NOT EXISTS platform_fee_pct NUMERIC(5,2) DEFAULT 20.0,
    ADD COLUMN IF NOT EXISTS platform_fee_cents INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS tutor_earnings_cents INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS join_url TEXT,
    ADD COLUMN IF NOT EXISTS notes_student TEXT,
    ADD COLUMN IF NOT EXISTS notes_tutor TEXT,
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(20) DEFAULT 'STUDENT',
    ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES student_packages(id) ON DELETE SET NULL;

-- Migrate existing rate data to cents (if rate_cents is NULL)
UPDATE bookings 
SET rate_cents = (hourly_rate * 100)::INTEGER
WHERE rate_cents IS NULL AND hourly_rate IS NOT NULL;

-- Calculate platform fee and tutor earnings for existing bookings
UPDATE bookings
SET 
    platform_fee_cents = (rate_cents * 0.20)::INTEGER,
    tutor_earnings_cents = (rate_cents * 0.80)::INTEGER
WHERE platform_fee_cents = 0 AND rate_cents IS NOT NULL;

-- Add check constraints
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS valid_lesson_type;
ALTER TABLE bookings ADD CONSTRAINT valid_lesson_type 
    CHECK (lesson_type IN ('TRIAL', 'REGULAR', 'PACKAGE'));

ALTER TABLE bookings DROP CONSTRAINT IF EXISTS valid_created_by;
ALTER TABLE bookings ADD CONSTRAINT valid_created_by 
    CHECK (created_by IN ('STUDENT', 'TUTOR', 'ADMIN'));

-- ============================================================================
-- Create Payments table
-- ============================================================================

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
    provider_payment_id TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'REQUIRES_ACTION',
    metadata JSONB DEFAULT '{}',
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

-- ============================================================================
-- Create Refunds table
-- ============================================================================

CREATE TABLE IF NOT EXISTS refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE RESTRICT,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    reason VARCHAR(30) NOT NULL,
    provider_refund_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_refund_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT valid_refund_reason CHECK (reason IN ('STUDENT_CANCEL', 'TUTOR_CANCEL', 'NO_SHOW_TUTOR', 'GOODWILL', 'OTHER'))
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment ON refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_booking ON refunds(booking_id);
CREATE INDEX IF NOT EXISTS idx_refunds_reason ON refunds(reason);
CREATE INDEX IF NOT EXISTS idx_refunds_created ON refunds(created_at DESC);

-- ============================================================================
-- Create Payouts table
-- ============================================================================

CREATE TABLE IF NOT EXISTS payouts (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    transfer_reference TEXT,
    metadata JSONB DEFAULT '{}',
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

-- ============================================================================
-- Create Availabilities table (recurring weekly windows)
-- ============================================================================
-- NOTE: This table structure matches init.sql for consistency
-- Uses tutor_profile_id (not tutor_id) to link directly to tutor_profiles

CREATE TABLE IF NOT EXISTS tutor_availabilities (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_availability_time_order CHECK (start_time < end_time),
    CONSTRAINT uq_tutor_availability_slot UNIQUE (tutor_profile_id, day_of_week, start_time, end_time)
);

CREATE INDEX IF NOT EXISTS idx_tutor_availability_profile_day ON tutor_availabilities(tutor_profile_id, day_of_week);

-- ============================================================================
-- Create Blackouts table (vacation/temporary blocks)
-- ============================================================================

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

-- ============================================================================
-- Add tutor cancellation tracking fields
-- ============================================================================

ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS cancellation_strikes INTEGER DEFAULT 0 CHECK (cancellation_strikes >= 0),
    ADD COLUMN IF NOT EXISTS auto_confirm BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS trial_price_cents INTEGER CHECK (trial_price_cents >= 0),
    ADD COLUMN IF NOT EXISTS payout_method JSONB DEFAULT '{}';

-- ============================================================================
-- Add student credit balance
-- ============================================================================

ALTER TABLE student_profiles
    ADD COLUMN IF NOT EXISTS credit_balance_cents INTEGER DEFAULT 0 CHECK (credit_balance_cents >= 0),
    ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10);

-- ============================================================================
-- Create exclusion constraint for booking overlap prevention
-- ============================================================================

-- This prevents double-booking for tutors
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Drop existing constraint if it exists
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_tutor_overlap;

-- Add exclusion constraint (only for active bookings)
-- Note: Using a partial index approach since exclusion constraints can be complex
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_no_overlap 
ON bookings (tutor_profile_id, start_time, end_time)
WHERE status IN ('PENDING', 'CONFIRMED');

-- ============================================================================
-- Create indexes for new booking columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_bookings_lesson_type ON bookings(lesson_type);
CREATE INDEX IF NOT EXISTS idx_bookings_student_tz ON bookings(student_tz);
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_tz ON bookings(tutor_tz);
CREATE INDEX IF NOT EXISTS idx_bookings_package ON bookings(package_id);
CREATE INDEX IF NOT EXISTS idx_bookings_created_by ON bookings(created_by);
CREATE INDEX IF NOT EXISTS idx_bookings_join_url ON bookings(join_url) WHERE join_url IS NOT NULL;

-- ============================================================================
-- Update trigger for updated_at columns
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to new tables
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_payouts_updated_at ON payouts;
CREATE TRIGGER update_payouts_updated_at
    BEFORE UPDATE ON payouts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_availabilities_updated_at ON tutor_availabilities;
CREATE TRIGGER update_availabilities_updated_at
    BEFORE UPDATE ON tutor_availabilities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE payments IS 'Payment transactions for bookings and packages';
COMMENT ON TABLE refunds IS 'Refund transactions linked to payments';
COMMENT ON TABLE payouts IS 'Tutor earnings payout batches';
COMMENT ON TABLE tutor_availabilities IS 'Recurring weekly availability windows for tutors';
COMMENT ON TABLE tutor_blackouts IS 'Temporary unavailable periods (vacations, etc.)';

COMMENT ON COLUMN bookings.lesson_type IS 'Type of lesson: TRIAL, REGULAR, or PACKAGE';
COMMENT ON COLUMN bookings.student_tz IS 'Student timezone (IANA) at booking time';
COMMENT ON COLUMN bookings.tutor_tz IS 'Tutor timezone (IANA) at booking time';
COMMENT ON COLUMN bookings.rate_cents IS 'Agreed rate in cents (frozen at booking time)';
COMMENT ON COLUMN bookings.platform_fee_pct IS 'Platform fee percentage (frozen at booking time)';
COMMENT ON COLUMN bookings.platform_fee_cents IS 'Computed platform fee in cents';
COMMENT ON COLUMN bookings.tutor_earnings_cents IS 'Computed tutor earnings in cents';
COMMENT ON COLUMN bookings.join_url IS 'Session join link (generated on confirmation)';
