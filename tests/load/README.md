# Load Testing Suite

Load testing for EduStream using [Locust](https://locust.io/).

## Quick Start

### Install Locust

```bash
pip install locust
```

### Run Tests

**With Web UI:**
```bash
cd tests/load
locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

**Headless (CI/CD):**
```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m \
  --csv=results/load_test
```

### Docker Compose

```bash
docker compose -f docker-compose.load-test.yml up
```

## Test Configuration

### Target Metrics

| Metric | Target |
|--------|--------|
| Concurrent Users | 100 |
| P95 Response Time | <500ms |
| Error Rate | <1% |
| Requests/sec | >50 |

### User Behavior Weights

| User Type | Weight | Description |
|-----------|--------|-------------|
| EduStreamUser | Default | Unauthenticated browsing |
| StudentUser | 3x | Student actions |
| TutorUser | 1x | Tutor actions |

### Task Distribution

**EduStreamUser (anonymous):**
- Health check: 10 (baseline)
- Browse tutors: 5
- Search tutors: 3
- View tutor profile: 2
- View subjects: 2
- View reviews: 1

**StudentUser:**
- Browse tutors: 5
- View my bookings: 3
- View wallet: 2
- View packages: 2
- View notifications: 1

**TutorUser:**
- View my bookings: 5
- View availability: 3
- View earnings: 2
- View my reviews: 1

## Test Scenarios

### Scenario 1: Normal Load (100 users)

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --headless -u 100 -r 10 -t 5m
```

### Scenario 2: Peak Load (250 users)

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --headless -u 250 -r 25 -t 10m
```

### Scenario 3: Stress Test (500 users)

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --headless -u 500 -r 50 -t 10m
```

### Scenario 4: Soak Test (8 hours)

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --headless -u 50 -r 5 -t 8h
```

## Output Files

When using `--csv=results/load_test`, Locust generates:

- `load_test_stats.csv` - Request statistics
- `load_test_failures.csv` - Failure details
- `load_test_stats_history.csv` - Time-series data
- `load_test_exceptions.csv` - Exception details

## Interpreting Results

### Success Criteria

✅ **PASS** if:
- P95 response time < 500ms
- Error rate < 1%
- No 5xx errors under normal load

❌ **FAIL** if:
- P95 response time > 500ms
- Error rate > 1%
- Database connection pool exhaustion
- Memory leaks detected

### Common Issues

| Symptom | Possible Cause | Solution |
|---------|----------------|----------|
| High latency | Database queries | Add indexes, optimize queries |
| Connection errors | Pool exhaustion | Increase pool size |
| 5xx errors | Application errors | Check logs, fix bugs |
| Timeouts | Blocking operations | Add async, increase timeout |

## Distributed Testing

### Master Mode

```bash
locust -f locustfile.py --master
```

### Worker Mode

```bash
locust -f locustfile.py --worker --master-host=<master-ip>
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Load Tests
  run: |
    pip install locust
    locust -f tests/load/locustfile.py \
      --host=${{ secrets.TEST_HOST }} \
      --headless \
      -u 100 -r 10 -t 5m \
      --csv=results/load_test \
      --exit-code-on-error 1
```

### Exit Codes

- `0` - Test completed successfully
- `1` - Test had failures (with `--exit-code-on-error 1`)

## Performance Baseline

Record baseline after each major release:

| Version | Users | P50 | P95 | P99 | RPS | Error % |
|---------|-------|-----|-----|-----|-----|---------|
| 0.9.0 | 100 | TBD | TBD | TBD | TBD | TBD |

## Related Documentation

- [Metrics](../../docs/METRICS.md) - Success metrics
- [Project Status](../../docs/project_status.md) - Current progress
- [Runbooks](../../docs/runbooks/) - Operational procedures
