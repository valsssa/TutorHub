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
