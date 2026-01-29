# On-Call Procedures

**Last Updated**: 2026-01-29

---

## On-Call Overview

### Rotation Schedule

| Week | Primary | Secondary |
|------|---------|-----------|
| Week 1 | Engineer A | Engineer B |
| Week 2 | Engineer B | Engineer C |
| Week 3 | Engineer C | Engineer D |
| Week 4 | Engineer D | Engineer A |

**Rotation changes**: Sundays at 10:00 AM UTC

### Coverage Hours

| Type | Hours | Response Time |
|------|-------|---------------|
| Business Hours | Mon-Fri 9am-6pm | 15 minutes (P0), 1 hour (P1) |
| After Hours | All other times | 30 minutes (P0), 4 hours (P1) |

---

## Alert Sources

### PagerDuty Services

| Service | Description | Severity |
|---------|-------------|----------|
| edustream-backend-critical | API errors, service down | P0 |
| edustream-frontend-critical | Frontend errors | P0 |
| edustream-database | Database issues | P0 |
| edustream-payments | Payment failures | P0/P1 |
| edustream-general | Non-critical alerts | P2 |

### Alert Routing

```
Sentry Error → PagerDuty
  ↓
Primary On-Call (15 min)
  ↓ (if no ack)
Secondary On-Call (15 min)
  ↓ (if no ack)
Engineering Manager
  ↓ (if no ack)
CTO
```

---

## Response Procedures

### Step 1: Acknowledge

Within response time window:
1. Acknowledge alert in PagerDuty
2. Join incident Slack channel if created
3. Post initial assessment

```
🔍 Investigating: [Brief description]
- Alert: [Alert name]
- Time: [Timestamp]
- Initial assessment: [What you see]
```

### Step 2: Assess Severity

| Severity | Criteria | Action |
|----------|----------|--------|
| **P0** | Service down, data loss | Create incident, all hands |
| **P1** | Major feature broken | Create incident, primary focus |
| **P2** | Feature degraded | Investigate, fix in business hours |
| **P3** | Minor issue | Track, fix in sprint |

### Step 3: Investigate

1. **Check dashboards**
   - Sentry: https://sentry.io/organizations/edustream/
   - Infrastructure: [monitoring URL]
   - Logs: `docker compose logs -f`

2. **Check recent changes**
   - Recent deployments: `git log --oneline -10`
   - Config changes
   - Infrastructure changes

3. **Gather information**
   - Error messages
   - Affected users/endpoints
   - Timestamp of first occurrence

### Step 4: Mitigate

**Quick mitigations:**

| Issue | Mitigation |
|-------|------------|
| Bad deployment | Rollback: `./scripts/rollback.sh` |
| Database overload | Kill long queries, add read replica |
| Memory issues | Restart service: `docker compose restart backend` |
| Rate limiting | Adjust limits or whitelist |
| External service down | Enable fallback, communicate delay |

### Step 5: Communicate

**Status updates every 30 minutes during incident:**

```
📊 Update [HH:MM UTC]:
- Status: [investigating/mitigating/resolved]
- Impact: [description]
- Actions: [what we're doing]
- ETA: [if known]
```

### Step 6: Resolve

1. Confirm fix is deployed and working
2. Monitor for 30 minutes
3. Update status page
4. Post final update:

```
✅ Resolved [HH:MM UTC]:
- Issue: [brief description]
- Root cause: [if known]
- Resolution: [what fixed it]
- Duration: [X hours Y minutes]
- Follow-up: [any needed actions]
```

---

## Runbooks Quick Reference

### Service Won't Start

```bash
# Check logs
docker compose logs backend --tail=100

# Check container status
docker compose ps

# Rebuild and restart
docker compose down
docker compose up --build -d
```

### Database Connection Issues

```bash
# Check database is running
docker compose exec db pg_isready

# Check connection count
docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Restart database (caution)
docker compose restart db
```

### High Error Rate

```bash
# Check Sentry for error details
# Check logs for patterns
docker compose logs backend --tail=500 | grep -i error

# Check API response times
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/api/v1/health
```

### Payment Failures

1. Check Stripe dashboard for webhook delivery
2. Verify webhook secret matches
3. Check backend logs for Stripe errors
4. Manual retry webhook if needed

### Full Runbooks

See `docs/runbooks/` for detailed procedures:
- [Database Operations](./runbooks/database.md)
- [Deployment & Rollback](./runbooks/deployment.md)
- [Incident Response](./runbooks/incident-response.md)
- [Cache Operations](./runbooks/cache.md)
- [Log Analysis](./runbooks/logs.md)

---

## Emergency Contacts

### Escalation Path

| Level | Contact | When |
|-------|---------|------|
| 1 | Primary On-Call | First responder |
| 2 | Secondary On-Call | 15 min no response |
| 3 | Engineering Manager | 30 min no response |
| 4 | CTO | Critical/extended outage |

### External Services

| Service | Contact | Issue Type |
|---------|---------|------------|
| Stripe | stripe.com/support | Payment issues |
| Hosting Provider | [support URL] | Infrastructure |
| Domain/DNS | [provider] | DNS issues |

---

## On-Call Checklist

### Start of Shift

- [ ] Verify PagerDuty access
- [ ] Check current alert status
- [ ] Review any ongoing incidents
- [ ] Verify VPN/access works
- [ ] Check laptop battery/charger
- [ ] Confirm secondary contact

### During Shift

- [ ] Keep phone accessible
- [ ] Stay within response time of laptop
- [ ] Monitor Slack #alerts channel
- [ ] Check dashboards periodically

### End of Shift

- [ ] Handoff any active issues
- [ ] Update incident documentation
- [ ] Brief incoming on-call
- [ ] Update rotation calendar if swapped

---

## Swap Procedures

### Requesting a Swap

1. Find coverage at least 48 hours in advance
2. Post in #on-call-swaps with dates
3. Get confirmation from covering engineer
4. Update PagerDuty schedule
5. Notify manager

### Coverage Compensation

- Swap within same pay period: time trade
- No swap available: overtime rate applies
- Holiday coverage: holiday rate applies

---

## Post-Incident

### Within 24 Hours

1. Create postmortem document
2. Schedule postmortem meeting
3. Track follow-up items

### Postmortem Template

```markdown
# Incident Postmortem: [Title]

**Date**: [YYYY-MM-DD]
**Duration**: [X hours Y minutes]
**Severity**: [P0/P1/P2]
**Author**: [Name]

## Summary
[2-3 sentence summary of what happened]

## Timeline
- HH:MM - [Event]
- HH:MM - [Event]

## Root Cause
[What caused the incident]

## Impact
- Users affected: [count]
- Duration: [time]
- Revenue impact: [if applicable]

## What Went Well
- [Item]

## What Could Be Improved
- [Item]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action] | [Name] | [Date] | ⬜ |
```

### Follow-Up Actions

- File issues for all action items
- Track in sprint planning
- Review in next team meeting

---

## Training Requirements

### Before First Shift

- [ ] Complete on-call training session
- [ ] Shadow one on-call shift
- [ ] Review all runbooks
- [ ] Verify all access (PagerDuty, Sentry, servers)
- [ ] Test alerting to your phone
- [ ] Complete incident response drill

### Quarterly

- [ ] Runbook review and update
- [ ] Incident response drill
- [ ] Access audit

---

## FAQ

**Q: What if I can't acknowledge in time?**
A: Alert escalates to secondary. Message them ASAP.

**Q: What if I don't know how to fix something?**
A: Escalate early. Better to wake someone than cause extended outage.

**Q: Do I need to be at my computer 24/7?**
A: No, but within response time of your laptop with internet.

**Q: What counts as "resolved"?**
A: Service restored to normal operation. Root cause fix can be later.

**Q: Who pays for on-call?**
A: Per company policy. Check with manager.

---

## Related Documents

- [Incident Response Playbook](./runbooks/incident-response.md)
- [Support Processes](./SUPPORT.md)
- [Metrics](./METRICS.md)
