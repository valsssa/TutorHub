# Database Operations Runbook

## Quick Reference

| Operation | Command |
|-----------|---------|
| Connect to database | `docker compose exec db psql -U postgres -d authapp` |
| Create backup | See [Manual Backup](#manual-backup) |
| Restore backup | See [Restore from Backup](#restore-from-backup) |
| Run migrations | See [Apply Migrations](#apply-migrations) |

---

## Manual Backup

### When to Use
- Before major deployments
- Before running migrations
- Ad-hoc backup requests
- Before any destructive operations

### Procedure

1. **Create backup file**
   ```bash
   # Navigate to project directory
   cd /path/to/Project1-splitversion

   # Create timestamped backup
   docker compose exec db pg_dump -U postgres -Fc authapp > backup_$(date +%Y%m%d_%H%M%S).dump
   ```

2. **Verify backup was created**
   ```bash
   ls -la backup_*.dump
   ```

3. **Copy to secure storage** (recommended)
   ```bash
   # Example: Copy to S3
   aws s3 cp backup_*.dump s3://edustream-backups/database/
   ```

### Expected Output
- File named `backup_YYYYMMDD_HHMMSS.dump`
- File size should be proportional to database size (check previous backups)

---

## Restore from Backup

### When to Use
- Disaster recovery
- Rollback after failed migration
- Data corruption recovery

### Prerequisites
- Backup file available
- All services stopped (backend)
- Database accessible

### Procedure

1. **Stop the backend service**
   ```bash
   docker compose stop backend
   ```

2. **Verify backup file exists**
   ```bash
   ls -la backup_YYYYMMDD_HHMMSS.dump
   ```

3. **Restore the database**
   ```bash
   # Option 1: Restore to existing database (will fail if objects exist)
   docker compose exec -T db pg_restore -U postgres -d authapp < backup_YYYYMMDD_HHMMSS.dump

   # Option 2: Drop and recreate database (DESTRUCTIVE)
   docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS authapp;"
   docker compose exec db psql -U postgres -c "CREATE DATABASE authapp;"
   docker compose exec -T db pg_restore -U postgres -d authapp < backup_YYYYMMDD_HHMMSS.dump
   ```

4. **Verify restoration**
   ```bash
   docker compose exec db psql -U postgres -d authapp -c "SELECT COUNT(*) FROM users;"
   ```

5. **Restart the backend**
   ```bash
   docker compose start backend
   ```

6. **Verify application health**
   ```bash
   curl http://localhost:8000/health
   ```

### Rollback
If restoration fails, restore from an earlier backup.

---

## Apply Migrations

### When to Use
- Deploying new features with schema changes
- Manual migration application

### Procedure

1. **Check current schema state**
   ```bash
   docker compose exec db psql -U postgres -d authapp -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 5;"
   ```

2. **Review pending migrations**
   ```bash
   ls -la database/migrations/
   ```

3. **Create backup before migration**
   ```bash
   docker compose exec db pg_dump -U postgres -Fc authapp > backup_pre_migration_$(date +%Y%m%d_%H%M%S).dump
   ```

4. **Apply migrations**

   Migrations are auto-applied on backend startup. To manually apply:
   ```bash
   # Apply specific migration
   docker compose exec db psql -U postgres -d authapp -f database/migrations/XXX_migration_name.sql
   ```

5. **Verify migration applied**
   ```bash
   docker compose exec db psql -U postgres -d authapp -c "SELECT * FROM schema_migrations WHERE version = 'XXX';"
   ```

### Rollback
Migrations don't have automatic rollback. To rollback:
1. Restore from pre-migration backup
2. Or manually write and apply reverse migration

---

## Check Database Health

### Connection Count
```bash
docker compose exec db psql -U postgres -d authapp -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'authapp';"
```

### Table Sizes
```bash
docker compose exec db psql -U postgres -d authapp -c "
SELECT
  relname as table,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
"
```

### Long-Running Queries
```bash
docker compose exec db psql -U postgres -d authapp -c "
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query,
  state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state != 'idle';
"
```

### Kill Long-Running Query
```bash
docker compose exec db psql -U postgres -d authapp -c "SELECT pg_terminate_backend(PID);"
```

---

## Emergency: Database Unresponsive

1. **Check if PostgreSQL is running**
   ```bash
   docker compose ps db
   ```

2. **Check logs**
   ```bash
   docker compose logs --tail=100 db
   ```

3. **Restart PostgreSQL**
   ```bash
   docker compose restart db
   ```

4. **If still unresponsive, check disk space**
   ```bash
   docker compose exec db df -h
   ```

5. **Check memory**
   ```bash
   docker stats db
   ```

---

## Scheduled Backup Setup

For automated daily backups, add to crontab:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/Project1-splitversion && docker compose exec -T db pg_dump -U postgres -Fc authapp > /backups/edustream_$(date +\%Y\%m\%d).dump && find /backups -name "edustream_*.dump" -mtime +30 -delete
```
