# ADR-003: PostgreSQL as Primary Database

## Status

Accepted

## Date

2026-01-29

## Context

EduStream requires a database that can:
- Handle financial transactions with ACID guarantees
- Store structured relational data (users, bookings, payments)
- Support flexible metadata (JSONB)
- Enable full-text search for tutor discovery
- Scale to 10,000+ monthly active users

## Decision

We will use **PostgreSQL 17** as the primary database.

Key features utilized:
- ACID transactions for payment and booking operations
- JSONB columns for flexible metadata (pricing snapshots, preferences)
- tsvector/tsquery for full-text tutor search
- Partial indexes for soft-delete optimization
- CHECK constraints for data validation
- Connection pooling (pool_size=10, max_overflow=20)

## Consequences

### Positive

- **Strong consistency**: ACID transactions for financial operations
- **Feature-rich**: JSONB, full-text search, advanced indexing
- **Mature ecosystem**: Excellent tooling, documentation, community
- **Hosting options**: Self-hosted or managed (RDS, Cloud SQL, Supabase)
- **SQLAlchemy support**: First-class ORM integration

### Negative

- **Horizontal scaling complexity**: Sharding is difficult
- **Operational overhead**: Requires tuning for large scale
- **Write scalability**: Single primary node bottleneck

### Neutral

- Read replicas needed for read-heavy scale-out
- Connection pooling limits concurrent connections

## Alternatives Considered

### Option A: MySQL

Widely used relational database.

**Pros:**
- Very common, easy to hire
- Good performance

**Cons:**
- Weaker JSONB support
- Fewer advanced features (partial indexes, arrays)
- Less flexible type system

**Why not chosen:** PostgreSQL features better match our needs.

### Option B: MongoDB

Document database with flexible schema.

**Pros:**
- Schema flexibility
- Horizontal scaling built-in
- JSON-native

**Cons:**
- No ACID for multi-document transactions (historically)
- Not ideal for relational data
- Different query paradigm

**Why not chosen:** Financial transactions require strong ACID guarantees.

### Option C: CockroachDB

Distributed SQL database compatible with PostgreSQL.

**Pros:**
- Horizontal scaling
- Geographic distribution
- PostgreSQL compatible

**Cons:**
- Higher complexity
- Cost overhead
- Overkill for MVP scale

**Why not chosen:** Complexity not justified at current scale.

## References

- Schema: `database/init.sql`
- Connection pool: `backend/database.py`
- Migrations: `database/migrations/`
