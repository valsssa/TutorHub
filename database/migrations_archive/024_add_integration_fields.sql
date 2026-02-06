-- Migration 024: Add integration fields for Stripe, Google OAuth, and Zoom
-- Adds fields required for payment processing, OAuth authentication, and video conferencing

-- =============================================================================
-- 1. USER TABLE: Add Google OAuth and Owner role
-- =============================================================================

-- Add Google OAuth ID for social login
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);

-- Add unique constraint and index for google_id
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_users_google_id'
  ) THEN
    CREATE UNIQUE INDEX idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;
  END IF;
END $$;

-- Update role constraint to include 'owner' role
ALTER TABLE users
  DROP CONSTRAINT IF EXISTS valid_role;

ALTER TABLE users
  ADD CONSTRAINT valid_role CHECK (role IN ('student', 'tutor', 'admin', 'owner'));

COMMENT ON COLUMN users.google_id IS 'Google OAuth subject ID for social login';


-- =============================================================================
-- 2. TUTOR_PROFILES TABLE: Add Stripe Connect fields
-- =============================================================================

ALTER TABLE tutor_profiles
  ADD COLUMN IF NOT EXISTS stripe_account_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS stripe_charges_enabled BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS stripe_payouts_enabled BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS stripe_onboarding_completed BOOLEAN DEFAULT FALSE;

-- Add index for Stripe account lookups
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_tutor_profiles_stripe_account'
  ) THEN
    CREATE INDEX idx_tutor_profiles_stripe_account ON tutor_profiles(stripe_account_id) WHERE stripe_account_id IS NOT NULL;
  END IF;
END $$;

COMMENT ON COLUMN tutor_profiles.stripe_account_id IS 'Stripe Connect account ID (acct_...)';
COMMENT ON COLUMN tutor_profiles.stripe_charges_enabled IS 'Whether Stripe account can accept charges';
COMMENT ON COLUMN tutor_profiles.stripe_payouts_enabled IS 'Whether Stripe account can receive payouts';
COMMENT ON COLUMN tutor_profiles.stripe_onboarding_completed IS 'Whether tutor has completed Stripe onboarding';


-- =============================================================================
-- 3. BOOKINGS TABLE: Add Stripe and Zoom integration fields
-- =============================================================================

ALTER TABLE bookings
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS zoom_meeting_id VARCHAR(255);

-- Add indexes for integration ID lookups
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_bookings_stripe_session'
  ) THEN
    CREATE INDEX idx_bookings_stripe_session ON bookings(stripe_checkout_session_id) WHERE stripe_checkout_session_id IS NOT NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_bookings_zoom_meeting'
  ) THEN
    CREATE INDEX idx_bookings_zoom_meeting ON bookings(zoom_meeting_id) WHERE zoom_meeting_id IS NOT NULL;
  END IF;
END $$;

COMMENT ON COLUMN bookings.stripe_checkout_session_id IS 'Stripe Checkout session ID for payment tracking';
COMMENT ON COLUMN bookings.zoom_meeting_id IS 'Zoom meeting ID for video conferencing';


-- =============================================================================
-- 4. PAYMENTS TABLE: Add Stripe-specific tracking fields
-- =============================================================================

ALTER TABLE payments
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS refund_amount_cents INTEGER,
  ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Add indexes for Stripe ID lookups
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_payments_stripe_session'
  ) THEN
    CREATE INDEX idx_payments_stripe_session ON payments(stripe_checkout_session_id) WHERE stripe_checkout_session_id IS NOT NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_payments_stripe_intent'
  ) THEN
    CREATE INDEX idx_payments_stripe_intent ON payments(stripe_payment_intent_id) WHERE stripe_payment_intent_id IS NOT NULL;
  END IF;
END $$;

-- Update payment status constraint to support Stripe statuses
ALTER TABLE payments
  DROP CONSTRAINT IF EXISTS valid_payment_status;

ALTER TABLE payments
  ADD CONSTRAINT valid_payment_status CHECK (
    status IN (
      'pending', 'completed', 'failed', 'refunded', 'partially_refunded',
      'REQUIRES_ACTION', 'AUTHORIZED', 'CAPTURED', 'REFUNDED', 'FAILED'
    )
  );

COMMENT ON COLUMN payments.stripe_checkout_session_id IS 'Stripe Checkout session ID';
COMMENT ON COLUMN payments.stripe_payment_intent_id IS 'Stripe PaymentIntent ID (pi_...)';
COMMENT ON COLUMN payments.paid_at IS 'Timestamp when payment was successfully captured';
COMMENT ON COLUMN payments.refunded_at IS 'Timestamp when payment was refunded';
COMMENT ON COLUMN payments.refund_amount_cents IS 'Amount refunded in cents (for partial refunds)';
COMMENT ON COLUMN payments.error_message IS 'Error message if payment failed';


-- =============================================================================
-- 5. Migration verification
-- =============================================================================

-- Verify columns exist (will fail silently if already applied)
DO $$
DECLARE
  col_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'users' AND column_name = 'google_id';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: users.google_id column not created';
  END IF;

  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'tutor_profiles' AND column_name = 'stripe_account_id';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: tutor_profiles.stripe_account_id column not created';
  END IF;

  RAISE NOTICE 'Migration 024 completed successfully: Integration fields added';
END $$;
