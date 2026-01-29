# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the EduStream platform.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](./001-modular-monolith.md) | Modular Monolith Architecture | Accepted | 2026-01-29 |
| [ADR-002](./002-booking-state-machine.md) | Four-Field Booking State Machine | Accepted | 2026-01-29 |
| [ADR-003](./003-postgresql-database.md) | PostgreSQL as Primary Database | Accepted | 2026-01-29 |
| [ADR-004](./004-jwt-authentication.md) | JWT Authentication Strategy | Accepted | 2026-01-29 |
| [ADR-005](./005-stripe-payments.md) | Stripe Connect for Payments | Accepted | 2026-01-29 |

## Creating a New ADR

1. Copy the template from `_template.md`
2. Name it `XXX-short-title.md` (next sequential number)
3. Fill in all sections
4. Update this README's index
5. Submit PR for review

## ADR Lifecycle

- **Proposed**: Under discussion
- **Accepted**: Decision has been made
- **Deprecated**: No longer applies but kept for history
- **Superseded**: Replaced by another ADR (link to new one)

## Template

See [_template.md](./_template.md) for the standard ADR format.
