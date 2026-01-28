# Alembic Database Migrations

This directory contains automated database migrations using Alembic.

## Setup

Alembic is now configured and ready to use. All future schema changes should be done through migrations.

## Common Commands

### Generate a New Migration

```bash
# Auto-generate migration from model changes
docker compose exec backend alembic revision --autogenerate -m "description of change"

# Manually create empty migration
docker compose exec backend alembic revision -m "description of change"
```

### Apply Migrations

```bash
# Upgrade to latest
docker compose exec backend alembic upgrade head

# Upgrade one version
docker compose exec backend alembic upgrade +1

# Upgrade to specific revision
docker compose exec backend alembic upgrade <revision_id>
```

### Rollback Migrations

```bash
# Downgrade one version
docker compose exec backend alembic downgrade -1

# Downgrade to specific revision
docker compose exec backend alembic downgrade <revision_id>

# Downgrade to base (remove all migrations)
docker compose exec backend alembic downgrade base
```

### View Migration History

```bash
# Show current version
docker compose exec backend alembic current

# Show migration history
docker compose exec backend alembic history

# Show pending migrations
docker compose exec backend alembic heads
```

## Migration Workflow

1. **Modify models** in `models.py`
2. **Generate migration**: `alembic revision --autogenerate -m "add new field"`
3. **Review migration** in `alembic/versions/`
4. **Test locally**: `alembic upgrade head`
5. **Commit migration** to git
6. **Deploy**: Migration runs automatically on startup

## Best Practices

### DO:
- ✅ Always review auto-generated migrations
- ✅ Test migrations locally before deploying
- ✅ Write descriptive migration messages
- ✅ Include both `upgrade()` and `downgrade()`
- ✅ Backup database before running migrations in production

### DON'T:
-  Edit existing migrations after they're deployed
-  Skip migration files (keep them in order)
-  Run migrations directly on production without testing
-  Forget to commit migration files to git

## Manual SQL Migrations

The following manual migrations exist in `database/migrations/` and should be run BEFORE using Alembic:

1. `001_standardize_booking_status.sql` - Uppercase status values
2. `002_consolidate_booking_url_fields.sql` - Remove duplicate meeting_url

### Apply Manual Migrations First

```bash
# Apply manual migrations
docker compose exec db psql -U postgres -d authapp -f /docker-entrypoint-initdb.d/migrations/001_standardize_booking_status.sql
docker compose exec db psql -U postgres -d authapp -f /docker-entrypoint-initdb.d/migrations/002_consolidate_booking_url_fields.sql

# Then initialize Alembic (marks current state as base)
docker compose exec backend alembic stamp head
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
alembic current

# Force stamp to specific version
alembic stamp <revision_id>
```

### "Can't locate revision identified by 'xyz'"
```bash
# Verify migration files exist
ls alembic/versions/

# Re-initialize if needed
alembic downgrade base
alembic upgrade head
```

### "Multiple head revisions"
```bash
# Merge heads
alembic merge heads -m "merge migrations"
```

## Production Deployment

Add to your deployment script:

```bash
# Before starting application
docker compose exec backend alembic upgrade head

# Then start application
docker compose up -d
```

## CI/CD Integration

Add to `.github/workflows/deploy.yml`:

```yaml
- name: Run migrations
  run: |
    docker compose exec -T backend alembic upgrade head
```
