# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- Booking state machine with four-field status system
- APScheduler integration for background jobs
- Owner dashboard with revenue analytics
- Feature flags system with Redis backend (`backend/core/feature_flags.py`)
- Feature flags admin API (`backend/modules/admin/feature_flags_router.py`)
- Frontend feature flags client with React hooks (`frontend/lib/featureFlags.ts`)
- Load testing suite with Locust (`tests/load/`)
- Success metrics documentation (`docs/METRICS.md`)
- On-call procedures (`docs/ON_CALL.md`)
- Support processes documentation (`docs/SUPPORT.md`)
- Engineer onboarding guide (`docs/ONBOARDING.md`)
- Security audit report (`docs/SECURITY_AUDIT.md`)
- Distributed tracing with OpenTelemetry (`backend/core/tracing.py`, `backend/core/tracing_middleware.py`)
- Refresh token support for authentication (`backend/modules/auth/presentation/api.py`)
- WebSocket stability improvements (reconnection, message queue, ack system)
- Backend test coverage expansion (payments, auth, tutor approval, packages)

### Changed
- Standardized currency fields across tables
- Renamed 'metadata' to 'extra_data' in Notification model

### Fixed
- Booking tests updated for new status system

---

## [0.9.0] - 2026-01-29

### Added

#### Error Monitoring
- Sentry integration for backend (`backend/core/sentry.py`)
- Sentry integration for frontend (`frontend/sentry.*.config.ts`)
- Error filtering for expected HTTP errors (401, 403, 404, 422)
- Automatic error capture with context (user, transaction)

#### API Versioning
- All endpoints now use `/api/v1` prefix
- Centralized versioning in `main.py`
- Updated OpenAPI documentation with versioned servers
- Frontend updated to use versioned endpoints

#### Operational Documentation
- Launch checklist (`docs/LAUNCH_CHECKLIST.md`)
- Runbook index (`docs/runbooks/README.md`)
- Database operations runbook (`docs/runbooks/database.md`)
- Deployment procedures runbook (`docs/runbooks/deployment.md`)
- Incident response playbook (`docs/runbooks/incident-response.md`)
- Cache management runbook (`docs/runbooks/cache.md`)
- Log analysis runbook (`docs/runbooks/logs.md`)

#### Testing
- Comprehensive booking state machine tests (700+ lines)
- Payment state transition tests
- Dispute state transition tests
- Session lifecycle tests
- Cancel booking edge case tests

### Changed

#### Backend
- All module routers updated to remove `/api/` prefix
- Routers now use centralized `API_V1_PREFIX` in main.py
- Legacy avatar route updated to `/api/v1/avatars/`
- Health integrity endpoint updated to `/api/v1/health/integrity`

#### Frontend
- `lib/api.ts` - All API paths updated to `/api/v1/`
- `lib/api/auth.ts` - Auth API paths updated
- `components/TimeSlotPicker.tsx` - API path updated
- `components/TutorProfileView.tsx` - API path updated
- `components/ModernBookingModal.tsx` - API path updated
- E2E and integration tests updated

#### Documentation
- `CLAUDE.md` updated with API versioning guidelines
- `modules/README.md` updated with versioning pattern
- `project_status.md` updated with progress
- Technical debt register updated

### Dependencies
- Added `sentry-sdk[fastapi]==1.40.0` to backend
- Added `@sentry/nextjs` to frontend

---

## [0.8.0] - 2026-01-28

### Added
- User role management system with admin controls
- Student notes feature for tutors
- Enhanced booking state machine with dispute handling

### Changed
- Improved booking tests for new status system
- Updated notification model metadata field

---

## [0.7.0] - 2026-01-27

### Added
- Owner role with business analytics dashboard
- Commission tier system (20%/15%/10%)
- Performance indexes for database optimization

### Changed
- Standardized currency fields across all tables
- Enhanced tutor search with full-text search

---

## [0.6.0] - 2026-01-26

### Added
- Booking status redesign with four-field system
- Package consistency checks
- Tutor search improvements

---

## [0.5.0] - 2026-01-25

### Added
- Stripe Connect integration for tutor payouts
- Wallet system for student credits
- Package expiration service

---

## [0.4.0] - 2026-01-24

### Added
- Real-time messaging with WebSocket
- File attachments for messages
- Message search functionality

---

## [0.3.0] - 2026-01-23

### Added
- Google Calendar integration
- Zoom meeting creation for bookings
- Tutor availability management

---

## [0.2.0] - 2026-01-22

### Added
- Tutor profile management
- Subject and pricing configuration
- Review and rating system

---

## [0.1.0] - 2026-01-21

### Added
- Initial MVP release
- JWT authentication with Google OAuth
- Role-based access control (admin, tutor, student)
- Basic booking system
- Stripe payment integration
- Notification system with Brevo email
