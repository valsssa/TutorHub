-- Migration: Rename notifications.metadata to extra_data
-- Description: SQLAlchemy reserves 'metadata' as an attribute name, so we rename the column
-- to 'extra_data' to avoid conflicts.

-- Only rename the column if 'metadata' exists and 'extra_data' does not
DO $$
BEGIN
    -- Check if 'metadata' column exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'notifications' AND column_name = 'metadata'
    ) THEN
        -- Rename metadata to extra_data
        ALTER TABLE notifications RENAME COLUMN metadata TO extra_data;
        RAISE NOTICE 'Renamed notifications.metadata to extra_data';
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'notifications' AND column_name = 'extra_data'
    ) THEN
        -- Neither column exists, add extra_data
        ALTER TABLE notifications ADD COLUMN extra_data JSONB DEFAULT '{}'::JSONB;
        RAISE NOTICE 'Added extra_data column to notifications';
    ELSE
        RAISE NOTICE 'Column extra_data already exists, skipping';
    END IF;
END $$;

-- Drop delivery_channels column if it exists (not in model)
ALTER TABLE notifications DROP COLUMN IF EXISTS delivery_channels;
