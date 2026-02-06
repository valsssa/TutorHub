# ADR-009: Brevo for Transactional Email

## Status

Accepted

## Date

2026-01-29

## Context

EduStream requires transactional email capabilities for:
- Booking confirmations (to student and tutor)
- Session reminders (24h and 1h before)
- Cancellation notifications
- Password reset emails
- Welcome emails for new users
- Email verification

Key requirements:
- **Deliverability**: Emails must reach inbox, not spam
- **Template support**: Consistent branding across emails
- **API-based**: Programmatic sending from backend
- **Cost effective**: Free tier sufficient for MVP
- **Reliability**: High uptime with fallback options
- **Compliance**: GDPR-compliant for European users

## Decision

We will use **Brevo** (formerly Sendinblue) for transactional email delivery.

Integration approach:
- Python SDK (`sib-api-v3-sdk`) for API calls
- Inline HTML templates in code (not Brevo template system)
- Lazy client initialization for performance
- Graceful degradation when API key not configured

Configuration:
```python
BREVO_API_KEY = "xkeysib-..."
BREVO_SENDER_EMAIL = "noreply@edustream.valsa.solutions"
BREVO_SENDER_NAME = "EduStream"
EMAIL_ENABLED = True  # Toggle for development
```

Email categories:
- **Booking lifecycle**: Confirmation, reminder, cancellation
- **Authentication**: Password reset, email verification
- **Onboarding**: Welcome email with role-specific content

## Consequences

### Positive

- **Generous free tier**: 300 emails/day free, sufficient for MVP
- **Good deliverability**: Established sender reputation
- **Simple API**: Easy Python SDK integration
- **GDPR compliant**: EU-based company, data processing agreements
- **Real-time tracking**: Open and click tracking available
- **Multiple channels**: Can add SMS later with same platform

### Negative

- **Vendor dependency**: Tied to Brevo API and pricing
- **Template limitations**: Inline templates harder to maintain than visual editor
- **Rate limits**: Free tier has daily sending limits
- **No local testing**: Requires API key even for development

### Neutral

- Email analytics available but not currently used
- Bounce handling managed by Brevo
- Unsubscribe links required for marketing (not transactional)

## Alternatives Considered

### Option A: Amazon SES

AWS Simple Email Service.

**Pros:**
- Extremely cost effective at scale
- Integrates with AWS ecosystem
- High deliverability
- Flexible configuration

**Cons:**
- Requires AWS account
- More complex setup (domain verification, sandbox exit)
- No built-in template editor
- Raw API, more code needed

**Why not chosen:** More setup complexity; Brevo faster for MVP.

### Option B: SendGrid

Popular transactional email provider.

**Pros:**
- Industry standard
- Excellent documentation
- Good template system
- Strong deliverability

**Cons:**
- Free tier limited (100 emails/day)
- Pricing scales less favorably
- Acquired by Twilio (pricing changes)

**Why not chosen:** Brevo free tier more generous for MVP stage.

### Option C: Postmark

Developer-focused transactional email.

**Pros:**
- Excellent deliverability
- Simple, focused product
- Good developer experience

**Cons:**
- No free tier (pay from first email)
- More expensive per email
- Less feature-rich

**Why not chosen:** No free tier makes it expensive for MVP validation.

### Option D: Self-hosted (Postal, Mailcow)

Run own email infrastructure.

**Pros:**
- Full control
- No per-email costs
- Privacy

**Cons:**
- Significant operational overhead
- Deliverability challenges (IP reputation)
- Spam filter management
- Infrastructure costs

**Why not chosen:** Operational complexity not justified; deliverability risk.

### Option E: SMTP Relay

Use generic SMTP provider (Mailgun, SparkPost).

**Pros:**
- Standard protocol
- Provider flexibility

**Cons:**
- Similar costs to Brevo
- Less integrated experience
- More configuration needed

**Why not chosen:** Brevo SDK simpler than raw SMTP integration.

## Template Strategy

Current approach: Inline HTML templates in Python code.

```python
html_content = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h1 style="color: #10b981;">Booking Confirmed!</h1>
    <p>Hi {student_name},</p>
    ...
</body>
</html>
"""
```

Benefits:
- Templates versioned with code
- Dynamic content via f-strings
- No external template management

Drawbacks:
- Harder for non-developers to edit
- HTML mixed with Python code
- No visual preview

Future consideration:
- Move to Brevo template system for marketing emails
- Consider Jinja2 templates for complex layouts
- Email preview endpoint for development

## Fallback Handling

When Brevo is unavailable or not configured:

1. **No API key**: Log email content, return success
   ```python
   if not settings.BREVO_API_KEY:
       logger.warning("Brevo API key not configured - emails disabled")
       return True  # Don't fail the operation
   ```

2. **API failure**: Log error, return False
   ```python
   except Exception as e:
       logger.error(f"Failed to send email: {e}")
       return False
   ```

3. **Development mode**: `EMAIL_ENABLED=False` logs but doesn't send

Operations should not fail due to email delivery issues. Email is best-effort.

## Email Types

### Booking Emails

| Email | Trigger | Recipients |
|-------|---------|------------|
| Confirmation | Tutor accepts | Student, Tutor |
| Reminder (24h) | 24h before session | Student, Tutor |
| Reminder (1h) | 1h before session | Student, Tutor |
| Cancellation | Booking cancelled | Affected party |

### Authentication Emails

| Email | Trigger | Recipients |
|-------|---------|------------|
| Password Reset | User requests reset | User |
| Email Verification | Registration | New user |
| Welcome | First login | New user |

## Future Enhancements

1. **Template externalization**: Move to Jinja2 or Brevo templates
2. **Email queuing**: Async sending via background jobs
3. **Retry logic**: Automatic retry on transient failures
4. **Analytics integration**: Track open rates, click rates
5. **Preference center**: User email preferences
6. **SMS notifications**: Use Brevo SMS API for urgent alerts

## References

- Implementation: `backend/core/email_service.py`
- Configuration: `backend/core/config.py`
- Brevo API documentation: https://developers.brevo.com/
- Python SDK: https://github.com/sendinblue/APIv3-python-library
