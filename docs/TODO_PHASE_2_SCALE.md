# Phase 2: V1 Scale & AI Matching

**Timeline**: Weeks 13-26
**Goal**: Scale to 5000 tutors, 20000 students, launch AI matching, achieve $500K GMV
**Dependencies**: Phase 1 complete

---

## AI Tutor Matching (Primary Differentiator)

### 🔴 P0 - Critical

- [ ] **Design AI matching architecture**
  - Feature engineering specification
  - Model selection (LightGBM initial)
  - Serving infrastructure design
  - Create: `docs/AI_MATCHING_DESIGN.md`
  - Related: `docs/PRODUCT_VISION_AND_PLAN.md` Section 12.2

- [ ] **Build feature store**
  - Student features: subjects, price sensitivity, timezone, history
  - Tutor features: subjects, price, rating, response time, completion rate
  - Cross features: subject match, price fit, availability overlap
  - Files: New `backend/modules/matching/`

- [ ] **Implement data pipeline**
  - Historical booking data extraction
  - Feature computation
  - Label: session completed with rating >= 4
  - Training data preparation

- [ ] **Train initial model**
  - LightGBM model training
  - Offline evaluation (AUC, precision, recall)
  - Target: 20% lift over baseline
  - Create: `ml/models/`

- [ ] **Build recommendation API**
  - `GET /api/recommendations?user_id=X&subject=Y`
  - <500ms latency requirement
  - Caching layer (5-min TTL)
  - Files: `backend/modules/matching/api.py`

### 🟠 P1 - High Priority

- [ ] **Implement recommendation UI**
  - "Recommended for you" carousel
  - Match score display (0-100)
  - Match reasons explanation
  - Files: `frontend/app/tutors/`, new components

- [ ] **Build feedback mechanism**
  - "Not interested" button
  - Track clicks on recommendations
  - A/B test framework integration
  - Files: `frontend/components/`, `backend/modules/matching/`

- [ ] **Implement fallback to rule-based**
  - When ML unavailable
  - Cold start for new users
  - Subject + price + rating sorting
  - Files: `backend/modules/matching/`

### 🟡 P2 - Medium Priority

- [ ] **Model monitoring**
  - Prediction distribution tracking
  - Click-through rate monitoring
  - Model drift detection
  - Dashboard: Grafana

- [ ] **Weekly model retraining**
  - Automated pipeline
  - A/B test new vs old model
  - Gradual rollout

---

## Infrastructure Scaling

### 🔴 P0 - Critical

- [ ] **Migrate to Kubernetes**
  - Kubernetes cluster setup (GKE/EKS)
  - Helm charts for all services
  - Horizontal Pod Autoscaler
  - Create: `kubernetes/`

- [ ] **Set up managed PostgreSQL**
  - Cloud SQL/RDS migration
  - Automated backups
  - Point-in-time recovery
  - Connection pooling (PgBouncer)

- [ ] **Add PostgreSQL read replicas**
  - Read/write splitting
  - Route read-heavy queries to replica
  - Files: `backend/core/database.py`

- [ ] **Redis cluster setup**
  - Multi-node Redis
  - Failover capability
  - Session persistence

### 🟠 P1 - High Priority

- [ ] **CDN for static assets**
  - Cloudflare/CloudFront setup
  - Cache headers configuration
  - Asset versioning
  - Files: `frontend/next.config.js`

- [ ] **Implement feature flag system**
  - LaunchDarkly or custom (Redis-based)
  - Gradual rollout capability
  - Kill switch for features
  - Create: `backend/core/feature_flags.py`

- [ ] **Load test for 1000 concurrent users**
  - Update load testing scripts
  - Identify new bottlenecks
  - Capacity planning
  - Files: `tests/load/`

### 🟡 P2 - Medium Priority

- [ ] **Implement distributed tracing**
  - OpenTelemetry integration
  - Correlation IDs
  - Jaeger/Tempo setup
  - Files: `backend/core/tracing.py`

- [ ] **Database query optimization**
  - Query analysis
  - Index optimization
  - Connection pool tuning

---

## Product Features

### 🔴 P0 - Critical

- [ ] **Advanced search filters**
  - Filter by certification
  - Filter by experience level
  - Filter by availability window
  - Filter by language
  - Files: `frontend/app/tutors/`, `backend/modules/tutors/`

- [ ] **Tutor verification badges**
  - ID verified badge
  - Education verified badge
  - Background check badge (K-12)
  - Files: `backend/modules/tutor_profile/`, `frontend/components/`

- [ ] **Package system improvements**
  - Better package comparison UI
  - Package gifting
  - Package transfer between tutors
  - Files: `frontend/app/packages/`, `backend/modules/packages/`

### 🟠 P1 - High Priority

- [ ] **Mobile-responsive optimization**
  - Full responsive audit
  - Touch-friendly interactions
  - Mobile-specific optimizations
  - Files: `frontend/components/`

- [ ] **Notification preferences enhancements**
  - Channel preferences (email, push, in-app)
  - Notification scheduling
  - Digest mode option
  - Files: `frontend/app/settings/notifications/`

- [ ] **Multi-currency improvements**
  - Currency selector in header
  - Tutor earnings in their currency
  - Exchange rate display
  - Files: `frontend/components/`, `backend/core/currency.py`

### 🟡 P2 - Medium Priority

- [ ] **Progress tracking for students**
  - Learning goals setting
  - Session history with notes
  - Milestone celebrations
  - Files: New progress module

- [ ] **Tutor analytics dashboard**
  - Booking trends
  - Revenue analytics
  - Student retention metrics
  - Files: `frontend/app/tutor/earnings/`

---

## Growth Features

### 🔴 P0 - Critical

- [ ] **Affiliate program**
  - Affiliate signup flow
  - Tracking infrastructure
  - Commission management
  - Create: `backend/modules/affiliates/`

- [ ] **SEO expansion**
  - 50+ subject pages
  - 20+ city pages
  - Long-tail keyword targeting
  - Files: `frontend/app/subjects/`, `frontend/app/locations/`

### 🟠 P1 - High Priority

- [ ] **Social proof widgets**
  - Embeddable review widget
  - "As seen on" badges
  - Partner integration
  - Create: `frontend/app/widgets/`

- [ ] **Student activation improvements**
  - Onboarding quiz
  - Personalized tutor suggestions
  - First booking incentive
  - Files: `frontend/app/dashboard/`

### 🟡 P2 - Medium Priority

- [ ] **Gamification elements**
  - Learning streaks
  - Achievement badges
  - Progress milestones
  - Files: New gamification module

---

## Trust & Safety

### 🔴 P0 - Critical

- [ ] **Background check integration**
  - Checkr API integration
  - K-12 tutor requirement
  - Status display on profile
  - Create: `backend/modules/verification/`

- [ ] **Content moderation**
  - Message scanning (profanity, PII)
  - Profile content review
  - Automated flagging
  - Files: `backend/core/moderation.py`

### 🟠 P1 - High Priority

- [ ] **Enhanced dispute resolution**
  - Evidence collection UI
  - Timeline visualization
  - Resolution templates
  - Files: `frontend/app/admin/`, `backend/modules/bookings/`

- [ ] **Fraud detection**
  - Fake review detection
  - Payment fraud signals
  - Account abuse patterns
  - Files: `backend/core/fraud.py`

### 🟡 P2 - Medium Priority

- [ ] **Session recording (opt-in)**
  - Consent flow
  - Cloud storage integration
  - Playback for disputes
  - Create: `backend/modules/recordings/`

---

## API & Integration Improvements

### 🔴 P0 - Critical

- [ ] **Add API versioning**
  - `/api/v1/` prefix for all endpoints
  - Version negotiation
  - Deprecation headers
  - Files: `backend/main.py`, all routers

- [ ] **Improve webhook reliability**
  - Webhook retry logic
  - Dead letter queue
  - Webhook logging
  - Files: `backend/modules/payments/`

### 🟠 P1 - High Priority

- [ ] **Google Meet integration**
  - Alternative to Zoom
  - User preference setting
  - Files: `backend/modules/integrations/`

- [ ] **Microsoft Teams integration**
  - Enterprise customer need
  - OAuth flow
  - Create: `backend/modules/integrations/teams_router.py`

### 🟡 P2 - Medium Priority

- [ ] **Public API preparation**
  - API key management
  - Rate limiting by tier
  - Documentation (Swagger/Redoc)
  - Create: `docs/API.md`

---

## Definition of Done (Phase 2)

- [ ] 5,000 active tutors
- [ ] 20,000 registered students
- [ ] $500K GMV
- [ ] AI matching used in 30% of bookings
- [ ] 99.5% uptime
- [ ] <500ms API P95 latency
- [ ] Kubernetes deployment live
- [ ] Background checks for K-12 tutors
- [ ] Feature flags system operational
- [ ] Affiliate program launched

---

## New Files to Create

| File | Purpose |
|------|---------|
| `docs/AI_MATCHING_DESIGN.md` | AI matching technical design |
| `backend/modules/matching/` | Matching service module |
| `ml/models/` | ML model artifacts |
| `kubernetes/` | Kubernetes manifests |
| `backend/core/feature_flags.py` | Feature flag system |
| `backend/core/tracing.py` | Distributed tracing |
| `backend/modules/verification/` | Background checks |
| `backend/core/moderation.py` | Content moderation |
| `backend/core/fraud.py` | Fraud detection |
| `backend/modules/affiliates/` | Affiliate program |
| `frontend/app/widgets/` | Embeddable widgets |

---

## Related Architecture Docs

- [System Overview](./architecture/02-system-overview.md) - Phase 2 scaling plan
- [Scalability & Operations](./architecture/08-scalability-operations.md) - Kubernetes migration
- [Future Evolution](./architecture/09-future-evolution.md) - AI matching preparation
