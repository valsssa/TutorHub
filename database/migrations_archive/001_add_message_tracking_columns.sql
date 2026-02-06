-- Migration 001: Add Message Tracking Columns
-- Adds read receipts, edit tracking, and timestamp management to messages

-- Add new columns (idempotent - safe to re-run)
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;

-- Set updated_at for existing records
UPDATE messages 
SET updated_at = COALESCE(updated_at, created_at)
WHERE updated_at IS NULL;

-- Create performance index
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at DESC);

