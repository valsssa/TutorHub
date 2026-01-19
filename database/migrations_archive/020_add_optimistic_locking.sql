-- Migration 020: Add optimistic locking for concurrent edits
-- Prevents lost updates when multiple devices edit availability/pricing simultaneously

-- Add version column to tutor_profiles for optimistic locking
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Create index for efficient version checks
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_version ON tutor_profiles(id, version);

-- Comment explaining the versioning strategy
COMMENT ON COLUMN tutor_profiles.version IS 'Optimistic locking version - incremented on every update to availability or pricing collections';
