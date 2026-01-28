 EduStream Production Roadmap - Final Version

  Your Complete Configuration

  Business Setup
  ┌────────────────────┬───────────────────────────────────────┐
  │      Setting       │                 Value                 │
  ├────────────────────┼───────────────────────────────────────┤
  │ Business Entity    │ Serbian company                       │
  ├────────────────────┼───────────────────────────────────────┤
  │ Target Markets     │ US + Europe                           │
  ├────────────────────┼───────────────────────────────────────┤
  │ Commission Model   │ Revenue-based tiers (20% → 15% → 10%) │
  ├────────────────────┼───────────────────────────────────────┤
  │ Refund Policy      │ 24-hour auto-refund window            │
  ├────────────────────┼───────────────────────────────────────┤
  │ Tutor Verification │ Document upload triggers review       │
  ├────────────────────┼───────────────────────────────────────┤
  │ Languages          │ English only                          │
  ├────────────────────┼───────────────────────────────────────┤
  │ Support            │ Email + YouTrack integration          │
  └────────────────────┴───────────────────────────────────────┘
  Technical Setup
  ┌────────────┬─────────────────────────────────────────┐
  │  Setting   │                  Value                  │
  ├────────────┼─────────────────────────────────────────┤
  │ Hosting    │ Home server + Cloudflare Tunnel         │
  ├────────────┼─────────────────────────────────────────┤
  │ Domain/CDN │ Cloudflare (DNS + SSL + CDN + Tunnel)   │
  ├────────────┼─────────────────────────────────────────┤
  │ Payments   │ Stripe (need entity resolution)         │
  ├────────────┼─────────────────────────────────────────┤
  │ Payouts    │ Stripe Connect (need entity resolution) │
  ├────────────┼─────────────────────────────────────────┤
  │ Email      │ Brevo (Sendinblue)                      │
  ├────────────┼─────────────────────────────────────────┤
  │ Video      │ Zoom + Google Meet embed                │
  ├────────────┼─────────────────────────────────────────┤
  │ Auth       │ Email/password + Google OIDC            │
  ├────────────┼─────────────────────────────────────────┤
  │ Monitoring │ Standardized logging throughout         │
  ├────────────┼─────────────────────────────────────────┤
  │ Backups    │ Manual scripts                          │
  └────────────┴─────────────────────────────────────────┘
  ---
  ⚠️ Critical Business Decision Required

  Stripe Availability Issue

  Problem: Stripe Connect (marketplace payouts) is not available in Serbia for platform owners. You can accept payments, but cannot run a marketplace with automated tutor payouts.

  Your Options:
  ┌──────────────────────────────────┬──────────────────────────────────────────────────┬────────────────────────────────────────────────┬──────────────────┬───────────┐
  │              Option              │                       Pros                       │                      Cons                      │       Cost       │ Timeline  │
  ├──────────────────────────────────┼──────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────────────┼───────────┤
  │ Estonia e-Residency + EU company │ Full Stripe access, EU credibility, GDPR natural │ €190 e-Residency + €200/yr company maintenance │ ~€400 first year │ 2-4 weeks │
  ├──────────────────────────────────┼──────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────────────┼───────────┤
  │ Stripe Atlas (US LLC)            │ Fastest, Stripe handles everything               │ US tax complexity, must file US returns        │ $500 one-time    │ 1-2 weeks │
  ├──────────────────────────────────┼──────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────────────┼───────────┤
  │ Payoneer                         │ Works in Serbia directly                         │ Higher fees (2-3%), less developer-friendly    │ Transaction fees │ Immediate │
  ├──────────────────────────────────┼──────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────────────┼───────────┤
  │ Wise Business + manual           │ Works in Serbia                                  │ Manual payouts, not scalable                   │ €50 setup        │ 1 week    │
  └──────────────────────────────────┴──────────────────────────────────────────────────┴────────────────────────────────────────────────┴──────────────────┴───────────┘
  My Recommendation: Estonia e-Residency + OÜ company if you're serious about EU market. It's the cleanest long-term solution for a Serbian founder targeting US+EU.

  ---
  Implementation Phases

  Phase 0: Business Setup (Parallel Track)

  Week 1-4 (while building):
  ├── Research and decide on business entity for payments
  ├── Apply for e-Residency OR Stripe Atlas OR Payoneer
  ├── Register domain (if not done)
  ├── Set up Cloudflare account
  └── Set up Brevo account

  Phase 1: Security Hardening (Week 1)
  ┌───────────────────────────────────────┬───────────────────────────────┬────────┐
  │                 Task                  │         File/Location         │ Effort │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Remove hardcoded credentials          │ backend/main.py:89            │ 2h     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Generate random defaults on first run │ backend/core/config.py        │ 2h     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Enable HSTS header                    │ backend/core/middleware.py:74 │ 1h     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Add refresh tokens                    │ backend/core/security.py      │ 1d     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Implement token revocation            │ backend/modules/auth/         │ 4h     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Add GDPR cookie consent               │ frontend/components/          │ 1d     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Create Privacy Policy page            │ frontend/app/privacy/         │ 4h     │
  ├───────────────────────────────────────┼───────────────────────────────┼────────┤
  │ Create Terms of Service page          │ frontend/app/terms/           │ 4h     │
  └───────────────────────────────────────┴───────────────────────────────┴────────┘
  Phase 2: Policy Updates (Week 1)
  ┌──────────────────────────────────────────┬──────────────────────────────────────────────┬────────┐
  │                   Task                   │                File/Location                 │ Effort │
  ├──────────────────────────────────────────┼──────────────────────────────────────────────┼────────┤
  │ Change refund window 12h → 24h           │ backend/modules/bookings/policy_engine.py:22 │ 1h     │
  ├──────────────────────────────────────────┼──────────────────────────────────────────────┼────────┤
  │ Implement revenue-based commission tiers │ backend/modules/bookings/service.py          │ 1d     │
  ├──────────────────────────────────────────┼──────────────────────────────────────────────┼────────┤
  │ Add tutor tier tracking                  │ backend/models/tutors.py                     │ 4h     │
  ├──────────────────────────────────────────┼──────────────────────────────────────────────┼────────┤
  │ Update pricing calculation               │ backend/core/currency.py                     │ 4h     │
  └──────────────────────────────────────────┴──────────────────────────────────────────────┴────────┘
  Commission Tier Logic:
  def get_platform_fee_percentage(tutor_total_earnings_cents: int) -> float:
      if tutor_total_earnings_cents < 100000:  # < $1,000
          return 0.20  # 20%
      elif tutor_total_earnings_cents < 500000:  # < $5,000
          return 0.15  # 15%
      else:
          return 0.10  # 10%

  Phase 3: Stripe Integration (Week 2-3)
  ┌─────────────────────────────────────────┬────────┬────────────────────────────────┐
  │                  Task                   │ Effort │             Notes              │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Stripe SDK setup                        │ 2h     │ pip install stripe             │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Create checkout session endpoint        │ 1d     │ POST /api/payments/checkout    │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Handle payment_intent.succeeded webhook │ 4h     │ Update booking status          │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Handle charge.refunded webhook          │ 4h     │ Process refunds                │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Stripe Connect onboarding flow          │ 2d     │ Tutor KYC                      │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Connect account creation                │ 1d     │ Per-tutor Stripe accounts      │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Payout scheduling                       │ 1d     │ Weekly automatic payouts       │
  ├─────────────────────────────────────────┼────────┼────────────────────────────────┤
  │ Commission splitting                    │ 4h     │ Platform fee vs tutor earnings │
  └─────────────────────────────────────────┴────────┴────────────────────────────────┘
  Phase 4: Google OIDC (Week 3)
  ┌────────────────────────────┬────────┬────────────────────────────────────┐
  │            Task            │ Effort │               Notes                │
  ├────────────────────────────┼────────┼────────────────────────────────────┤
  │ Google Cloud Console setup │ 1h     │ Create OAuth credentials           │
  ├────────────────────────────┼────────┼────────────────────────────────────┤
  │ OIDC provider integration  │ 1d     │ Use authlib or python-social-auth  │
  ├────────────────────────────┼────────┼────────────────────────────────────┤
  │ Frontend Google button     │ 4h     │ Sign in with Google                │
  ├────────────────────────────┼────────┼────────────────────────────────────┤
  │ Account linking            │ 4h     │ Connect Google to existing account │
  └────────────────────────────┴────────┴────────────────────────────────────┘
  Phase 5: Brevo Email Integration (Week 4)
  ┌───────────────────────────────┬────────┬──────────────────────────────────────┐
  │             Task              │ Effort │                Notes                 │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Brevo SDK setup               │ 2h     │ pip install sib-api-v3-sdk           │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Email templates in Brevo      │ 1d     │ Booking confirmation, reminder, etc. │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Transactional email service   │ 1d     │ backend/core/email.py                │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Password reset flow           │ 4h     │ Send reset link via email            │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Email verification            │ 4h     │ Verify new accounts                  │
  ├───────────────────────────────┼────────┼──────────────────────────────────────┤
  │ Booking reminder (24h before) │ 4h     │ Scheduled notification               │
  └───────────────────────────────┴────────┴──────────────────────────────────────┘
  Phase 6: Video Integration (Week 4-5)
  ┌──────────────────────────────┬────────┬───────────────────────────────────┐
  │             Task             │ Effort │               Notes               │
  ├──────────────────────────────┼────────┼───────────────────────────────────┤
  │ Zoom OAuth app registration  │ 2h     │ Zoom Marketplace                  │
  ├──────────────────────────────┼────────┼───────────────────────────────────┤
  │ Zoom meeting creation API    │ 1d     │ Auto-generate meeting for booking │
  ├──────────────────────────────┼────────┼───────────────────────────────────┤
  │ Google Calendar API setup    │ 1d     │ Optional: sync to calendar        │
  ├──────────────────────────────┼────────┼───────────────────────────────────┤
  │ In-app meeting launch button │ 4h     │ One-click join                    │
  └──────────────────────────────┴────────┴───────────────────────────────────┘
  Phase 7: Logging Standardization (Week 5)
  ┌──────────────────────────────────┬────────┬─────────────────────────────────────────┐
  │               Task               │ Effort │                  Notes                  │
  ├──────────────────────────────────┼────────┼─────────────────────────────────────────┤
  │ Create structured logging format │ 4h     │ JSON logs with context                  │
  ├──────────────────────────────────┼────────┼─────────────────────────────────────────┤
  │ Add request ID tracking          │ 4h     │ Trace requests across services          │
  ├──────────────────────────────────┼────────┼─────────────────────────────────────────┤
  │ Standardize log levels           │ 4h     │ INFO/WARNING/ERROR consistency          │
  ├──────────────────────────────────┼────────┼─────────────────────────────────────────┤
  │ Add business event logging       │ 1d     │ Booking created, payment received, etc. │
  ├──────────────────────────────────┼────────┼─────────────────────────────────────────┤
  │ Log aggregation setup            │ 4h     │ Loki or file-based with rotation        │
  └──────────────────────────────────┴────────┴─────────────────────────────────────────┘
  Phase 8: Owner Analytics Dashboard (Week 6)
  ┌───────────────────────────┬────────┬───────────────────────────────────┐
  │           Task            │ Effort │               Notes               │
  ├───────────────────────────┼────────┼───────────────────────────────────┤
  │ Add "owner" role          │ 2h     │ Super-admin with financial access │
  ├───────────────────────────┼────────┼───────────────────────────────────┤
  │ Revenue dashboard         │ 1d     │ GMV, platform fees, payouts       │
  ├───────────────────────────┼────────┼───────────────────────────────────┤
  │ Growth metrics            │ 1d     │ New users, bookings, retention    │
  ├───────────────────────────┼────────┼───────────────────────────────────┤
  │ Tutor performance metrics │ 4h     │ Top earners, completion rates     │
  ├───────────────────────────┼────────┼───────────────────────────────────┤
  │ Financial reports         │ 1d     │ Monthly/quarterly summaries       │
  └───────────────────────────┴────────┴───────────────────────────────────┘
  Phase 9: Infrastructure Setup (Week 6-7)
  ┌──────────────────────────────────┬────────┬────────────────────────────┐
  │               Task               │ Effort │           Notes            │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Cloudflare Tunnel setup          │ 2h     │ cloudflared service        │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Docker Compose production config │ 4h     │ Optimize for production    │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Nginx reverse proxy              │ 4h     │ SSL termination, caching   │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ PostgreSQL optimization          │ 4h     │ Connection pooling, tuning │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Backup scripts                   │ 4h     │ Database + file storage    │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Health check endpoints           │ 2h     │ For monitoring             │
  ├──────────────────────────────────┼────────┼────────────────────────────┤
  │ Cron jobs setup                  │ 2h     │ Reminders, cleanup tasks   │
  └──────────────────────────────────┴────────┴────────────────────────────┘
  Phase 10: Testing & QA (Week 7-8)
  ┌────────────────────────┬────────┬───────────────────────────────┐
  │          Task          │ Effort │             Notes             │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Stripe webhook tests   │ 1d     │ Mock webhook events           │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Payment flow E2E tests │ 2d     │ Full checkout → confirmation  │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Refund flow tests      │ 1d     │ 24h policy verification       │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Google OIDC tests      │ 4h     │ Login flow                    │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Email delivery tests   │ 4h     │ Template rendering            │
  ├────────────────────────┼────────┼───────────────────────────────┤
  │ Load testing           │ 1d     │ Verify 1000+ concurrent users │
  └────────────────────────┴────────┴───────────────────────────────┘
  ---
  Estimated Timeline

  Week 1:  Security + Policy updates
  Week 2:  Stripe integration (part 1)
  Week 3:  Stripe integration (part 2) + Google OIDC
  Week 4:  Brevo email + Video integration (start)
  Week 5:  Video integration (complete) + Logging
  Week 6:  Owner dashboard + Infrastructure
  Week 7:  Testing + QA
  Week 8:  Bug fixes + Soft launch
  ─────────────────────────────────────────────
  Total:   8 weeks to production-ready

  ---
  Infrastructure Architecture (Home Server + Cloudflare)

  ┌─────────────────────────────────────────────────────────────┐
  │                     INTERNET                                 │
  └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                  CLOUDFLARE                                  │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
  │  │   DNS    │  │   CDN    │  │  DDoS    │                  │
  │  │          │  │  Cache   │  │ Protect  │                  │
  │  └──────────┘  └──────────┘  └──────────┘                  │
  │                      │                                       │
  │              Cloudflare Tunnel                              │
  └─────────────────────────────────────────────────────────────┘
                            │
                      (encrypted tunnel)
                            │
                            ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                YOUR HOME SERVER                              │
  │                                                              │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │                 cloudflared                           │  │
  │  │            (Tunnel connector)                         │  │
  │  └──────────────────────────────────────────────────────┘  │
  │                          │                                   │
  │                          ▼                                   │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │                Docker Compose                         │  │
  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │  │
  │  │  │ nginx   │  │ backend │  │frontend │  │ postgres│ │  │
  │  │  │ :80/443 │  │  :8000  │  │  :3000  │  │  :5432  │ │  │
  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │  │
  │  │       │                                               │  │
  │  │  ┌─────────┐                                         │  │
  │  │  │  minio  │ (file storage)                          │  │
  │  │  │  :9000  │                                         │  │
  │  │  └─────────┘                                         │  │
  │  └──────────────────────────────────────────────────────┘  │
  │                                                              │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │              Backup Location                          │  │
  │  │         /backups/daily/                               │  │
  │  │         /backups/weekly/                              │  │
  │  └──────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────┘

  ---
  Risk Mitigation for Home Hosting
  ┌──────────────────┬───────────────────────────────────────────────────────────┐
  │       Risk       │                        Mitigation                         │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ Internet outage  │ Cloudflare caches static assets; users see cached version │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ Power outage     │ UPS (uninterruptible power supply) recommended            │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ Hardware failure │ Daily backups to external drive or cloud storage          │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ DDoS attacks     │ Cloudflare handles at edge (free tier included)           │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ IP exposure      │ Cloudflare Tunnel hides your real IP                      │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ ISP blocks ports │ Tunnel bypasses port restrictions                         │
  └──────────────────┴───────────────────────────────────────────────────────────┘
  ---
  Final Checklist Before Launch

  Legal & Compliance

  - Business entity for payments resolved
  - Privacy Policy published
  - Terms of Service published
  - Cookie consent implemented
  - GDPR data deletion process documented

  Security

  - Hardcoded credentials removed
  - HSTS enabled
  - Rate limiting tested
  - Security headers verified
  - SSL certificate active

  Payments

  - Stripe account active
  - Test transactions successful
  - Webhook handlers working
  - Refund flow tested
  - Payout to test tutor successful

  Infrastructure

  - Cloudflare Tunnel stable
  - Backup script tested
  - Monitoring/logs accessible
  - Health checks passing
  - Domain DNS configured

  Features

  - User registration → booking → payment flow works
  - Tutor onboarding → approval → payout flow works
  - Email notifications sending
  - Video meeting links generating

  ---
  Questions?

  Do you want me to:
  1. Start implementing any specific phase?
  2. Deep dive into Stripe Connect alternatives for Serbia?
  3. Create the production Docker Compose configuration?
  4. Set up the Cloudflare Tunnel configuration?
  5. Design the Owner analytics dashboard schema?

  Let me know your priority and I'll begin implementation.