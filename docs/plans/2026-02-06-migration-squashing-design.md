# Migration Squashing Design

**Date:** 2026-02-06
**Status:** Approved
**Author:** Claude Code

## Problem

Two related pain points with database schema management:
1. **Maintenance overhead** - Keeping `init.sql` synchronized with 39 migrations is tedious and error-prone
2. **Migration bloat** - 39 migration files becoming hard to manage

## Solution

Combine two approaches:
- **Squash migrations** into a single baseline
- **Abandon `init.sql`** - migrations become the only source of truth

## Design

### File Structure

**Before:**
```
database/
├── init.sql                    # 1,400 lines (DELETE)
├── SOURCE_OF_TRUTH.md
└── migrations/
    ├── 001_add_message_tracking_columns.sql
    ├── ... (39 files total)
    └── 056_comprehensive_database_fixes.sql
```

**After:**
```
database/
├── SOURCE_OF_TRUTH.md          # Updated
├── migrations/
│   └── 001_baseline_schema.sql # Single consolidated schema
└── migrations_archive/         # Historical reference
    └── (old migrations)
```

### Migration Tracking

Uses existing `schema_migrations` table:
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT,
    checksum VARCHAR(64)
);
```

Fresh databases run `001_baseline_schema.sql`, which records version `001`.
Future migrations start at `002_*.sql`.

### Implementation Steps

1. Create `001_baseline_schema.sql` from `init.sql`
2. Archive old migrations to `migrations_archive/`
3. Delete `init.sql`
4. Update `SOURCE_OF_TRUTH.md`
5. Update any scripts referencing `init.sql`
6. Test fresh database setup

## Deployment Context

- Production exists but can be reset (early stage)
- No complex migration path needed
- Fresh setup for all environments

## Future Migrations

All new schema changes go into numbered migrations:
```
migrations/
├── 001_baseline_schema.sql
├── 002_add_feature_x.sql
├── 003_fix_something.sql
└── ...
```
