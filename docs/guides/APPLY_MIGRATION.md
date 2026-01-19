# Apply Database Migration - Remote Dev Server

## Quick Fix for Message System

The message system code has been refactored but requires a database schema update. Run this single SQL file on your remote dev server:

### Option 1: Via Docker (Recommended)

```bash
# If using docker-compose on remote server
cat database/migrations/001_add_message_tracking_columns.sql | \
  docker compose exec -T db psql -U postgres -d authapp
```

### Option 2: Direct PostgreSQL Connection

```bash
# Connect to remote database
psql -h <host> -U postgres -d authapp -f database/migrations/001_add_message_tracking_columns.sql
```

### Option 3: Via psql Interactive

```bash
# Connect to database
psql -h <host> -U postgres -d authapp

# Then run:
\i database/migrations/001_add_message_tracking_columns.sql
```

### Option 4: Copy-Paste (If no file access)

Connect to your database and run this SQL:

```sql
-- Add new columns to messages table
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;

-- Set updated_at for existing records
UPDATE messages 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Create index
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at DESC);

-- Verify
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'messages' 
AND column_name IN ('read_at', 'is_edited', 'edited_at', 'updated_at')
ORDER BY column_name;
```

## What This Fixes

This migration adds 4 columns to the `messages` table:
- `read_at` - Timestamp when message was read
- `is_edited` - Boolean flag for edited messages
- `edited_at` - Timestamp of last edit
- `updated_at` - Auto-updated timestamp (managed by application code)

## Verification

After running the migration, verify it worked:

```sql
-- Check columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'messages' 
AND column_name IN ('read_at', 'is_edited', 'edited_at', 'updated_at');

-- Should show 4 rows
```

## Safety

- Migration is idempotent (safe to run multiple times)
- Uses `ADD COLUMN IF NOT EXISTS` to prevent errors
- Sets default values for existing records
- No data loss

## After Migration

Once applied, the message system will work with all features:
- ✅ Send/receive messages
- ✅ Read receipts
- ✅ Message editing (within 15 minutes)
- ✅ Message deletion (soft delete)
- ✅ Typing indicators
- ✅ Real-time delivery via WebSocket

---

**Note:** This is a one-time migration. Future deployments will use `database/init.sql` which already includes these columns for fresh installs.

