# Support Processes

**Last Updated**: 2026-01-29

---

## Support Channels

### Primary Channels

| Channel | Purpose | Response Time Target |
|---------|---------|----------------------|
| Email (support@edustream.com) | General inquiries, account issues | 24 hours |
| In-app Help | Context-aware help, FAQs | Immediate (self-service) |
| Live Chat | Urgent issues during business hours | 5 minutes |

### Internal Escalation

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| Slack #support-escalations | Engineering escalation | 30 minutes |
| PagerDuty | Critical incidents | 15 minutes |
| Email engineering@edustream.com | Non-urgent technical issues | 24 hours |

---

## Ticket Categories

### Category 1: Account Issues

**Examples:**
- Cannot log in
- Password reset not working
- Account locked
- Profile update issues

**Tier 1 Actions:**
1. Verify user identity (email + last 4 of payment method)
2. Check account status in admin panel
3. Reset password if needed
4. Unlock account if locked

**Escalation Trigger:**
- OAuth issues
- Database inconsistencies
- Suspected fraud

### Category 2: Payment Issues

**Examples:**
- Payment failed
- Refund not received
- Wrong amount charged
- Package not credited

**Tier 1 Actions:**
1. Verify transaction in Stripe dashboard
2. Check booking status in admin
3. Process refund if appropriate
4. Credit wallet for compensation

**Escalation Trigger:**
- Stripe webhook failures
- Disputed transactions
- System-wide payment issues

### Category 3: Booking Issues

**Examples:**
- Cannot create booking
- Booking not confirmed
- Session not started
- No-show dispute

**Tier 1 Actions:**
1. Check booking state in admin
2. Verify tutor availability
3. Check for conflicts
4. Manually update state if appropriate

**Escalation Trigger:**
- State machine bugs
- Zoom integration failures
- Calendar sync issues

### Category 4: Tutor Issues

**Examples:**
- Application status inquiry
- Profile not showing
- Availability not updating
- Payout issues

**Tier 1 Actions:**
1. Check tutor status in admin
2. Verify profile completeness
3. Check Stripe Connect status
4. Review availability settings

**Escalation Trigger:**
- Stripe Connect issues
- Search ranking problems
- Repeated complaints

### Category 5: Technical Issues

**Examples:**
- App not loading
- Features not working
- Error messages
- Performance issues

**Tier 1 Actions:**
1. Gather browser/device info
2. Check for known issues
3. Clear cache instructions
4. Collect screenshots/logs

**Escalation Trigger:**
- All technical issues → Engineering

---

## Response Templates

### Welcome Response

```
Hi [Name],

Thank you for contacting EduStream Support! I'm [Agent] and I'll be helping you today.

I've received your inquiry about [issue summary]. Let me look into this for you.

[Action taken / Question asked]

Best,
[Agent]
EduStream Support
```

### Account Verification

```
Hi [Name],

For security purposes, I need to verify your account before proceeding.

Could you please confirm:
1. The email address associated with your account
2. The last 4 digits of the payment method on file (if applicable)

Once verified, I'll be happy to assist with your request.

Best,
[Agent]
```

### Issue Resolved

```
Hi [Name],

Great news! I've [action taken] and [expected result].

Please try [specific action] and let me know if everything is working as expected.

Is there anything else I can help you with?

Best,
[Agent]
EduStream Support
```

### Escalation Notice

```
Hi [Name],

Thank you for your patience. I've escalated your case to our technical team for further investigation.

Reference number: [TICKET-ID]

You can expect an update within [timeframe]. I'll follow up personally once we have more information.

Best,
[Agent]
EduStream Support
```

### Compensation Offered

```
Hi [Name],

I sincerely apologize for the inconvenience you experienced with [issue].

As a gesture of goodwill, I've added [compensation] to your account:
- [Credit amount / Free session / etc.]

This has been applied and is available immediately.

We value you as a customer and appreciate your understanding.

Best,
[Agent]
EduStream Support
```

---

## Escalation Matrix

### Severity Levels

| Level | Description | Response Time | Escalation Path |
|-------|-------------|---------------|-----------------|
| **P0** | Service down, data loss | 15 min | PagerDuty → On-call → CTO |
| **P1** | Major feature broken | 1 hour | Slack → Engineering Lead |
| **P2** | Feature degraded | 4 hours | Slack → Engineering |
| **P3** | Minor issue | 24 hours | Ticket → Engineering |

### When to Escalate

**Immediately (P0):**
- Complete service outage
- Payment system failure
- Data breach suspected
- Security vulnerability

**Within 1 hour (P1):**
- Login system broken
- Bookings not processing
- Payments failing for multiple users
- Real-time features down

**Within 4 hours (P2):**
- Single user critical issue
- Integration failures
- Performance degradation
- Feature bugs

### Escalation Process

1. **Document** the issue thoroughly
2. **Check** known issues and recent deployments
3. **Gather** reproduction steps and logs
4. **Post** to #support-escalations with template:
   ```
   🚨 ESCALATION: [Brief Title]

   **Severity**: P1/P2/P3
   **Affected Users**: [count/description]
   **Ticket**: [ID]

   **Issue**: [detailed description]

   **Steps to Reproduce**:
   1. ...
   2. ...

   **User Impact**: [description]

   **What I've Tried**: [actions taken]
   ```

---

## Admin Panel Reference

### User Management

**Location**: `/admin/users`

**Actions available:**
- Search users by email/name
- View user details and roles
- Suspend/unsuspend accounts
- Reset passwords
- View audit logs

### Booking Management

**Location**: `/admin/bookings`

**Actions available:**
- Search bookings by ID/user
- View booking details and history
- Update booking states (with reason)
- Process manual refunds
- View state transition history

### Tutor Management

**Location**: `/admin/tutors`

**Actions available:**
- Review pending applications
- Approve/reject tutors
- View tutor profiles
- Check Stripe Connect status
- View booking history

### Payment Management

**Location**: Admin uses Stripe Dashboard

**Actions available:**
- View transactions
- Process refunds
- View disputes
- Check webhook delivery

---

## Common Issues & Solutions

### "I can't log in"

1. Verify email is correct
2. Check if account exists
3. Try password reset
4. Check if account is suspended
5. Clear browser cache
6. Try incognito mode
7. Escalate if OAuth issue

### "My payment failed"

1. Check Stripe dashboard for decline reason
2. Common reasons: insufficient funds, card expired, 3DS failure
3. Advise user to try different payment method
4. Check if payment actually succeeded (webhook delay)

### "My booking wasn't confirmed"

1. Check booking state in admin
2. Verify tutor received notification
3. Check if auto-expired
4. Look for conflicts
5. Manually confirm if appropriate

### "I didn't receive my refund"

1. Check Stripe dashboard for refund status
2. Verify refund was processed
3. Explain 5-10 business day processing
4. Provide transaction ID

### "Tutor didn't show up"

1. Verify booking was confirmed
2. Check session start time
3. Document no-show
4. Process refund per policy
5. Update tutor record

---

## Compensation Guidelines

### Standard Compensation

| Issue Type | Compensation |
|------------|--------------|
| Service outage affecting booking | Full refund + 10% credit |
| Tutor no-show | Full refund + free session credit |
| Payment processing error | Refund + $5 credit |
| Minor inconvenience | $5-10 credit |
| Major inconvenience | $15-25 credit |

### Approval Required

| Compensation Amount | Approval Level |
|---------------------|----------------|
| Up to $10 | Tier 1 Support |
| $11-50 | Support Lead |
| $51-100 | Support Manager |
| Over $100 | Operations Director |

---

## Metrics & Reporting

### Support Metrics

| Metric | Target |
|--------|--------|
| First Response Time | <4 hours |
| Resolution Time | <24 hours |
| Customer Satisfaction (CSAT) | >90% |
| First Contact Resolution | >70% |
| Escalation Rate | <20% |

### Weekly Report

Generate weekly with:
- Total tickets by category
- Resolution times
- CSAT scores
- Top issues
- Escalation summary

---

## Contact Directory

### Internal Contacts

| Role | Contact | When to Contact |
|------|---------|-----------------|
| Support Lead | support-lead@edustream.com | Approvals, complex cases |
| Engineering On-call | PagerDuty | P0/P1 incidents |
| Engineering Lead | eng-lead@edustream.com | P2 escalations |
| Operations | ops@edustream.com | Business escalations |
| Legal | legal@edustream.com | Legal/compliance issues |

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| Stripe Support | dashboard.stripe.com | Payment issues |
| Brevo Support | app.brevo.com | Email delivery |
| Zoom Support | support.zoom.us | Video issues |

---

## Related Documents

- [Incident Response](./runbooks/incident-response.md) - Technical incident handling
- [On-Call Procedures](./ON_CALL.md) - Engineering on-call
- [Metrics](./METRICS.md) - Success metrics
