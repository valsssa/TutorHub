# System Architecture Overview

## 1. High-Level Topology

```
+-----------------------------------------------------------------------------------+
|                              CLIENT LAYER                                          |
+-----------------------------------------------------------------------------------+
|  Browser (Next.js SSR/CSR)    |    Future: Mobile Apps (React Native/Flutter)     |
+----------------+--------------+------------------+--------------------------------+
                 | HTTPS                           | WSS
                 v                                 v
+-----------------------------------------------------------------------------------+
|                           GATEWAY / EDGE LAYER                                     |
+-----------------------------------------------------------------------------------+
|  Nginx / Cloud Load Balancer (TLS termination, rate limiting, routing)            |
+----------------+--------------+------------------+--------------------------------+
                 |                                 |
                 v                                 v
+-------------------------------+    +----------------------------------------------+
|    API SERVER (FastAPI)       |    |        WEBSOCKET SERVER (FastAPI)            |
|  - REST endpoints             |    |  - Real-time messaging                       |
|  - Authentication (JWT)       |    |  - Typing indicators                         |
|  - Business logic             |    |  - Presence tracking                         |
|  - Rate limiting              |    |  - Availability broadcasts                   |
+--------------+----------------+    +---------------------+------------------------+
               |                                           |
               v                                           |
+-----------------------------------------------------------------------------------+
|                            SERVICE LAYER                                           |
+-----------------------------------------------------------------------------------+
|  BookingService | TutorProfileService | PaymentService | NotificationService      |
|  MessageService | PackageService      | ReviewService  | AdminService             |
+-------+----------------+----------------+----------------+------------------------+
        |                |                |                |
        v                v                v                v
+---------------+  +-----------+  +-----------+  +------------------------------+
| PostgreSQL 17 |  |  Redis 7  |  |   MinIO   |  |    External Services         |
| - 45+ tables  |  |  - Cache  |  |  - Files  |  |  - Stripe (payments)         |
| - Connection  |  |  - Queue  |  |  - Photos |  |  - Brevo (email)             |
|   pool (30)   |  |  - Pub/Sub|  |  - Docs   |  |  - Google OAuth              |
+---------------+  +-----------+  +-----------+  |  - Zoom (video)              |
        |                                        +------------------------------+
        v
+-----------------------------------------------------------------------------------+
|                        BACKGROUND JOB LAYER                                        |
+-----------------------------------------------------------------------------------+
|  APScheduler (in-process)                                                          |
|  - expire_requests (every 5 min): REQUESTED -> EXPIRED after 24h                   |
|  - start_sessions (every 1 min): SCHEDULED -> ACTIVE at start_time                 |
|  - end_sessions (every 1 min): ACTIVE -> ENDED after end_time + grace              |
+-----------------------------------------------------------------------------------+
```

## 2. Architecture Style Decision

### Decision: Modular Monolith with DDD Patterns

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Traditional Monolith | Simple deployment | Tangled dependencies | Rejected |
| **Modular Monolith** | Module isolation, shared infra | Requires discipline | **Selected** |
| Microservices | Independent scaling | Operational overhead | Premature |

### Justification

1. **Team Size**: Small team (< 5 engineers) cannot support microservices ops overhead
2. **Product Stage**: MVP phase requires rapid iteration over distributed complexity
3. **Future Optionality**: Modular structure enables future service extraction
4. **Operational Simplicity**: Single deployment unit, shared database

### Module Extraction Candidates (When Scale Justifies)

| Module | Extraction Trigger | Complexity |
|--------|-------------------|------------|
| Payments | Compliance requirements, team specialization | Medium |
| Notifications | High volume, can be eventually consistent | Low |
| Messaging | Real-time scaling needs, different SLAs | Medium |

## 3. Component Inventory

### Backend Services

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Server | FastAPI (Python 3.12) | REST API, authentication, business logic |
| WebSocket Server | FastAPI (Starlette) | Real-time messaging, presence |
| Job Scheduler | APScheduler | Booking state transitions |

### Data Stores

| Store | Technology | Purpose |
|-------|------------|---------|
| Primary Database | PostgreSQL 17 | Transactional data, 45+ tables |
| Cache | Redis 7 | Session cache, rate limiting |
| Object Storage | MinIO | Avatars, documents, attachments |

### External Integrations

| Service | Provider | Purpose |
|---------|----------|---------|
| Payments | Stripe Connect | Payment processing, payouts |
| Email | Brevo (SendInBlue) | Transactional email |
| OAuth | Google | Social login |
| Video | Zoom | Video conferencing |
| Calendar | Google Calendar | Schedule sync |

## 4. Deployment Model

### Current: Single-Region Docker Compose

```
Single VM (8 CPU, 32GB RAM recommended)
+-- docker-compose.yml
    +-- db (PostgreSQL 17)
    +-- redis (Redis 7)
    +-- minio (MinIO)
    +-- backend (FastAPI + Gunicorn)
    +-- frontend (Next.js)
```

### Production Recommendation

#### Phase 1: MVP Launch (Current)

- Single VM with Docker Compose
- Nginx reverse proxy with TLS
- Daily database backups
- Basic monitoring (logs, uptime)

#### Phase 2: Growth (1K+ Users)

- Managed Kubernetes (GKE/EKS)
- Managed PostgreSQL (Cloud SQL/RDS)
- Redis Cluster
- CDN for static assets
- Horizontal pod autoscaling

#### Phase 3: Scale (10K+ Users)

- Multi-region deployment
- PostgreSQL read replicas
- Global CDN
- Event-driven architecture
- Dedicated job queue (Celery)

## 5. Network Architecture

### Current Network Flow

```
Internet
    |
    v
+-------------------+
| Nginx (TLS/Proxy) |
+-------------------+
    |
    +---> :3000 (Frontend - Next.js)
    |
    +---> :8000 (Backend - FastAPI)
           |
           +---> :5432 (PostgreSQL)
           +---> :6379 (Redis)
           +---> :9000 (MinIO)
```

### Port Assignments

| Port | Service | Protocol |
|------|---------|----------|
| 443 | Nginx (public) | HTTPS |
| 3000 | Frontend | HTTP (internal) |
| 8000 | Backend | HTTP (internal) |
| 5432 | PostgreSQL | TCP (internal) |
| 6379 | Redis | TCP (internal) |
| 9000 | MinIO API | HTTP (internal) |
| 9001 | MinIO Console | HTTP (internal) |

## 6. Configuration Management

### Environment Variables

Configuration is managed through environment variables with sensible defaults:

```yaml
# Core Settings
SECRET_KEY: required, 32+ chars
DATABASE_URL: postgresql://...
ENVIRONMENT: development|staging|production

# Rate Limiting
RATE_LIMIT_PER_MINUTE: 60
REGISTRATION_RATE_LIMIT: 5/minute
LOGIN_RATE_LIMIT: 10/minute

# External Services
STRIPE_SECRET_KEY: sk_...
BREVO_API_KEY: xkeysib-...
GOOGLE_CLIENT_ID: ...
ZOOM_CLIENT_ID: ...
```

### Configuration Hierarchy

1. Environment variables (highest priority)
2. Docker Compose environment
3. Application defaults (lowest priority)

## 7. Health Checks

### Application Health Endpoints

| Endpoint | Purpose | Check Interval |
|----------|---------|----------------|
| `GET /health` | Basic liveness | 10s |
| `GET /api/health/integrity` | Database connectivity | 30s |

### Container Health Checks

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]  # PostgreSQL
  test: ["CMD", "redis-cli", "ping"]              # Redis
  interval: 10s
  timeout: 5s
  retries: 5
```

## 8. Resource Requirements

### Development

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 20 GB |

### Production (MVP)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Disk | 50 GB SSD | 100 GB SSD |

### Production (Scale)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| API Pods | 2 | 4-10 (autoscale) |
| DB RAM | 8 GB | 16+ GB |
| DB Storage | 100 GB | 500 GB SSD |
