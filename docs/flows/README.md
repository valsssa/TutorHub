# User Flow Documentation

Detailed documentation of user journeys and workflows in TutorHub.

---

## Overview

These documents describe complete user flows through the application, covering:
- Frontend UI interactions
- Backend API calls
- Database operations
- State management
- Error handling
- Edge cases

---

## User Flows

### 1. [Authentication Flow](./01_AUTHENTICATION_FLOW.md)
**User registration, login, and password management**

- User registration (email + password)
- Email verification
- Login with JWT token
- Password reset flow
- Session management
- Multi-device sessions

**Key Endpoints:**
- `POST /register`
- `POST /login`
- `POST /forgot-password`
- `POST /reset-password`
- `GET /users/me`

---

### 2. [Booking Flow](./02_BOOKING_FLOW.md)
**Session booking and management lifecycle**

- Browse available tutors
- View tutor availability
- Create booking request
- Payment processing (Stripe)
- Booking confirmation
- Booking cancellation & refunds
- Booking status tracking

**Key Endpoints:**
- `GET /tutors`
- `POST /bookings`
- `GET /bookings/{id}`
- `PATCH /bookings/{id}`
- `POST /bookings/{id}/cancel`

**Statuses:** `pending`, `confirmed`, `completed`, `cancelled`, `refunded`

---

### 3. [Messaging Flow](./03_MESSAGING_FLOW.md)
**Real-time messaging between students and tutors**

- Conversation creation
- Send/receive messages
- Read receipts
- Message notifications
- Conversation archiving
- Search messages

**Key Endpoints:**
- `POST /conversations`
- `GET /conversations`
- `POST /conversations/{id}/messages`
- `GET /conversations/{id}/messages`

---

### 4. [Tutor Onboarding Flow](./04_TUTOR_ONBOARDING_FLOW.md)
**Tutor profile creation and verification**

- Profile setup
- Expertise/subjects selection
- Availability schedule configuration
- Rate setting
- Bio and profile picture upload
- Admin verification process

**Key Endpoints:**
- `POST /tutors/onboarding`
- `PATCH /users/me`
- `POST /upload/avatar`
- `PATCH /tutors/{id}/verify` (admin only)

---

### 5. [Student Profile Flow](./05_STUDENT_PROFILE_FLOW.md)
**Student profile management**

- Profile creation
- Personal information update
- Learning preferences
- Saved tutors/favorites
- Booking history
- Profile settings

**Key Endpoints:**
- `GET /users/me`
- `PATCH /users/me`
- `GET /bookings` (with filters)
- `POST /saved-tutors`

---

### 6. [Admin Dashboard Flow](./06_ADMIN_DASHBOARD_FLOW.md)
**Admin panel operations and management**

- User management (view, edit, delete)
- Role assignment (student → tutor, admin)
- Tutor verification
- Booking oversight
- Platform analytics
- System configuration

**Key Endpoints:**
- `GET /admin/users`
- `PATCH /admin/users/{id}`
- `DELETE /admin/users/{id}`
- `GET /admin/analytics`
- `PATCH /tutors/{id}/verify`

---

## Reading These Documents

Each flow document follows this structure:

1. **Overview** - High-level description
2. **User Journey** - Step-by-step user actions
3. **Frontend Components** - UI components involved
4. **API Calls** - Backend endpoints called
5. **Database Operations** - Data persistence
6. **State Management** - React state/context usage
7. **Error Handling** - Error scenarios and handling
8. **Edge Cases** - Special scenarios
9. **Security Considerations** - Auth and validation
10. **Testing** - Test coverage for the flow

---

## Flow Diagrams

For visual representations of these flows:

```
[User Action] → [Frontend Component] → [API Call] → [Backend Logic] → [Database]
```

Example - Login Flow:
```
User enters credentials
  ↓
LoginPage component
  ↓
POST /login
  ↓
Validate credentials, generate JWT
  ↓
Save session, return token
  ↓
Store token in cookies
  ↓
Redirect to dashboard
```

---

## Common Patterns

### Authentication Pattern
All protected flows follow this pattern:
1. Check for valid JWT token
2. Redirect to login if missing/invalid
3. Fetch current user data
4. Render protected content

### API Call Pattern
```typescript
try {
  const response = await axios.post('/api/endpoint', data, {
    headers: { Authorization: `Bearer ${token}` }
  })
  // Handle success
} catch (error) {
  // Handle error
  showError('Operation failed')
}
```

### State Management Pattern
```typescript
const [user, setUser] = useState(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
```

---

## Related Documentation

- **[API Reference](../API_REFERENCE.md)** - Complete API documentation
- **[Database Architecture](../architecture/DATABASE_ARCHITECTURE.md)** - Database schema
- **[Frontend-Backend Mapping](../FRONTEND_BACKEND_API_MAPPING.md)** - API integration
- **[User Roles](../USER_ROLES.md)** - Role-based access control
- **[Testing Guide](../testing/TESTING_GUIDE.md)** - How to test these flows

---

## Contributing

When updating flows:
1. Keep diagrams and code examples current
2. Update related API documentation
3. Add new edge cases as discovered
4. Include test scenarios

---

**Last Updated**: 2026-01-28
