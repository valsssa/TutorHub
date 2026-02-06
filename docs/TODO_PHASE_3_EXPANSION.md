# Phase 3: Mobile Apps & International Expansion

**Timeline**: Weeks 27-52 (Months 7-12)
**Goal**: Launch mobile apps, expand internationally, pilot enterprise, achieve $5M GMV run rate
**Dependencies**: Phase 2 complete

---

## Mobile Apps

### 🔴 P0 - Critical

- [ ] **Mobile app technology decision**
  - React Native vs Flutter vs Native
  - Recommendation: React Native (code sharing)
  - Create: `docs/ADR_MOBILE_TECHNOLOGY.md`

- [ ] **Mobile app architecture design**
  - Shared API client
  - Offline capability design
  - Push notification integration
  - Create: `docs/MOBILE_ARCHITECTURE.md`

- [ ] **iOS app development**
  - Core screens (search, profile, booking, messages)
  - Apple Pay integration
  - Push notifications (APNs)
  - Create: `mobile/ios/`

- [ ] **Android app development**
  - Core screens matching iOS
  - Google Pay integration
  - Push notifications (FCM)
  - Create: `mobile/android/`

- [ ] **Mobile push notification infrastructure**
  - Firebase Cloud Messaging setup
  - Apple Push Notification service setup
  - Notification handling
  - Files: `backend/modules/notifications/`, new push module

### 🟠 P1 - High Priority

- [ ] **App Store submission**
  - iOS App Store Connect setup
  - Google Play Console setup
  - App review preparation
  - Marketing materials (screenshots, description)

- [ ] **Mobile-specific features**
  - Quick rebook from notification
  - Calendar integration (native)
  - Share tutor via messaging apps

- [ ] **Mobile analytics**
  - App event tracking
  - Crash reporting (Crashlytics)
  - Performance monitoring

### 🟡 P2 - Medium Priority

- [ ] **Offline mode (basic)**
  - Cache recent messages
  - View upcoming bookings
  - Queue actions for sync

- [ ] **Mobile A/B testing**
  - Feature flag integration
  - Remote config
  - Gradual rollouts

---

## Parent Dashboard (K-12)

### 🔴 P0 - Critical

- [ ] **Parent account type**
  - Parent role in system
  - Child account linking
  - Multi-child support
  - Files: `backend/modules/auth/`, `backend/models/`

- [ ] **Child account creation**
  - Date of birth verification
  - COPPA compliance (parental consent)
  - Age-appropriate UI
  - Files: `backend/modules/auth/`, `frontend/app/`

- [ ] **Booking approval workflow**
  - Child requests booking
  - Parent receives notification
  - Parent approves/declines
  - Files: `backend/modules/bookings/`, new approval flow

- [ ] **Parent dashboard UI**
  - Overview of all children
  - Session history per child
  - Spending summary
  - Create: `frontend/app/parent/`

### 🟠 P1 - High Priority

- [ ] **Spending limits**
  - Monthly limit per child
  - Per-session limit
  - Notification when approaching limit
  - Files: `backend/modules/payments/`

- [ ] **Session notes visibility**
  - Parent can view tutor notes
  - Progress reports
  - Learning goals tracking
  - Files: `frontend/app/parent/`

- [ ] **Parent notifications**
  - Session completed alerts
  - New tutor recommendations
  - Progress milestone alerts
  - Files: `backend/modules/notifications/`

### 🟡 P2 - Medium Priority

- [ ] **Family payment method**
  - Shared payment method
  - Spending attribution
  - Family billing

- [ ] **Report cards**
  - Monthly progress report
  - PDF export
  - Email delivery

---

## International Expansion

### 🔴 P0 - Critical

- [ ] **Multi-region deployment preparation**
  - EU region setup (GDPR compliance)
  - Data residency requirements
  - Latency optimization
  - Update: `kubernetes/`

- [ ] **Localization infrastructure**
  - i18n setup in frontend
  - Translation management (Crowdin/Lokalise)
  - RTL support preparation
  - Files: `frontend/lib/i18n.ts`

- [ ] **UK/AU launch**
  - Local payment methods
  - Local tutor recruitment
  - Time zone handling verification
  - Marketing localization

- [ ] **India launch**
  - INR currency support
  - Local payment integration (Razorpay)
  - Recruitment in key cities
  - Pricing strategy for market

### 🟠 P1 - High Priority

- [ ] **Spanish language support**
  - UI translations
  - Email templates
  - Help content
  - Files: `frontend/locales/es/`

- [ ] **French language support**
  - UI translations
  - Email templates
  - Files: `frontend/locales/fr/`

- [ ] **GDPR compliance enhancements**
  - Data export endpoint
  - Deletion request flow
  - Consent management
  - Cookie consent update
  - Files: `backend/modules/gdpr/`

### 🟡 P2 - Medium Priority

- [ ] **German language support**
  - UI translations
  - Files: `frontend/locales/de/`

- [ ] **Regional tutor verification**
  - Country-specific background checks
  - Document verification by region
  - Create: `backend/modules/verification/regional/`

---

## Enterprise Features

### 🔴 P0 - Critical

- [ ] **Enterprise admin portal**
  - Bulk user management
  - Department organization
  - Budget allocation
  - Create: `frontend/app/enterprise/`

- [ ] **SSO integration (SAML/OIDC)**
  - SAML 2.0 support
  - OIDC support
  - User provisioning
  - Create: `backend/modules/auth/sso/`

- [ ] **Enterprise billing**
  - Invoice-based billing
  - Purchase order support
  - Custom payment terms
  - Files: `backend/modules/payments/`

### 🟠 P1 - High Priority

- [ ] **Reporting dashboard**
  - Usage reports
  - Spend reports
  - Department breakdown
  - PDF/CSV export
  - Files: `frontend/app/enterprise/`

- [ ] **Custom tutor pools**
  - Pre-approved tutors for org
  - Exclusive tutor contracts
  - Custom pricing
  - Files: `backend/modules/enterprise/`

- [ ] **LTI integration**
  - LMS integration (Canvas, Blackboard)
  - Single sign-on from LMS
  - Grade passback
  - Create: `backend/modules/integrations/lti/`

### 🟡 P2 - Medium Priority

- [ ] **White-label preparation**
  - Theming system
  - Custom domain support
  - Logo/branding customization

- [ ] **API access for enterprise**
  - Enterprise API keys
  - Higher rate limits
  - Dedicated support

---

## Advanced Analytics

### 🔴 P0 - Critical

- [ ] **Data warehouse setup**
  - Snowflake/BigQuery setup
  - ETL pipeline (Fivetran/Airbyte)
  - Data modeling (dbt)
  - Create: `analytics/`

- [ ] **Advanced BI dashboards**
  - Executive dashboard
  - Operations dashboard
  - Finance dashboard
  - Tool: Looker/Metabase

### 🟠 P1 - High Priority

- [ ] **Cohort analysis automation**
  - Weekly cohort reports
  - Retention curves
  - LTV projections
  - Files: `analytics/models/`

- [ ] **A/B testing platform**
  - Experiment management
  - Statistical analysis
  - Results dashboard
  - Files: `backend/core/experiments.py`

### 🟡 P2 - Medium Priority

- [ ] **ML-powered insights**
  - Churn prediction
  - Tutor success prediction
  - Demand forecasting

---

## Platform Reliability

### 🔴 P0 - Critical

- [ ] **99.9% uptime target**
  - Multi-AZ deployment
  - Automated failover
  - Chaos engineering tests
  - Update: `kubernetes/`

- [ ] **Disaster recovery**
  - Cross-region backups
  - Recovery runbooks
  - Regular DR drills
  - RTO: <1 hour, RPO: <15 minutes

### 🟠 P1 - High Priority

- [ ] **Performance optimization**
  - P95 latency <200ms
  - Database query optimization
  - Caching improvements
  - Files: Various

- [ ] **Security hardening**
  - Penetration testing
  - Security audit
  - Bug bounty program
  - Create: `SECURITY.md`

### 🟡 P2 - Medium Priority

- [ ] **Cost optimization**
  - Right-sizing resources
  - Reserved instances
  - Spot instances for batch jobs

---

## Definition of Done (Phase 3)

- [ ] iOS app launched (10K downloads)
- [ ] Android app launched (10K downloads)
- [ ] Parent dashboard live
- [ ] Available in 5 countries (US, UK, AU, CA, IN)
- [ ] 3 enterprise contracts signed
- [ ] 2 languages supported (EN, ES)
- [ ] $5M GMV run rate
- [ ] 99.9% uptime achieved
- [ ] Mobile apps: 4.5+ star rating

---

## New Files to Create

| File | Purpose |
|------|---------|
| `docs/ADR_MOBILE_TECHNOLOGY.md` | Mobile tech decision |
| `docs/MOBILE_ARCHITECTURE.md` | Mobile app architecture |
| `mobile/` | Mobile app codebase |
| `frontend/app/parent/` | Parent dashboard |
| `frontend/lib/i18n.ts` | Internationalization |
| `frontend/locales/` | Translation files |
| `backend/modules/gdpr/` | GDPR compliance |
| `backend/modules/auth/sso/` | SSO integration |
| `frontend/app/enterprise/` | Enterprise portal |
| `backend/modules/enterprise/` | Enterprise features |
| `backend/modules/integrations/lti/` | LMS integration |
| `analytics/` | Data warehouse models |
| `backend/core/experiments.py` | A/B testing |
| `SECURITY.md` | Security policy |

---

## Related Architecture Docs

- [System Overview](./architecture/02-system-overview.md) - Phase 3 multi-region
- [Future Evolution](./architecture/09-future-evolution.md) - Mobile apps, enterprise
- [Security & Reliability](./architecture/07-security-reliability.md) - GDPR compliance
