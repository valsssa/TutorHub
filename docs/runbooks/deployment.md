# Deployment Runbook

## Quick Reference

| Operation | Command |
|-----------|---------|
| Deploy (rebuild) | `docker compose up --build -d` |
| Deploy (no rebuild) | `docker compose up -d` |
| View status | `docker compose ps` |
| View logs | `docker compose logs -f` |
| Rollback | See [Rollback Procedure](#rollback-procedure) |

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing (`docker compose -f docker-compose.test.yml up --abort-on-container-exit`)
- [ ] Code reviewed and approved
- [ ] Database migration tested in staging
- [ ] Feature flags configured (if applicable)
- [ ] Team notified in Slack
- [ ] Backup created (for major releases)

---

## Standard Deployment

### When to Use
- Regular releases
- Bug fixes
- Minor updates

### Procedure

1. **Notify team**
   ```
   Post in #deployments: "Starting deployment of [version/feature] to production"
   ```

2. **Pull latest code**
   ```bash
   cd /path/to/Project1-splitversion
   git pull origin main
   ```

3. **Review changes**
   ```bash
   git log --oneline -10
   ```

4. **Build and deploy**
   ```bash
   # Build new images and restart
   docker compose up --build -d
   ```

5. **Monitor logs for errors**
   ```bash
   docker compose logs -f --tail=100
   ```

6. **Verify health**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:3000
   ```

7. **Verify key functionality**
   - [ ] Login works
   - [ ] Tutor search works
   - [ ] Can create booking (use test account)

8. **Notify team**
   ```
   Post in #deployments: "Deployment complete. All systems healthy."
   ```

### Expected Duration
- Build: 2-5 minutes
- Startup: 30-60 seconds
- Verification: 2-5 minutes
- **Total: ~10 minutes**

---

## Zero-Downtime Deployment

### When to Use
- Production deployments during business hours
- Critical bug fixes

### Procedure

1. **Deploy backend only (maintains frontend)**
   ```bash
   docker compose up --build -d --no-deps backend
   ```

2. **Wait for backend to be healthy**
   ```bash
   # Wait for health check
   sleep 10
   curl http://localhost:8000/health
   ```

3. **Deploy frontend**
   ```bash
   docker compose up --build -d --no-deps frontend
   ```

4. **Verify both services**
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   curl http://localhost:3000
   ```

---

## Rollback Procedure

### When to Use
- Deployment caused errors
- Critical functionality broken
- Performance degradation

### Procedure

1. **Identify the problem**
   ```bash
   docker compose logs --tail=200 backend
   docker compose logs --tail=200 frontend
   ```

2. **Get previous commit**
   ```bash
   git log --oneline -5
   # Note the commit hash before the problematic deployment
   ```

3. **Rollback code**
   ```bash
   git checkout <previous-commit-hash>
   ```

4. **Rebuild and deploy**
   ```bash
   docker compose up --build -d
   ```

5. **Verify health**
   ```bash
   curl http://localhost:8000/health
   ```

6. **If database migration was involved**
   - Restore from pre-deployment backup (see [Database Runbook](./database.md))

7. **Notify team**
   ```
   Post in #deployments: "ROLLBACK completed. Investigating issue."
   ```

8. **Create incident report**
   - What happened
   - Why rollback was needed
   - Root cause
   - Prevention measures

---

## Deployment with Database Migration

### When to Use
- Schema changes
- New tables
- Column modifications

### Procedure

1. **Create database backup**
   ```bash
   docker compose exec db pg_dump -U postgres -Fc authapp > backup_pre_deploy_$(date +%Y%m%d_%H%M%S).dump
   ```

2. **Stop backend (prevent writes during migration)**
   ```bash
   docker compose stop backend
   ```

3. **Apply migration manually (if needed)**
   ```bash
   docker compose exec db psql -U postgres -d authapp -f database/migrations/XXX_new_migration.sql
   ```

4. **Rebuild and start backend**
   ```bash
   docker compose up --build -d backend
   ```

5. **Verify migration applied**
   ```bash
   docker compose exec db psql -U postgres -d authapp -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 1;"
   ```

6. **Verify application health**
   ```bash
   curl http://localhost:8000/health
   ```

### Rollback
If migration fails:
```bash
# Stop backend
docker compose stop backend

# Restore database
docker compose exec -T db pg_restore -U postgres -d authapp --clean < backup_pre_deploy_YYYYMMDD_HHMMSS.dump

# Rollback code
git checkout <previous-commit>

# Restart
docker compose up --build -d
```

---

## Emergency Deployment (Hotfix)

### When to Use
- Critical bug in production
- Security vulnerability
- Data corruption

### Procedure

1. **Assess severity**
   - P1: Fix within 1 hour
   - P2: Fix within 4 hours

2. **Create hotfix branch**
   ```bash
   git checkout -b hotfix/critical-fix main
   ```

3. **Make minimal fix**
   - Only fix the critical issue
   - No refactoring
   - No additional features

4. **Quick test**
   ```bash
   # Run affected tests only
   pytest backend/tests/test_affected_module.py -v
   ```

5. **Deploy immediately**
   ```bash
   docker compose up --build -d
   ```

6. **Monitor closely**
   ```bash
   docker compose logs -f --tail=100
   ```

7. **Post-incident**
   - Merge hotfix to main
   - Write incident report
   - Schedule proper fix if needed

---

## View Deployment Status

### Current running versions
```bash
docker compose ps
```

### Container resource usage
```bash
docker stats
```

### Recent deployment logs
```bash
docker compose logs --tail=50 backend
docker compose logs --tail=50 frontend
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs backend

# Check if port is in use
lsof -i :8000

# Force recreate
docker compose up --force-recreate -d backend
```

### Out of disk space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes
```

### Memory issues
```bash
# Check memory
free -h

# Check container memory
docker stats --no-stream
```
