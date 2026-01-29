-- Migration 027: Add validity_days to tutor_pricing_options
-- Purpose: Allow pricing options to specify package expiration period
-- Date: 2026-01-28

-- Add validity_days column (nullable, in days) if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tutor_pricing_options' AND column_name = 'validity_days'
    ) THEN
        ALTER TABLE tutor_pricing_options ADD COLUMN validity_days INTEGER DEFAULT NULL;
    END IF;
END $$;

-- Add check constraint to ensure validity_days is positive if set (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'positive_validity_days' AND table_name = 'tutor_pricing_options'
    ) THEN
        ALTER TABLE tutor_pricing_options
        ADD CONSTRAINT positive_validity_days CHECK (validity_days IS NULL OR validity_days > 0);
    END IF;
END $$;

-- Add comment
COMMENT ON COLUMN tutor_pricing_options.validity_days IS 'Number of days after purchase that the package expires (NULL = no expiration)';
