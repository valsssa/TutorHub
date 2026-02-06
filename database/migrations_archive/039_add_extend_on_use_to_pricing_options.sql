-- Migration 039: Add extend_on_use to tutor_pricing_options
-- Purpose: Enable rolling expiry behavior for packages
-- When extend_on_use is TRUE, package validity extends on each credit use
-- Date: 2026-01-29

-- Add extend_on_use column (defaults to FALSE for existing packages)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tutor_pricing_options' AND column_name = 'extend_on_use'
    ) THEN
        ALTER TABLE tutor_pricing_options ADD COLUMN extend_on_use BOOLEAN DEFAULT FALSE NOT NULL;
    END IF;
END $$;

-- Add comment explaining the column
COMMENT ON COLUMN tutor_pricing_options.extend_on_use IS 'When TRUE, package expiration extends by validity_days on each credit use (rolling expiry). When FALSE, expiration is fixed from purchase date.';

-- Add expiry_warning_sent column to student_packages to track if warning was sent
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'student_packages' AND column_name = 'expiry_warning_sent'
    ) THEN
        ALTER TABLE student_packages ADD COLUMN expiry_warning_sent BOOLEAN DEFAULT FALSE NOT NULL;
    END IF;
END $$;

COMMENT ON COLUMN student_packages.expiry_warning_sent IS 'Whether an expiration warning notification has been sent for this package';
