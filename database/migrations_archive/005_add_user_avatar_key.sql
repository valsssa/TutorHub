-- ============================================================================
-- Migration: Add avatar_key to users for secure avatar storage
-- Created: 2025-02-14
-- ============================================================================

ALTER TABLE users
ADD COLUMN IF NOT EXISTS avatar_key VARCHAR(255);

-- Index for quick lookup when generating signed URLs
CREATE INDEX IF NOT EXISTS idx_users_avatar_key ON users(avatar_key) WHERE avatar_key IS NOT NULL;

COMMENT ON COLUMN users.avatar_key IS 'Object storage key for the user avatar stored in MinIO/S3';
