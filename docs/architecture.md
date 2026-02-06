# Architecture

## System Overview

EduStream is a student-tutor booking platform with the following components:

- **Backend**: FastAPI (Python 3.12) with SQLAlchemy ORM
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL 17
- **Cache/Queue**: Redis 7
- **Object Storage**: MinIO (S3-compatible)
- **Job Scheduler**: APScheduler

## Data Flow

1. Frontend authenticates via JWT tokens stored in cookies
2. API requests go through rate limiting and authentication middleware
3. Business logic is handled by module services
4. Database access via SQLAlchemy with connection pooling
5. Background jobs handle scheduled tasks (booking expirations, notifications)

## Module Architecture

See `backend/modules/README.md` for detailed module patterns.

## Key Integrations

- **Stripe**: Payment processing
- **Google OAuth**: Social login
- **Google Calendar**: Calendar sync
- **Zoom**: Video conferencing
- **Brevo**: Transactional email

## Observability

### Distributed Tracing (OpenTelemetry)

EduStream supports distributed tracing via OpenTelemetry for debugging and performance monitoring.

**Configuration:**

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `TRACING_ENABLED` | Enable/disable tracing | `false` |
| `TRACING_EXPORTER` | Exporter type: `jaeger`, `otlp`, or `console` | `console` |
| `TRACING_SERVICE_NAME` | Service name in traces | `edustream-api` |
| `TRACING_SAMPLE_RATE` | Sampling rate (0.0-1.0) | `1.0` (dev), `0.1` (prod) |
| `JAEGER_AGENT_HOST` | Jaeger agent hostname | `localhost` |
| `JAEGER_AGENT_PORT` | Jaeger agent port | `6831` |
| `OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |

**Features:**
- Automatic FastAPI request tracing
- SQLAlchemy database query tracing
- External API call tracing (Stripe, Brevo, Zoom, Google Calendar)
- Background job tracing
- Log correlation with trace IDs
- W3C Trace Context propagation

**Enabling Jaeger:**

1. Uncomment the Jaeger service in `docker-compose.yml`
2. Set environment variables:
   ```bash
   TRACING_ENABLED=true
   TRACING_EXPORTER=otlp
   ```
3. Access Jaeger UI at http://localhost:16686

### Error Monitoring (Sentry)

Error tracking via Sentry SDK. Configure with `SENTRY_DSN` environment variable.
