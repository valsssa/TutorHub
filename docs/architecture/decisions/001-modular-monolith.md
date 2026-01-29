# ADR-001: Modular Monolith Architecture

## Status

Accepted

## Date

2026-01-29

## Context

EduStream is a student-tutor marketplace MVP requiring rapid development and iteration. The team is small (< 5 engineers), and operational simplicity is paramount.

Key forces at play:
- **Team size**: Small team cannot support microservices operational overhead
- **Product stage**: MVP requires fast iteration over distributed complexity
- **Scaling needs**: Initial target is 1,000-10,000 MAU
- **Domain complexity**: Booking system has complex state management
- **Operational resources**: Limited DevOps capacity

## Decision

We will use a **Modular Monolith** architecture with Domain-Driven Design patterns.

The backend will be organized into feature modules under `backend/modules/`, each with clear boundaries and internal layering based on complexity:

1. **Full DDD** for complex domains (bookings, auth, tutor_profile)
   - domain/ -> application/ -> infrastructure/ -> presentation/

2. **Service + Presentation** for moderate complexity (packages, notifications, messages)
   - services/ -> presentation/

3. **Presentation Only** for simple CRUD (reviews, favorites, subjects)
   - Direct api.py routes

All modules share:
- Common infrastructure (`core/`)
- Database connection pool
- Single deployment unit

## Consequences

### Positive

- **Operational simplicity**: Single deployment, single database, simple debugging
- **Fast development**: Shared infrastructure, no network calls between modules
- **Future optionality**: Module boundaries allow future extraction to microservices
- **Easy onboarding**: New engineers learn one codebase, not distributed systems

### Negative

- **Scaling limitations**: Cannot scale modules independently
- **Deployment coupling**: All modules deploy together
- **Discipline required**: Must maintain module boundaries by convention
- **Single point of failure**: No service isolation

### Neutral

- Database coupling is intentional for transactional consistency
- Module dependencies documented but not enforced by tooling

## Alternatives Considered

### Option A: Traditional Monolith

Single codebase without explicit module boundaries.

**Pros:**
- Even simpler to start
- No module boundary overhead

**Cons:**
- Dependencies become tangled over time
- Hard to extract services later
- Difficult to parallelize development

**Why not chosen:** Tangled dependencies would slow development within months.

### Option B: Microservices

Separate services for each domain (bookings, payments, users, etc.).

**Pros:**
- Independent scaling
- Team autonomy
- Technology flexibility

**Cons:**
- Network complexity
- Distributed transactions difficult
- Operational overhead (container orchestration, service mesh)
- Team size insufficient

**Why not chosen:** Operational overhead exceeds benefit at current scale.

### Option C: Serverless Functions

AWS Lambda / Cloud Functions for each endpoint.

**Pros:**
- Auto-scaling
- Pay-per-use

**Cons:**
- Cold starts
- Stateful operations difficult
- Vendor lock-in
- Complex state machine handling

**Why not chosen:** Booking state machine requires consistent state handling.

## References

- [Modular Monolith: A Primer](https://www.kamilgrzybek.com/design/modular-monolith-primer/)
- [MonolithFirst by Martin Fowler](https://martinfowler.com/bliki/MonolithFirst.html)
- Backend module structure: `backend/modules/README.md`
