# Database Migrations

## Auto-Applied on Startup

Migrations in this directory are **automatically applied** when the backend starts up.

## How It Works

1. **Naming Convention**: Files must be named `{version}_{description}.sql`
   - Example: `001_add_message_columns.sql`
   - Version determines execution order (001, 002, 003, etc.)

2. **Automatic Execution**:
   - On startup, backend scans this directory
   - Applies pending migrations in order
   - Tracks applied migrations in `schema_migrations` table
   - Each migration runs exactly once

3. **Idempotent**: All migrations should be safe to re-run
   - Use `ADD COLUMN IF NOT EXISTS`
   - Use `CREATE INDEX IF NOT EXISTS`
   - Use `COALESCE` for updates

## Current Migrations

- `001_add_message_tracking_columns.sql` - Adds read receipts, edit tracking, and timestamp management

## Creating New Migrations

1. Create new file: `{next_version}_{description}.sql`
2. Write idempotent SQL
3. Commit to Git
4. Restart backend (or deploy) - migration applies automatically

## Example Migration

```sql
-- Migration 002: Add Booking Notes Column
-- Adds optional notes field for bookings

ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS notes TEXT;

CREATE INDEX IF NOT EXISTS idx_bookings_notes 
ON bookings(notes) WHERE notes IS NOT NULL;
```

## Rollback

Migrations don't support automatic rollback. To revert:
1. Create a new migration that reverses the changes
2. Example: `003_remove_booking_notes.sql`

## Production Deployment

✅ **Safe**: Migrations are idempotent and tested
✅ **Automatic**: No manual database updates needed
✅ **Tracked**: `schema_migrations` table shows applied migrations
✅ **Fast**: Only pending migrations run

---

**Philosophy**: Keep migrations simple, SQL-based, and automatic. No complex framework needed (DDD+KISS).

