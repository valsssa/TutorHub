# Database Source of Truth

This directory now contains only **one living schema** and a few **reference copies**. The intent of this document is to highlight the duplicates that already exist under `database/` and to point every maintainer to `database/init.sql` (and `database/migrations/`) as the single, authoritative source.

## Canonical assets

- `database/init.sql` – the consolidated, up‑to‑date schema. All new columns, constraints, indexes, seeding blocks, and trigger definitions belong here.
- `database/migrations/` – the migrations that the backend executes as part of startup. These files are the only scripts that should be modified or added when evolving the schema.

## Duplicate/archival copies

1. `database/init.sql.backup.20251014_131325`  
   - A historical snapshot of `init.sql` from November 2025. It contains many of the same table/index definitions plus legacy triggers and business logic that were subsequently moved into the application.
   - **Action**: Keep this file for reference but **do not** edit it; all live schema work happens in `database/init.sql`.

2. `database/migrations_archive/`  
   - Contains earlier migration versions (`001`–`020`) that were captured for auditing purposes. Their SQL is duplicated by the active migration pipeline only when a rebuild of a production database is required.
   - **Action**: Use this folder only for historical comparison. New migrations belong in `database/migrations/`.

## Enforcement

- When reviewing or documenting schema changes, refer only to `database/init.sql` and the files in `database/migrations/`.
- Remove any future duplicates by migrating them back into these paths and updating this document if new archival copies are created.

