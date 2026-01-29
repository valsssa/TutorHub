# E2E and Integration Tests

## Overview

This directory contains two types of comprehensive tests:

1. **Integration Tests** (`test_e2e_booking.py`) - Using FastAPI TestClient
2. **True E2E Tests** (`test_e2e_admin.py`) - Using HTTP requests to deployed API

---

## Test Types

### Integration Tests (test_e2e_booking.py)

**Purpose:** Test complete workflows using FastAPI TestClient with in-memory database.

**Characteristics:**
- ✅ Uses consolidated test infrastructure from `tests/conftest.py`
- ✅ Fast execution (in-memory SQLite database)
- ✅ Automatic database cleanup between tests
- ✅ No external dependencies
- ✅ Suitable for CI/CD pipelines
- ✅ Tests complete user workflows (booking lifecycle, etc.)

**Fixtures Used:**
- `client` - FastAPI TestClient
- `db_session` - Database session
- `tutor_user`, `student_user`, `admin_user` - Pre-created test users
- `tutor_token`, `student_token`, `admin_token` - JWT tokens

**Example:**
```python
def test_booking_workflow(client, tutor_token, student_token):
    # Test uses TestClient, not real HTTP
    response = client.post("/api/bookings", json=..., headers=...)
    assert response.status_code == 201
```

**Run:**
```bash
# From repo root
pytest backend/tests/test_e2e_booking.py -v

# With Docker
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
```

---

### True E2E Tests (test_e2e_admin.py)

**Purpose:** Test real API endpoints on deployed staging/production environments.

**Characteristics:**
- ✅ Uses `requests` library for real HTTP calls
- ✅ Tests against actual deployed API (staging/production)
- ✅ Requires API to be running
- ✅ Tests real network, authentication, database
- ✅ Slower but more realistic
- ⚠️  Requires cleanup of test data

**Configuration:**
```python
API_URL = os.getenv("API_URL", "https://api.valsa.solutions")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://edustream.valsa.solutions")
```

**Example:**
```python
def test_admin_workflow(self):
    # Real HTTP request to deployed API
    response = requests.post(
        f"{self.api_url}/api/admin/users",
        json=...,
        headers={"Authorization": f"Bearer {self.admin_token}"}
    )
    assert response.status_code == 200
```

**Run:**
```bash
# Against staging
API_URL=https://api-staging.valsa.solutions pytest backend/tests/test_e2e_admin.py -v

# Against production (use with caution!)
API_URL=https://api.valsa.solutions pytest backend/tests/test_e2e_admin.py -v
```

---

## Test Coverage

### Integration Tests (test_e2e_booking.py)

✅ **Implemented:**
1. `test_tutor_profile_setup_and_booking_lifecycle`
   - Tutor creates profile
   - Student searches tutors
   - Student creates booking
   - Tutor confirms booking
   - Both parties view updated status

2. `test_booking_validation_subject_not_offered`
   - Validates subject constraints
   - Rejects invalid subjects

3. `test_booking_cancellation_workflow`
   - Student cancels within free cancellation window
   - Verifies cancelled status

4. `test_booking_time_conflict_prevention`
   - Prevents double-booking same time slot
   - Tests conflict handling

5. `test_booking_timezone_handling`
   - Validates timezone conversion
   - Tests cross-timezone bookings

🔄 **Placeholders (to implement):**
- `test_booking_authorization` - Role-based access control
- `test_booking_with_package_credits` - Package-based bookings

---

### True E2E Tests (test_e2e_admin.py)

✅ **Implemented:**
1. `test_complete_admin_workflow_create_user`
   - Create user
   - Update email
   - Change roles (admin/tutor/student)
   - Deactivate/reactivate
   - Reset password
   - Delete user

2. `test_admin_self_protection_workflow`
   - Admin cannot demote self
   - Admin cannot deactivate self
   - Admin cannot delete self

3. `test_regular_user_cannot_access_admin_endpoints`
   - List users (403)
   - Update users (403)
   - Delete users (403)
   - Reset passwords (403)

4. `test_unauthenticated_access_denied`
   - All admin endpoints require auth (401)

5. `test_invalid_inputs_rejected`
   - Invalid email format (422)
   - Invalid role (400)
   - Password too short (400)
   - Non-existent user (404)

6. `test_email_uniqueness_enforced`
   - Cannot register duplicate email
   - Cannot update to existing email

7. `test_multi_field_update`
   - Update multiple fields simultaneously
   - Verify all fields updated correctly

8. `test_concurrent_admin_operations`
   - Multiple rapid updates
   - No data corruption

---

## Recent Updates (2026-01-28)

### ✅ Fixed Issues

1. **Endpoint Updates**
   - ❌ OLD: `/token`
   - ✅ NEW: `/api/auth/login`
   - ❌ OLD: `/register`
   - ✅ NEW: `/api/auth/register`

2. **Test Infrastructure**
   - ✅ Updated integration tests to use consolidated `tests/conftest.py`
   - ✅ Removed duplicate database setup code
   - ✅ Removed duplicate user creation functions
   - ✅ Now uses shared fixtures: `client`, `tutor_token`, `student_token`, etc.

3. **Test Improvements**
   - ✅ Added pagination handling for booking lists
   - ✅ Updated to use new four-field status system (session_state, session_outcome, payment_state, dispute_state)
   - ✅ Added better error messages in assertions
   - ✅ Added timezone handling tests
   - ✅ Added state machine tests for booking transitions

---

## Test Naming Convention

### Integration Tests
```python
def test_<feature>_<scenario>(<fixtures>):
    """
    Test <what it does>.

    Steps:
    1. Setup
    2. Action
    3. Verification
    """
```

### E2E Tests
```python
def test_<workflow>_<aspect>(self):
    """
    Test <user story or workflow>.

    Verifies:
    - Expected behavior
    - Error handling
    - Security
    """
```

---

## Best Practices

### ✅ DO

- **Integration Tests:**
  - Use fixtures from consolidated conftest
  - Test complete workflows, not individual endpoints
  - Handle both paginated and non-paginated responses
  - Check multiple status formats (uppercase/lowercase)
  - Add descriptive assertion messages

- **E2E Tests:**
  - Clean up test data in finally blocks
  - Use environment variables for API URLs
  - Test both happy path and error cases
  - Verify security (auth, authorization)
  - Test edge cases (empty strings, null, etc.)

### ❌ DON'T

- **Integration Tests:**
  - Don't duplicate test infrastructure (use conftest)
  - Don't hardcode URLs (use relative paths)
  - Don't leave test data in database
  - Don't assume specific database IDs

- **E2E Tests:**
  - Don't run against production without review
  - Don't leave test users in production database
  - Don't hardcode API URLs in code
  - Don't skip cleanup steps

---

## Running Tests

### All Integration Tests
```bash
pytest backend/tests/test_e2e_booking.py -v
```

### Specific Integration Test
```bash
pytest backend/tests/test_e2e_booking.py::test_tutor_profile_setup_and_booking_lifecycle -v
```

### All E2E Tests (Staging)
```bash
API_URL=https://api-staging.valsa.solutions \
FRONTEND_URL=https://staging.valsa.solutions \
pytest backend/tests/test_e2e_admin.py -v
```

### Specific E2E Test
```bash
API_URL=https://api-staging.valsa.solutions \
pytest backend/tests/test_e2e_admin.py::TestAdminWorkflows::test_complete_admin_workflow_create_user -v
```

### With Docker (Integration Tests Only)
```bash
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
```

---

## Troubleshooting

### Integration Tests

**Issue:** Fixture not found
```
Solution: Ensure using consolidated conftest from tests/conftest.py
Check: backend/tests/conftest.py imports from root tests/
```

**Issue:** Database errors
```
Solution: Tests auto-create/drop database
Check: setup_database fixture is working (autouse=True)
```

**Issue:** Token authentication fails
```
Solution: Use token fixtures, not manual login
Example: Use tutor_token fixture, not manual /api/auth/login call
```

### E2E Tests

**Issue:** Connection refused
```
Solution: Ensure API server is running
Check: API_URL environment variable is correct
```

**Issue:** 401 Unauthorized
```
Solution: Check default credentials in setup()
Default admin: admin@example.com / admin123
Default student: student@example.com / student123
```

**Issue:** Test data not cleaning up
```
Solution: Use try/finally blocks in tests
Always delete test users at end of test
```

---

## Adding New Tests

### Integration Test Template

```python
def test_new_feature_workflow(client, tutor_token, student_token, db_session):
    """
    Test [describe workflow].

    Steps:
    1. [Setup step]
    2. [Action step]
    3. [Verification step]
    """
    # Setup
    # ...

    # Action
    response = client.post(
        "/api/endpoint",
        json={...},
        headers={"Authorization": f"Bearer {student_token}"}
    )

    # Verify
    assert response.status_code == 201
    data = response.json()
    assert data["expected_field"] == "expected_value"
```

### E2E Test Template

```python
def test_new_workflow(self):
    """
    Test [describe user workflow].

    Verifies:
    - [Expected behavior 1]
    - [Expected behavior 2]
    """
    # Create test data
    response = requests.post(
        f"{self.api_url}/api/resource",
        json={...},
        headers=self.get_headers(self.admin_token)
    )
    assert response.status_code == 201
    resource_id = response.json()["id"]

    try:
        # Perform workflow steps
        # ...

        # Verify results
        # ...

    finally:
        # Cleanup
        requests.delete(
            f"{self.api_url}/api/resource/{resource_id}",
            headers=self.get_headers(self.admin_token)
        )
```

---

## Continuous Integration

### GitHub Actions / GitLab CI

```yaml
test:
  stage: test
  script:
    - docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
  # Integration tests run automatically

e2e-staging:
  stage: e2e
  only:
    - develop
  script:
    - API_URL=$STAGING_API_URL pytest backend/tests/test_e2e_admin.py -v
  # E2E tests against staging before merge
```

---

## Test Data Management

### Integration Tests
- ✅ Automatic cleanup (database drops after each test)
- ✅ Isolated test data per test function
- ✅ No manual cleanup needed

### E2E Tests
- ⚠️  Manual cleanup required
- ⚠️  Use try/finally blocks
- ⚠️  Delete created test users
- ⚠️  Clean up test bookings, reviews, etc.

---

## Booking Status System

Bookings use a four-field status system. Tests should check these fields:

| Field | Values |
|-------|--------|
| `session_state` | REQUESTED, SCHEDULED, ACTIVE, ENDED, CANCELLED, EXPIRED |
| `session_outcome` | COMPLETED, NOT_HELD, NO_SHOW_STUDENT, NO_SHOW_TUTOR (null if not ended) |
| `payment_state` | PENDING, AUTHORIZED, CAPTURED, VOIDED, REFUNDED, PARTIALLY_REFUNDED |
| `dispute_state` | NONE, OPEN, RESOLVED_UPHELD, RESOLVED_REFUNDED |

The legacy `status` field is still returned for backward compatibility.

**See:** `backend/modules/bookings/domain/status.py` for enum definitions.

---

## Related Documentation

- `tests/README.md` - Test infrastructure documentation
- `tests/conftest.py` - Consolidated test fixtures
- `docs/flows/02_BOOKING_FLOW.md` - Booking flow and status documentation
- `CLAUDE.md` - Project development guidelines
- `docker-compose.test.yml` - Test environment configuration

---

**Last Updated:** 2026-01-29
**Status:** ✅ E2E tests updated for four-field booking status system
**Coverage:** Booking workflows + Admin workflows + State machine tests
