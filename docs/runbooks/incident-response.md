# Incident Response Runbook

## Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P1** | Complete outage | 15 minutes | Site down, payments broken, data breach |
| **P2** | Major degradation | 1 hour | Bookings failing, significant errors |
| **P3** | Minor issues | 4 hours | Feature not working, UI bug |
| **P4** | Low priority | 24 hours | Cosmetic issues |

---

## Incident Response Process

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DETECTION  │───▶│   TRIAGE    │───▶│  MITIGATE   │───▶│   RESOLVE   │───▶│ POST-MORTEM │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Phase 1: Detection

### Automated Alerts
- Sentry error rate spike
- Uptime monitor down alert
- Stripe webhook failures
- High CPU/memory alerts

### Manual Detection
- User reports
- Support tickets
- Team observation

### First Response
1. Acknowledge the alert (PagerDuty/Slack)
2. Check if it's a real incident or false positive
3. Assign severity level

---

## Phase 2: Triage

### Quick Assessment Checklist

```bash
# 1. Is the site up?
curl -I https://edustream.valsa.solutions
curl -I https://api.valsa.solutions/health

# 2. Are services running?
docker compose ps

# 3. What's in the logs?
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend

# 4. Check error monitoring
# Visit: https://sentry.io/organizations/YOUR_ORG/issues/

# 5. Check payments
# Visit: https://dashboard.stripe.com/events
```

### Communication
1. Create incident channel: `#inc-YYYY-MM-DD-brief-description`
2. Post initial assessment
3. Tag on-call engineer and relevant team members

### Incident Template

```markdown
## Incident: [Brief Description]
**Severity:** P1/P2/P3
**Status:** Investigating / Mitigating / Resolved
**Started:** YYYY-MM-DD HH:MM UTC
**Responders:** @name1, @name2

### Impact
- Who is affected?
- What functionality is broken?

### Timeline
- HH:MM - First alert received
- HH:MM - Investigation started

### Current Status
[What do we know? What are we doing?]

### Next Update
In X minutes
```

---

## Phase 3: Mitigate

### Priority 1: Stop the Bleeding

**If site is down:**
```bash
# Restart all services
docker compose restart

# If still down, check individual services
docker compose logs backend
docker compose restart backend
```

**If payments are failing:**
```bash
# Check Stripe dashboard for issues
# Check webhook logs
docker compose logs backend | grep -i stripe

# If webhook issue, verify endpoint
curl -X POST https://api.valsa.solutions/api/payments/webhook
```

**If database is unresponsive:**
```bash
# Check database status
docker compose exec db pg_isready

# Restart database
docker compose restart db

# Check connections
docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### Rollback Decision Tree

```
Is the issue caused by recent deployment?
├── YES → Rollback immediately (see deployment runbook)
└── NO → Continue investigation

Is data being corrupted?
├── YES → Stop writes, switch to maintenance mode
└── NO → Continue investigation

Can we fix forward quickly (<15 min)?
├── YES → Apply hotfix
└── NO → Rollback first, then fix properly
```

---

## Phase 4: Resolve

### Verification Checklist

After fix is applied:

- [ ] Health check returns 200
- [ ] Error rate returned to normal in Sentry
- [ ] Users can log in
- [ ] Users can search tutors
- [ ] Users can create bookings
- [ ] Payments processing
- [ ] Emails sending

### Communication

1. Update incident channel with resolution
2. Post in #general if user-facing impact
3. Send status page update (if applicable)

---

## Phase 5: Post-Mortem

### When Required
- All P1 incidents
- P2 incidents with >30 min impact
- Any incident affecting payments

### Timeline
- Draft within 48 hours
- Team review within 1 week
- Action items assigned and tracked

### Post-Mortem Template

```markdown
# Post-Mortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1/P2
**Author:** [Name]

## Summary
[2-3 sentence summary of what happened]

## Impact
- Users affected: X
- Revenue impact: $X
- Features affected: [list]

## Timeline (all times UTC)
- HH:MM - First alert
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Verified resolved

## Root Cause
[Detailed technical explanation]

## What Went Well
- [Bullet points]

## What Went Wrong
- [Bullet points]

## Action Items
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Action] | @name | YYYY-MM-DD | Open |

## Lessons Learned
[Key takeaways for the team]
```

---

## Common Incidents

### High Error Rate

1. Check Sentry for error patterns
2. Identify affected endpoint(s)
3. Check recent deployments
4. Review logs for root cause
5. Apply fix or rollback

### Slow Response Times

1. Check database query performance
   ```bash
   docker compose exec db psql -U postgres -d authapp -c "
   SELECT query, calls, mean_time, total_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 10;"
   ```
2. Check CPU/memory usage
   ```bash
   docker stats
   ```
3. Check for connection pool exhaustion
4. Scale up or optimize queries

### Payment Failures

1. Check Stripe dashboard for issues
2. Verify webhook delivery
3. Check backend logs for Stripe errors
4. Contact Stripe support if platform issue

### Email Not Sending

1. Check Brevo dashboard for delivery
2. Verify API key is valid
3. Check for rate limiting
4. Check backend logs for Brevo errors

### Database Connection Issues

1. Check connection count
2. Restart connection pool (restart backend)
3. Check for long-running queries
4. Kill blocking queries if needed

---

## Escalation Matrix

| Severity | First Responder | Escalate After | Escalate To |
|----------|-----------------|----------------|-------------|
| P1 | On-call Engineer | 15 min | Engineering Lead |
| P1 | Engineering Lead | 30 min | CEO |
| P2 | On-call Engineer | 1 hour | Engineering Lead |
| P3 | On-call Engineer | 4 hours | Team Lead |

---

## Emergency Maintenance Mode

If you need to take the site down for emergency maintenance:

1. **Update DNS or load balancer** to point to maintenance page
2. **Or create maintenance response**
   ```bash
   # Quick maintenance mode (returns 503)
   docker compose stop backend
   # Frontend will show error or maintenance message
   ```

3. **Communicate**
   - Post on Twitter/social media
   - Update status page
   - Email affected users (for extended outages)
