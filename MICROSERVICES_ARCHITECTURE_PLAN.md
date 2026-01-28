# Microservices Architecture Migration Plan
## EduStream TutorConnect - True DDD + Microservices

**Target**: Migrate from modular monolith to true microservices with DDD
**Timeline**: 12-16 weeks
**Team Size**: 3-5 developers

---

## 📊 Bounded Context Analysis

### 1. Identity & Access Context (Port 8001)

**Responsibility**: User authentication, authorization, identity management

**Domain Model**:
```
User (Aggregate Root)
├── UserId (Value Object)
├── Email (Value Object)
├── Password (Value Object)
├── Role (Value Object: Student, Tutor, Admin)
└── UserProfile (Entity)
    ├── FirstName
    ├── LastName
    ├── AvatarUrl
    └── Preferences
```

**Domain Events**:
- `UserRegistered`
- `UserLoggedIn`
- `UserPasswordChanged`
- `UserRoleChanged`
- `UserProfileUpdated`

**API Endpoints**:
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/me
PATCH  /api/users/{id}
POST   /api/users/{id}/change-password
```

**Database Tables**:
- users
- user_profiles
- user_sessions
- refresh_tokens

---

### 2. Tutoring Context (Port 8002)

**Responsibility**: Tutor profiles, expertise, availability, ratings

**Domain Model**:
```
TutorProfile (Aggregate Root)
├── TutorId (Value Object)
├── UserId (Foreign Aggregate Reference)
├── Biography (Value Object)
├── Subjects (Collection of Subject Value Objects)
├── Availability (Value Object)
│   ├── WeeklySchedule
│   └── TimeSlots
├── PricingOptions (Collection)
│   ├── HourlyRate (Money Value Object)
│   ├── PackagePrice (Money Value Object)
│   └── Currency
├── Certifications (Collection of Entities)
├── Education (Collection of Entities)
└── Rating (Value Object)
    ├── AverageScore
    └── TotalReviews
```

**Domain Events**:
- `TutorProfileCreated`
- `TutorAvailabilityUpdated`
- `TutorPricingChanged`
- `TutorReviewReceived`
- `TutorVerified`

**API Endpoints**:
```
GET    /api/tutors              # List tutors (search, filter)
GET    /api/tutors/{id}         # Get tutor detail
POST   /api/tutors/profile      # Create tutor profile
PATCH  /api/tutors/profile      # Update profile
PUT    /api/tutors/availability # Update availability
PUT    /api/tutors/pricing      # Update pricing
POST   /api/tutors/certifications
```

**Database Tables**:
- tutor_profiles
- tutor_subjects
- tutor_availability
- tutor_pricing_options
- certifications
- education
- tutor_ratings (projection)

---

### 3. Booking Context (Port 8003)

**Responsibility**: Session booking, scheduling, payments, refunds

**Domain Model**:
```
Booking (Aggregate Root)
├── BookingId (Value Object)
├── StudentId (Foreign Aggregate Reference)
├── TutorId (Foreign Aggregate Reference)
├── BookingSnapshot (Value Object)
│   ├── TutorName
│   ├── TutorEmail
│   ├── StudentName
│   ├── StudentEmail
│   └── OriginalPrice
├── SessionDetails (Value Object)
│   ├── ScheduledAt (DateTime)
│   ├── Duration (Duration)
│   ├── MeetingUrl
│   └── Subject
├── Payment (Entity)
│   ├── Amount (Money Value Object)
│   ├── Status (PaymentStatus Enum)
│   ├── StripePaymentId
│   └── RefundDetails
└── Status (BookingStatus Enum)
    ├── Pending
    ├── Confirmed
    ├── Completed
    ├── Cancelled
    └── Refunded
```

**Domain Services**:
- `BookingConflictChecker` - Check scheduling conflicts
- `RefundCalculator` - Calculate refund amounts
- `BookingConfirmationService` - Auto-confirm instant bookings

**Domain Events**:
- `BookingRequested`
- `BookingConfirmed`
- `BookingCancelled`
- `BookingCompleted`
- `PaymentProcessed`
- `RefundIssued`

**API Endpoints**:
```
POST   /api/bookings            # Create booking
GET    /api/bookings            # List my bookings
GET    /api/bookings/{id}       # Get booking detail
PATCH  /api/bookings/{id}       # Update booking
POST   /api/bookings/{id}/confirm
POST   /api/bookings/{id}/cancel
POST   /api/bookings/{id}/complete
```

**Database Tables**:
- bookings
- booking_snapshots
- payments
- refunds

---

### 4. Messaging Context (Port 8004)

**Responsibility**: Real-time messaging, conversations, notifications

**Domain Model**:
```
Conversation (Aggregate Root)
├── ConversationId (Value Object)
├── Participants (Collection)
│   ├── ParticipantId (Foreign Reference)
│   └── Role (Student/Tutor)
├── Messages (Collection of Entities)
│   ├── MessageId
│   ├── SenderId
│   ├── Content (Value Object)
│   ├── SentAt (DateTime)
│   ├── ReadAt (DateTime)
│   └── EditedAt (DateTime)
└── ConversationStatus (Active, Archived)
```

**Domain Events**:
- `ConversationStarted`
- `MessageSent`
- `MessageRead`
- `MessageEdited`
- `MessageDeleted`
- `ConversationArchived`

**API Endpoints**:
```
POST   /api/conversations       # Start conversation
GET    /api/conversations       # List conversations
GET    /api/conversations/{id}  # Get conversation
POST   /api/conversations/{id}/messages
PATCH  /api/messages/{id}/read
PATCH  /api/messages/{id}/edit
DELETE /api/messages/{id}
```

**Database Tables**:
- conversations
- conversation_participants
- messages
- message_read_receipts

**WebSocket Events**:
- `message:new`
- `message:read`
- `user:typing`

---

### 5. Notification Context (Port 8005)

**Responsibility**: Email, push, SMS notifications

**Domain Model**:
```
Notification (Aggregate Root)
├── NotificationId (Value Object)
├── RecipientId (Foreign Reference)
├── Type (NotificationType Enum)
│   ├── BookingConfirmed
│   ├── MessageReceived
│   ├── PaymentReceived
│   └── ReviewPosted
├── Channel (Email, Push, SMS)
├── Content (Value Object)
├── Status (Sent, Failed, Pending)
└── SentAt (DateTime)
```

**Domain Events** (Consumed from other services):
- Listens to: `BookingConfirmed`, `MessageSent`, `PaymentProcessed`, etc.
- Emits: `NotificationSent`, `NotificationFailed`

**API Endpoints**:
```
GET    /api/notifications       # List notifications
PATCH  /api/notifications/mark-all-read
PATCH  /api/notifications/{id}/read
PUT    /api/notifications/preferences
```

**Database Tables**:
- notifications
- notification_preferences
- notification_delivery_log

---

### 6. Payment Context (Port 8006)

**Responsibility**: Payment processing, wallet, payouts

**Domain Model**:
```
Payment (Aggregate Root)
├── PaymentId (Value Object)
├── PayerId (Foreign Reference)
├── PayeeId (Foreign Reference)
├── Amount (Money Value Object)
├── StripePaymentIntent
├── Status (Enum: Pending, Succeeded, Failed, Refunded)
└── Metadata

TutorPayout (Aggregate Root)
├── PayoutId (Value Object)
├── TutorId (Foreign Reference)
├── Amount (Money Value Object)
├── Period (DateRange Value Object)
├── Status (Pending, Processing, Completed)
└── StripeTransferId
```

**Domain Events**:
- `PaymentRequested`
- `PaymentSucceeded`
- `PaymentFailed`
- `RefundProcessed`
- `PayoutInitiated`
- `PayoutCompleted`

**API Endpoints**:
```
POST   /api/payments            # Process payment
GET    /api/payments/{id}       # Get payment status
POST   /api/payments/{id}/refund
GET    /api/payouts             # List payouts (tutor)
POST   /api/payouts/initiate    # Request payout
```

**Database Tables**:
- payments
- refunds
- tutor_payouts
- stripe_webhooks_log

---

### 7. Review & Rating Context (Port 8007)

**Responsibility**: Reviews, ratings, feedback

**Domain Model**:
```
Review (Aggregate Root)
├── ReviewId (Value Object)
├── BookingId (Foreign Reference)
├── StudentId (Foreign Reference)
├── TutorId (Foreign Reference)
├── Rating (Value Object: 1-5 stars)
├── Comment (Value Object)
├── CreatedAt (DateTime)
└── Status (Published, Hidden, Flagged)
```

**Domain Events**:
- `ReviewPosted`
- `ReviewEdited`
- `ReviewFlagged`
- `ReviewHidden`

**API Endpoints**:
```
POST   /api/reviews             # Create review
GET    /api/reviews/tutor/{id}  # Get tutor reviews
GET    /api/reviews/booking/{id}
PATCH  /api/reviews/{id}
DELETE /api/reviews/{id}
POST   /api/reviews/{id}/flag
```

**Database Tables**:
- reviews
- review_flags

---

## 🏗️ Service Communication Patterns

### Synchronous Communication (HTTP/gRPC)

**API Gateway Pattern**:
```
Client → API Gateway (Kong/Traefik)
         ↓
    Routes to appropriate service
         ↓
    Identity Service (auth check)
         ↓
    Target Service
```

**Service-to-Service Calls** (Minimal, use events instead):
```python
# ⚠️ AVOID: Direct HTTP calls between services
# Only use for:
# - Real-time validation
# - Critical reads (user exists check)

# Example: Booking service checks if tutor exists
async def validate_tutor_exists(tutor_id: int) -> bool:
    try:
        response = await http_client.get(
            f"{TUTOR_SERVICE_URL}/api/tutors/{tutor_id}",
            timeout=2.0  # Fail fast
        )
        return response.status_code == 200
    except Exception:
        # Fail closed
        raise ServiceUnavailableError("Tutor service unavailable")
```

### Asynchronous Communication (Event Bus)

**Kafka Topics**:
```yaml
Topics:
  - identity.events        # User registration, login, role changes
  - tutoring.events       # Profile updates, availability changes
  - booking.events        # Booking lifecycle events
  - messaging.events      # Messages, conversations
  - payment.events        # Payment, refund events
  - notification.events   # Notification delivery
  - review.events         # Reviews posted, ratings
```

**Event Publishing Example**:
```python
# Booking Service publishes event
from datetime import datetime
from dataclasses import dataclass

@dataclass
class BookingConfirmed:
    event_id: str
    booking_id: int
    student_id: int
    tutor_id: int
    scheduled_at: datetime
    amount: float
    occurred_at: datetime

# Publish
await event_bus.publish(
    topic="booking.events",
    event=BookingConfirmed(
        event_id=str(uuid.uuid4()),
        booking_id=booking.id,
        student_id=booking.student_id,
        tutor_id=booking.tutor_id,
        scheduled_at=booking.scheduled_at,
        amount=booking.amount,
        occurred_at=datetime.utcnow()
    )
)
```

**Event Consumption Example**:
```python
# Notification Service consumes event
@event_handler("booking.events", event_type="BookingConfirmed")
async def handle_booking_confirmed(event: BookingConfirmed):
    """Send confirmation emails when booking confirmed."""

    # Get user details from local projection/cache
    student = await get_user_projection(event.student_id)
    tutor = await get_user_projection(event.tutor_id)

    # Send emails
    await email_service.send(
        to=student.email,
        template="booking_confirmed_student",
        data={
            "tutor_name": tutor.name,
            "scheduled_at": event.scheduled_at,
            "booking_id": event.booking_id
        }
    )

    await email_service.send(
        to=tutor.email,
        template="booking_confirmed_tutor",
        data={
            "student_name": student.name,
            "scheduled_at": event.scheduled_at,
            "booking_id": event.booking_id
        }
    )
```

---

## 🗄️ Data Management Patterns

### Database per Service

**Each service owns its database**:
```yaml
Identity Service:
  database: identity_db
  schema: users, user_profiles, sessions

Tutoring Service:
  database: tutoring_db
  schema: tutor_profiles, subjects, availability

Booking Service:
  database: booking_db
  schema: bookings, payments, booking_snapshots

Messaging Service:
  database: messaging_db
  schema: conversations, messages
```

### Data Consistency Patterns

#### 1. Event Sourcing (Optional)

Store events instead of current state:

```python
# Event Store
class BookingEventStore:
    events = [
        {"type": "BookingRequested", "data": {...}, "timestamp": "..."},
        {"type": "PaymentProcessed", "data": {...}, "timestamp": "..."},
        {"type": "BookingConfirmed", "data": {...}, "timestamp": "..."},
    ]

    def rebuild_aggregate(self, booking_id):
        events = self.get_events(booking_id)
        booking = Booking()
        for event in events:
            booking.apply(event)
        return booking
```

#### 2. Saga Pattern (Distributed Transactions)

**Choreography-based Saga** (Event-driven):

```
Student books session:
  1. Booking Service: Create booking (status: Pending)
     → Emits: BookingRequested

  2. Payment Service: Listens to BookingRequested
     → Process payment
     → Emits: PaymentSucceeded OR PaymentFailed

  3. Booking Service: Listens to PaymentSucceeded
     → Update booking (status: Confirmed)
     → Emits: BookingConfirmed

  4. Notification Service: Listens to BookingConfirmed
     → Send confirmation emails

  5. Tutoring Service: Listens to BookingConfirmed
     → Update availability (mark time slot as booked)

Rollback on failure:
  If PaymentFailed:
    Booking Service: Mark booking as Failed
    Notification Service: Send payment failure email
```

**Orchestration-based Saga** (Centralized):

```python
# Booking Saga Orchestrator
class BookingSaga:
    async def execute(self, booking_request):
        booking = None
        payment = None

        try:
            # Step 1: Create booking
            booking = await booking_service.create(booking_request)

            # Step 2: Process payment
            payment = await payment_service.charge(
                amount=booking.amount,
                customer_id=booking.student_id
            )

            # Step 3: Confirm booking
            await booking_service.confirm(booking.id, payment.id)

            # Step 4: Update tutor availability
            await tutoring_service.block_time_slot(
                tutor_id=booking.tutor_id,
                time_slot=booking.scheduled_at
            )

            # Step 5: Send notifications
            await notification_service.send_booking_confirmation(booking.id)

        except PaymentFailedError:
            # Compensate: Cancel booking
            if booking:
                await booking_service.cancel(booking.id)
            raise

        except Exception as e:
            # Compensate: Refund payment and cancel booking
            if payment:
                await payment_service.refund(payment.id)
            if booking:
                await booking_service.cancel(booking.id)
            raise
```

#### 3. CQRS (Command Query Responsibility Segregation)

**Separate read and write models**:

```python
# Write Model (Commands)
class CreateBookingCommand:
    student_id: int
    tutor_id: int
    scheduled_at: datetime
    duration: int

class BookingCommandHandler:
    async def handle(self, command: CreateBookingCommand):
        # Validate
        # Create booking
        # Publish event
        pass

# Read Model (Queries - Denormalized)
class BookingListQuery:
    student_id: Optional[int]
    tutor_id: Optional[int]
    status: Optional[str]

class BookingReadModel:
    """Denormalized for fast queries."""
    id: int
    student_id: int
    student_name: str  # Denormalized!
    student_email: str  # Denormalized!
    tutor_id: int
    tutor_name: str  # Denormalized!
    tutor_email: str  # Denormalized!
    scheduled_at: datetime
    status: str
    amount: float

# Projection Builder (listens to events)
@event_handler("booking.events")
async def project_booking_read_model(event):
    """Build read model from events."""
    if event.type == "BookingConfirmed":
        # Fetch user data
        student = await identity_service.get_user(event.student_id)
        tutor = await identity_service.get_user(event.tutor_id)

        # Create denormalized read model
        await read_db.create(BookingReadModel(
            id=event.booking_id,
            student_id=event.student_id,
            student_name=student.name,
            student_email=student.email,
            tutor_id=event.tutor_id,
            tutor_name=tutor.name,
            tutor_email=tutor.email,
            scheduled_at=event.scheduled_at,
            status="confirmed",
            amount=event.amount
        ))
```

---

## 🔧 Technology Stack

### Service Framework
```yaml
Framework: FastAPI (Python 3.12)
API Protocol: REST + gRPC (for inter-service)
WebSockets: For real-time messaging
Validation: Pydantic
ORM: SQLAlchemy (per service)
```

### Event Bus
```yaml
Message Broker: Apache Kafka
  - High throughput
  - Persistent events
  - Event replay capability

Alternative: RabbitMQ
  - Simpler setup
  - Good for smaller scale
```

### API Gateway
```yaml
Gateway: Kong or Traefik
Features:
  - Request routing
  - Authentication (JWT validation)
  - Rate limiting
  - Load balancing
  - API versioning
```

### Service Discovery
```yaml
Discovery: Consul or etcd
Features:
  - Service registration
  - Health checking
  - Dynamic configuration
```

### Observability
```yaml
Metrics: Prometheus
Dashboards: Grafana
Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
Tracing: Jaeger or Zipkin
APM: Datadog or New Relic
```

### Container Orchestration
```yaml
Orchestrator: Kubernetes
Service Mesh: Istio or Linkerd
Features:
  - Auto-scaling
  - Traffic management
  - Circuit breaking
  - Retry logic
  - Canary deployments
```

---

## 📁 Project Structure (Per Service)

```
booking-service/
├── domain/                     # Domain layer (core business logic)
│   ├── model/
│   │   ├── booking.py         # Booking aggregate
│   │   ├── value_objects.py   # Money, DateRange, etc.
│   │   └── enums.py           # BookingStatus, etc.
│   │
│   ├── events/
│   │   ├── booking_requested.py
│   │   ├── booking_confirmed.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── booking_conflict_checker.py
│   │   └── refund_calculator.py
│   │
│   └── repositories/
│       └── booking_repository.py  # Interface (ABC)
│
├── application/                # Application layer (use cases)
│   ├── commands/
│   │   ├── create_booking.py
│   │   ├── confirm_booking.py
│   │   └── cancel_booking.py
│   │
│   ├── queries/
│   │   ├── get_booking.py
│   │   └── list_bookings.py
│   │
│   ├── handlers/
│   │   ├── command_handlers.py
│   │   └── query_handlers.py
│   │
│   └── event_handlers/
│       ├── payment_succeeded_handler.py
│       └── ...
│
├── infrastructure/             # Infrastructure layer
│   ├── persistence/
│   │   ├── sqlalchemy_booking_repository.py
│   │   ├── models.py          # SQLAlchemy models
│   │   └── database.py
│   │
│   ├── messaging/
│   │   ├── kafka_producer.py
│   │   ├── kafka_consumer.py
│   │   └── event_bus.py
│   │
│   └── external_services/
│       ├── identity_service_client.py
│       └── tutoring_service_client.py
│
├── presentation/               # Presentation layer (API)
│   ├── api/
│   │   ├── routes.py
│   │   ├── schemas.py         # Pydantic request/response
│   │   └── dependencies.py
│   │
│   └── grpc/                  # gRPC for inter-service
│       ├── booking_service.proto
│       └── booking_grpc.py
│
├── core/                       # Shared utilities
│   ├── config.py
│   ├── exceptions.py
│   ├── logging.py
│   └── utils.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── migrations/                 # Database migrations (Alembic)
├── main.py                     # Service entry point
├── Dockerfile
└── requirements.txt
```

---

## 🚀 Migration Timeline

### Week 1-2: Design & Planning
- ✅ Define bounded contexts
- ✅ Design domain models
- ✅ Design event schemas
- ✅ Design API contracts
- ✅ Choose technology stack

### Week 3-4: Infrastructure Setup
- Setup Kubernetes cluster
- Deploy Kafka cluster
- Setup API Gateway (Kong)
- Setup service discovery (Consul)
- Setup monitoring (Prometheus + Grafana)
- Setup centralized logging (ELK)

### Week 5-6: Identity Service
- Extract identity/auth code
- Implement DDD structure
- Create separate database
- Implement event publishing
- Deploy to Kubernetes
- Integration testing

### Week 7-8: Tutoring Service
- Extract tutor profile code
- Implement DDD structure
- Create separate database
- Listen to identity events (user projection)
- Deploy to Kubernetes

### Week 9-10: Booking Service
- Extract booking code
- Implement Saga pattern
- Create separate database
- Integrate with payment gateway
- Deploy to Kubernetes

### Week 11-12: Messaging & Notification Services
- Extract messaging code
- Implement WebSocket support
- Extract notification code
- Deploy both services

### Week 13-14: Payment & Review Services
- Extract payment processing
- Implement Stripe webhooks
- Extract review/rating code
- Deploy both services

### Week 15-16: Integration & Testing
- End-to-end testing
- Performance testing
- Security audits
- Documentation
- Gradual migration (strangler pattern)

---

## 📊 Deployment Architecture

```yaml
# Kubernetes deployment structure
namespaces:
  - edustream-services    # All microservices
  - edustream-infra       # Kafka, Redis, etc.
  - edustream-monitoring  # Prometheus, Grafana

services:
  identity-service:
    replicas: 3
    resources:
      cpu: "500m"
      memory: "512Mi"
    autoscaling:
      min: 3
      max: 10
      cpu_threshold: 70%

  booking-service:
    replicas: 3
    resources:
      cpu: "1000m"
      memory: "1Gi"
    autoscaling:
      min: 3
      max: 15
      cpu_threshold: 70%

  # ... other services

databases:
  # Each service has its own PostgreSQL instance
  identity-db:
    type: PostgreSQL 17
    storage: 20Gi
    backup: daily

  booking-db:
    type: PostgreSQL 17
    storage: 50Gi
    backup: hourly

  # ... other databases

message-broker:
  kafka:
    brokers: 3
    replication: 3
    partitions: 12
    retention: 7 days
```

---

## 🎯 Success Criteria

### Technical Metrics
- ✅ Each service < 5000 lines of code
- ✅ Each service independently deployable
- ✅ Each service has its own database
- ✅ No direct database access between services
- ✅ 95% test coverage per service
- ✅ API response time < 100ms (p95)
- ✅ Event processing latency < 1s (p99)

### Business Metrics
- ✅ Zero-downtime deployments
- ✅ Can scale individual services independently
- ✅ New features deploy in < 1 hour
- ✅ Mean time to recovery (MTTR) < 15 minutes

---

**Next Steps**: Review this plan and I'll provide detailed implementation for each service.
