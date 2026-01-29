# EduStream Architecture Documentation

This directory contains comprehensive architectural documentation for the EduStream student-tutor marketplace platform.

## Document Index

| Document | Description |
|----------|-------------|
| [01-business-context.md](./01-business-context.md) | Business goals, target users, and non-functional requirements |
| [02-system-overview.md](./02-system-overview.md) | High-level system architecture and deployment model |
| [03-domain-model.md](./03-domain-model.md) | Domain-driven design, bounded contexts, and aggregates |
| [04-backend-architecture.md](./04-backend-architecture.md) | Backend patterns, API design, and state machines |
| [05-data-storage.md](./05-data-storage.md) | Database design, schema patterns, and migration strategy |
| [06-frontend-architecture.md](./06-frontend-architecture.md) | Frontend patterns, state management, and API consumption |
| [07-security-reliability.md](./07-security-reliability.md) | Authentication, authorization, and threat model |
| [08-scalability-operations.md](./08-scalability-operations.md) | Scaling strategy, CI/CD, and monitoring |
| [09-future-evolution.md](./09-future-evolution.md) | Future requirements and technical debt register |

## Architecture Decision Records

See [decisions/](./decisions/) for Architecture Decision Records (ADRs) documenting key architectural choices.

## Diagrams

See [diagrams/](./diagrams/) for visual representations of system architecture.

## Quick Reference

**Stack**: FastAPI (Python 3.12) + Next.js 15 (TypeScript) + PostgreSQL 17 + Redis 7 + MinIO

**Architecture Style**: Modular Monolith with DDD patterns

**Key Integrations**: Stripe (payments), Google OAuth, Zoom (video), Brevo (email)

**Roles**: student, tutor, admin, owner

## Last Updated

2026-01-29
