# Scalability & Operations

## 1. Current Bottleneck Analysis

| Component | Current Limit | Symptoms | Mitigation |
|-----------|--------------|----------|------------|
| Database Connections | 30 total | Connection pool exhaustion | Managed PostgreSQL |
| API Server | Single process | CPU-bound queries | Multiple workers |
| Background Jobs | In-process | Jobs block requests | Celery migration |
| File Storage | Single MinIO | I/O bottleneck | CDN + S3 |
| WebSocket | Single server | Memory per connection | Redis pub/sub |

## 2. Scaling Strategy

### Phase 1: Vertical Scaling (MVP, 1-1,000 users)

```
Single VM (8 CPU, 32GB RAM)
+-- PostgreSQL (4GB RAM)
+-- Redis (1GB RAM)
+-- Backend (8 workers, 16GB RAM)
+-- Frontend (static, CDN)
+-- MinIO (local storage)
```

**Cost**: ~$100-200/month on major cloud providers

### Phase 2: Horizontal Scaling (1,000-10,000 users)

```
Load Balancer
+-- Backend Pod 1..N (auto-scale 2-10)
+-- Worker Pod 1..M (Celery)
|
+-- PostgreSQL Primary
|   +-- Read Replica 1
|   +-- Read Replica 2
|
+-- Redis Cluster (3 nodes)
|
+-- S3/CloudStorage
|
+-- CDN (Cloudflare)
```

**Cost**: ~$500-1,500/month

### Phase 3: Multi-Region (10,000+ users)

```
Global Load Balancer (Anycast)
+-- Region A (US-East)
|   +-- Backend pods
|   +-- PostgreSQL Primary
|   +-- Redis
|
+-- Region B (EU-West)
|   +-- Backend pods
|   +-- PostgreSQL Replica
|   +-- Redis (follower)
|
+-- CDN Edge (global)
```

**Cost**: ~$3,000-10,000/month

## 3. Caching Strategy

### Cache Layers

| Layer | Technology | TTL | Use Case |
|-------|------------|-----|----------|
| Browser | HTTP Cache | 1 year | Static assets |
| CDN | Cloudflare | 5 min | Public pages |
| API | In-memory LRU | 2 min | API responses |
| Database | Redis | 5-10 min | Query results |
| Session | Redis | 30 min | JWT validation |

### Implementation

```python
# Frontend API cache (lib/api.ts)
const cache = new Map<string, CacheEntry>();
const DEFAULT_TTL = 2 * 60 * 1000;  // 2 minutes

// Cache configuration by endpoint
const TTL_CONFIG = {
  'subjects': 10 * 60 * 1000,     // Static data
  'tutors/list': 60 * 1000,       // Frequently updated
  'bookings': 30 * 1000,          // Real-time critical
  'user/current': 10 * 60 * 1000, // Rarely changes
};
```

### Cache Invalidation

```python
# Pattern-based invalidation on mutations
const INVALIDATION_PATTERNS = {
  'POST /bookings': ['bookings/*', 'tutor/bookings/*'],
  'PUT /tutor/profile': ['tutors/*', 'tutor/profile'],
  'POST /reviews': ['reviews/*', 'tutors/*'],
};
```

## 4. Load Patterns

### Expected Traffic

| Time Period | Traffic Level | Notes |
|-------------|---------------|-------|
| 6 AM - 9 AM | Low | Morning prep |
| 9 AM - 4 PM | Medium | School/work hours |
| 4 PM - 10 PM | **Peak** | After school tutoring |
| 10 PM - 6 AM | Low | Overnight |

### Seasonal Patterns

- **Back to school** (Aug-Sep): +50% traffic
- **Exam season** (Nov-Dec, Apr-May): +30% traffic
- **Summer** (Jun-Jul): -20% traffic
- **Holidays**: Variable

### Auto-Scaling Configuration

```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 5. CI/CD Pipeline

### Recommended Pipeline

```
+--------+    +--------+    +--------+    +--------+    +---------+
|  Push  |--->|  Lint  |--->|  Test  |--->| Build  |--->| Deploy  |
|to main |    |        |    |        |    |        |    | Staging |
+--------+    +--------+    +--------+    +--------+    +----+----+
                                                             |
                                                        +----v----+
                                                        | Deploy  |
                                                        |  Prod   |
                                                        |(manual) |
                                                        +---------+
```

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff mypy bandit
      - run: ruff check backend/
      - run: mypy backend/
      - run: bandit -r backend/ -ll

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run type-check

  test-backend:
    needs: lint-backend
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v

  test-frontend:
    needs: lint-frontend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npm ci
      - run: cd frontend && npm test

  build:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: |
          docker build -t backend:${{ github.sha }} backend/
          docker build -t frontend:${{ github.sha }} frontend/

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          # Deploy to staging environment
          kubectl set image deployment/backend backend=backend:${{ github.sha }}
          kubectl set image deployment/frontend frontend=frontend:${{ github.sha }}

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Manual approval required
          kubectl set image deployment/backend backend=backend:${{ github.sha }}
          kubectl set image deployment/frontend frontend=frontend:${{ github.sha }}
```

## 6. Testing Pyramid

```
                      /\
                     /  \
                    / E2E\           5-10 tests
                   / Tests \         Critical user journeys
                  /----------\
                 /  Integration\     50-100 tests
                /    Tests      \    API + DB
               /------------------\
              /    Unit Tests      \  500+ tests
             /   (pytest, Jest)     \ Business logic
            /------------------------\
```

### Test Categories

| Type | Tools | Coverage | Location |
|------|-------|----------|----------|
| Unit | pytest, Jest | Business logic | `tests/unit/` |
| Integration | pytest + testcontainers | API + DB | `tests/integration/` |
| E2E | Playwright | User journeys | `tests/e2e/` |

### Critical Test Scenarios

1. **Booking State Machine**
   - All valid transitions
   - Invalid transition rejection
   - Edge cases (timeout, no-show)

2. **Payment Flow**
   - Authorization
   - Capture
   - Refund (full and partial)

3. **Authentication**
   - Login/logout
   - OAuth flow
   - Token expiry

4. **Tutor Approval**
   - Profile submission
   - Admin review
   - Approval/rejection

## 7. Monitoring & Alerting

### Key Metrics Dashboard

```
+---------------------------+---------------------------+
|     Request Rate          |    Error Rate             |
|   [=========>    ]        |   [=>              ]      |
|   1,234 req/min           |   0.5%                    |
+---------------------------+---------------------------+
|     P95 Latency           |    Active Connections     |
|   [=====>        ]        |   [======>         ]      |
|   145ms                   |   18/30                   |
+---------------------------+---------------------------+
|     CPU Usage             |    Memory Usage           |
|   [========>     ]        |   [==========>    ]       |
|   62%                     |   74%                     |
+---------------------------+---------------------------+
```

### Alert Configuration

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | > 1% | > 5% | Page on-call |
| P95 Latency | > 500ms | > 2s | Investigate |
| CPU | > 70% | > 90% | Scale up |
| Memory | > 80% | > 95% | Investigate leak |
| DB Connections | > 80% | > 95% | Scale pool |
| Disk | > 80% | > 90% | Expand storage |
| Payment Failures | > 2% | > 5% | Urgent review |

### PagerDuty Integration

```yaml
# alertmanager.yml example
receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_KEY>'
        severity: critical

  - name: 'slack-warnings'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK>'
        channel: '#alerts'

route:
  receiver: 'slack-warnings'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
```

## 8. Runbooks

### Common Operations

#### Deploy New Version

```bash
# 1. Run tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# 2. Build new images
docker compose build

# 3. Deploy with zero downtime
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend

# 4. Verify health
curl https://api.example.com/health
```

#### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U postgres -Fc authapp > backup_$(date +%Y%m%d).dump

# Restore backup
docker compose exec -T db pg_restore -U postgres -d authapp < backup_20260129.dump
```

#### Clear Cache

```bash
# Redis cache
docker compose exec redis redis-cli FLUSHDB

# Application restart (clears in-memory cache)
docker compose restart backend
```

#### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# Since specific time
docker compose logs --since="2026-01-29T10:00:00" backend
```

### Incident Response

#### High Error Rate

1. Check logs for error patterns
2. Identify affected endpoints
3. Check database connectivity
4. Check external service status (Stripe, etc.)
5. Rollback if recent deployment

#### Slow Response Times

1. Check database query performance
2. Check connection pool utilization
3. Check CPU/memory usage
4. Check external API latency
5. Enable query logging temporarily

#### Payment Issues

1. Check Stripe dashboard
2. Verify webhook delivery
3. Check payment logs
4. Contact Stripe support if systemic

## 9. Onboarding Checklist

### New Engineer Setup

- [ ] Clone repository
- [ ] Install Docker and Docker Compose
- [ ] Copy `.env.example` to `.env`
- [ ] Run `docker compose up --build`
- [ ] Verify http://localhost:3000 works
- [ ] Run test suite
- [ ] Read CLAUDE.md and architecture docs
- [ ] Review ADRs in docs/architecture/decisions/
- [ ] Shadow a deployment
- [ ] Get access to monitoring dashboards

### Key Documentation

| Document | Purpose |
|----------|---------|
| CLAUDE.md | AI-friendly codebase overview |
| docs/architecture/ | System design details |
| backend/modules/README.md | Module patterns |
| tests/README.md | Testing guide |

## 10. Disaster Recovery

### Backup Schedule

| Type | Frequency | Retention | Storage |
|------|-----------|-----------|---------|
| Database full | Daily | 30 days | Cloud storage |
| Database WAL | Continuous | 7 days | Cloud storage |
| File storage | Daily | 30 days | Cross-region |
| Config/secrets | On change | Forever | Git + vault |

### Recovery Objectives

| Metric | Target | Current |
|--------|--------|---------|
| RTO (Recovery Time) | < 1 hour | ~4 hours |
| RPO (Data Loss) | < 1 hour | ~24 hours |

### DR Procedure

1. Provision new infrastructure
2. Restore database from backup
3. Restore file storage
4. Update DNS
5. Verify functionality
6. Notify users
