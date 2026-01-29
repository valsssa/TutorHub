# Log Analysis Runbook

## Quick Reference

| Operation | Command |
|-----------|---------|
| All logs | `docker compose logs -f` |
| Backend logs | `docker compose logs -f backend` |
| Frontend logs | `docker compose logs -f frontend` |
| Database logs | `docker compose logs -f db` |
| Last 100 lines | `docker compose logs --tail=100 backend` |

---

## Viewing Logs

### Real-Time Logs (Follow Mode)

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Multiple services
docker compose logs -f backend frontend
```

### Historical Logs

```bash
# Last N lines
docker compose logs --tail=100 backend

# Since specific time
docker compose logs --since="2026-01-29T10:00:00" backend

# Last hour
docker compose logs --since="1h" backend
```

### Filter Logs

```bash
# Filter for errors
docker compose logs backend | grep -i error

# Filter for specific user
docker compose logs backend | grep "user_id=123"

# Filter for specific endpoint
docker compose logs backend | grep "POST /api/bookings"

# Exclude noise
docker compose logs backend | grep -v "Health check"
```

---

## Log Levels

The backend uses structured logging with these levels:

| Level | Description | Example |
|-------|-------------|---------|
| DEBUG | Detailed debugging | Query results |
| INFO | Normal operations | "Booking created" |
| WARNING | Potential issues | "Rate limit approaching" |
| ERROR | Errors that were handled | "Payment failed" |
| CRITICAL | Unrecoverable errors | "Database connection lost" |

### Set Log Level

```bash
# In .env or docker-compose.yml
LOG_LEVEL=DEBUG  # More verbose
LOG_LEVEL=INFO   # Normal (default)
LOG_LEVEL=WARNING # Less verbose
```

---

## Common Log Patterns

### Successful Request

```
2026-01-29 10:30:00,123 - uvicorn.access - INFO - 127.0.0.1:54321 - "POST /api/bookings HTTP/1.1" 201
```

### Error Pattern

```
2026-01-29 10:30:00,123 - backend.modules.bookings - ERROR - [main.py:123] - Booking failed: insufficient credits
```

### Exception with Traceback

```
2026-01-29 10:30:00,123 - backend.modules.payments - ERROR - Payment processing failed
Traceback (most recent call last):
  File "/app/modules/payments/service.py", line 45, in process_payment
    ...
stripe.error.CardError: Your card was declined.
```

---

## Debugging Specific Issues

### Authentication Issues

```bash
# Look for auth-related logs
docker compose logs backend | grep -E "(auth|login|token|401|403)"
```

### Payment Issues

```bash
# Look for Stripe-related logs
docker compose logs backend | grep -i stripe

# Look for payment errors
docker compose logs backend | grep -E "(payment|checkout|refund)"
```

### Booking Issues

```bash
# Look for booking-related logs
docker compose logs backend | grep -i booking

# Look for state machine transitions
docker compose logs backend | grep -E "(state|transition)"
```

### Database Issues

```bash
# PostgreSQL logs
docker compose logs db

# Look for slow queries
docker compose logs db | grep "duration"

# Look for connection issues
docker compose logs db | grep -E "(connection|pool)"
```

### Email Issues

```bash
# Look for email/Brevo logs
docker compose logs backend | grep -i "email\|brevo\|notification"
```

---

## Log Aggregation (Future)

For production, consider:

1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
2. **CloudWatch Logs** (AWS)
3. **Stackdriver** (GCP)
4. **Datadog**

### Docker Log Driver

To send logs to external service:

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Log Retention

Current setup:
- Docker keeps logs until container is removed
- No automatic rotation by default

### Enable Log Rotation

Add to docker-compose.yml:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"    # Max file size
        max-file: "5"       # Max number of files
```

### Manual Log Cleanup

```bash
# Clear logs for specific container
truncate -s 0 $(docker inspect --format='{{.LogPath}}' edustream-backend-1)
```

---

## Exporting Logs

### Export to File

```bash
# Export last 24 hours
docker compose logs --since="24h" backend > backend_logs_$(date +%Y%m%d).log

# Export all logs
docker compose logs backend > backend_all_logs.log
```

### Export for Support

When reporting issues, include:

```bash
# Create log bundle
mkdir -p logs_$(date +%Y%m%d)
docker compose logs --tail=1000 backend > logs_$(date +%Y%m%d)/backend.log
docker compose logs --tail=1000 frontend > logs_$(date +%Y%m%d)/frontend.log
docker compose logs --tail=1000 db > logs_$(date +%Y%m%d)/db.log
docker compose ps > logs_$(date +%Y%m%d)/services.txt
tar -czvf logs_$(date +%Y%m%d).tar.gz logs_$(date +%Y%m%d)/
```

---

## Sentry Integration

For errors, also check Sentry:

1. Visit https://sentry.io/organizations/YOUR_ORG/issues/
2. Filter by environment (production/staging)
3. Filter by time range
4. Look for error patterns and stack traces

Sentry provides:
- Error grouping
- Stack traces
- User context
- Breadcrumbs (recent events before error)
