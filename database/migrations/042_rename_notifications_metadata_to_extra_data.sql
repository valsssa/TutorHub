-- Migration: Rename notifications.metadata to extra_data
-- Description: SQLAlchemy reserves 'metadata' as an attribute name, so we rename the column
-- to 'extra_data' to avoid conflicts.

-- Rename the column
ALTER TABLE notifications RENAME COLUMN metadata TO extra_data;

-- Drop delivery_channels column if it exists (not in model)
ALTER TABLE notifications DROP COLUMN IF EXISTS delivery_channels;
