-- Migration 027: Add validity_days to tutor_pricing_options
-- Purpose: Allow pricing options to specify package expiration period
-- Date: 2026-01-28

-- Add validity_days column (nullable, in days)
ALTER TABLE tutor_pricing_options
ADD COLUMN validity_days INTEGER DEFAULT NULL;

-- Add check constraint to ensure validity_days is positive if set
ALTER TABLE tutor_pricing_options
ADD CONSTRAINT positive_validity_days CHECK (validity_days IS NULL OR validity_days > 0);

-- Add comment
COMMENT ON COLUMN tutor_pricing_options.validity_days IS 'Number of days after purchase that the package expires (NULL = no expiration)';
