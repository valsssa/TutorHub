# ADR-005: Stripe Connect for Payments

## Status

Accepted

## Date

2026-01-29

## Context

EduStream is a two-sided marketplace requiring:
- Student payment for sessions
- Tutor earnings with platform commission
- Automatic payouts to tutors
- Refund handling for cancellations/disputes
- PCI compliance without handling raw card data

The platform takes a tiered commission (20%/15%/10% based on tutor lifetime earnings).

## Decision

We will use **Stripe Connect** with the Express account type for marketplace payments.

Flow:
1. Students pay via Stripe Checkout
2. Funds held until session completion
3. Platform fee automatically deducted
4. Tutors receive payouts to their connected accounts

Integration points:
- Stripe Checkout for payment collection
- Stripe Connect for tutor onboarding
- Webhooks for async event handling
- PaymentIntents for authorization/capture flow

Commission implementation:
```python
if lifetime_earnings < 1000:
    platform_fee_pct = 20
elif lifetime_earnings < 5000:
    platform_fee_pct = 15
else:
    platform_fee_pct = 10
```

## Consequences

### Positive

- **PCI compliance delegated**: Stripe handles card data
- **Tutor payouts automated**: No manual transfers
- **Refunds built-in**: Stripe handles refund mechanics
- **Marketplace-native**: Express accounts designed for this use case
- **Global coverage**: 40+ countries supported

### Negative

- **Processing fees**: ~2.9% + $0.30 per transaction
- **Vendor lock-in**: Significant integration effort
- **Payout delays**: Standard is T+2 to T+7 days
- **Currency complexity**: Multi-currency adds complexity

### Neutral

- Stripe's fraud protection is included
- Dashboard provides operational visibility
- API rate limits manageable at our scale

## Alternatives Considered

### Option A: PayPal Commerce Platform

PayPal's marketplace solution.

**Pros:**
- Widely trusted by consumers
- Global reach

**Cons:**
- Higher fees for marketplace
- Complex integration
- Less developer-friendly

**Why not chosen:** Developer experience inferior; Stripe more suitable.

### Option B: Adyen for Platforms

Enterprise marketplace solution.

**Pros:**
- Lower rates at high volume
- More payment methods

**Cons:**
- Enterprise pricing/contracts
- Longer integration time
- Overkill for MVP

**Why not chosen:** Enterprise focus not suitable for MVP.

### Option C: Build with Stripe Direct

Direct charges without Connect (platform as merchant of record).

**Pros:**
- Simpler integration
- Lower per-transaction complexity

**Cons:**
- Manual tutor payouts
- Platform liable for all transactions
- Regulatory complexity

**Why not chosen:** Connect's marketplace features essential for scaling.

## Future Considerations

- Add Stripe Billing for subscription packages
- Implement split payments for group sessions
- Add instant payouts for premium tutors
- Multi-currency pricing display

## References

- Implementation: `backend/core/stripe_client.py`
- Payment module: `backend/modules/payments/`
- Webhook handling: `backend/modules/payments/webhooks.py`
