# Test Infrastructure

## Overview

This directory contains the **consolidated test configuration** for the entire project. The `conftest.py` file provides shared pytest fixtures and utilities for both backend and frontend tests.

## Consolidation (2026-01-28)

Previously, test configuration was duplicated across:
- `tests/conftest.py` (root level tests)
- `backend/tests/conftest.py` (backend-specific tests)

This duplication has been **eliminated** by consolidating all test infrastructure into a single `tests/conftest.py` file. The backend conftest now simply re-exports fixtures from the root conftest for backward compatibility.

## Available Fixtures

### Core Fixtures

- **`setup_database`** (autouse) - Creates fresh database schema for each test
- **`db_session`** - Database session for direct database operations
- **`db`** - Alias for `db_session` (backward compatibility)
- **`client`** - FastAPI TestClient with database setup

### User Fixtures

- **`admin_user`** - Admin user (admin@test.com / admin123)
- **`tutor_user`** - Tutor user with profile (tutor@test.com / tutor123)
- **`student_user`** - Student user (student@test.com / student123)

### Token Fixtures (Login-based)

Use these for integration tests that test the full login flow:

- **`admin_token`** - JWT token via login endpoint
- **`tutor_token`** - JWT token via login endpoint
- **`student_token`** - JWT token via login endpoint

### Token Fixtures (Direct)

Use these for unit tests that don't need to test the login endpoint:

- **`admin_token_direct`** - JWT token directly from TokenManager
- **`tutor_token_direct`** - JWT token directly from TokenManager
- **`student_token_direct`** - JWT token directly from TokenManager

### Data Fixtures

- **`test_subject`** - Mathematics subject
- **`test_booking`** - Sample booking between tutor and student

### Legacy Fixtures

- **`test_student_token`** - Creates student@example.com and returns token
- **`test_tutor_token`** - Creates tutor@example.com and returns token

## Utility Functions

### `create_test_user(db, email, password, role, first_name="Test", last_name="User")`

Unified function to create test users. Automatically creates student profiles for student role.

**Example:**
```python
def test_custom_user(db_session):
    user = create_test_user(
        db_session,
        email="custom@test.com",
        password="password",
        role="student",
        first_name="Custom",
        last_name="User"
    )
    assert user.email == "custom@test.com"
```

### `create_test_tutor_profile(db, user_id, hourly_rate=50.00)`

Create a minimal approved tutor profile for a user.

**Example:**
```python
def test_tutor_profile(db_session, student_user):
    # Convert student to tutor
    student_user.role = "tutor"
    db_session.commit()

    profile = create_test_tutor_profile(db_session, student_user.id)
    assert profile.is_approved == True
```

## Usage Examples

### Basic Test with Database

```python
def test_create_user(db_session):
    """Test user creation."""
    user = create_test_user(
        db_session,
        email="test@example.com",
        password="password",
        role="student"
    )
    assert user.id is not None
    assert user.email == "test@example.com"
```

### Integration Test with Client

```python
def test_login_endpoint(client, student_user):
    """Test login endpoint."""
    response = client.post(
        "/api/auth/login",
        data={"username": "student@test.com", "password": "student123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Authenticated Request

```python
def test_protected_endpoint(client, student_token):
    """Test protected endpoint with authentication."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "student@test.com"
```

### Unit Test with Direct Token

```python
def test_token_validation(student_token_direct):
    """Test token validation without HTTP."""
    from core.security import TokenManager

    payload = TokenManager.decode_token(student_token_direct)
    assert payload["sub"] == "student@test.com"
```

## Configuration

The test infrastructure automatically:

1. **Sets up SQLite in-memory database** for speed
2. **Enables foreign key constraints** for referential integrity
3. **Creates fresh schema** for each test (isolation)
4. **Overrides database dependency** to use test database
5. **Configures environment** (DATABASE_URL, SECRET_KEY, BCRYPT_ROUNDS)

## Database Setup

Each test function gets a **fresh database schema**:

```python
@pytest.fixture(autouse=True, scope="function")
def setup_database():
    """Create fresh schema for every test function."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)
```

This ensures:
- ✅ Test isolation (no state leakage)
- ✅ Fast execution (in-memory database)
- ✅ No need for cleanup code in tests

## Running Tests

### All Tests
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Backend Tests Only
```bash
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
```

### Specific Test File
```bash
# From repo root
pytest tests/test_favorites.py -v

# From backend directory
pytest tests/test_admin.py -v
```

### Specific Test Function
```bash
pytest tests/test_favorites.py::test_add_favorite_tutor -v
```

## Best Practices

### ✅ DO

- Use existing fixtures when possible
- Use `create_test_user()` for custom test users
- Use direct token fixtures for unit tests (faster)
- Use login-based token fixtures for integration tests (more realistic)
- Keep tests isolated (don't depend on other tests)

### ❌ DON'T

- Don't manually create database sessions
- Don't hardcode passwords (use fixtures)
- Don't share state between tests
- Don't mock the database (use the test database)
- Don't create duplicate fixture definitions

## Backward Compatibility

The `backend/tests/conftest.py` file re-exports all fixtures from this consolidated conftest. Existing tests continue to work without modification.

**Migration path:**
1. Existing tests: No changes needed (backward compatible)
2. New tests: Import directly from root `tests/conftest.py` or use fixtures automatically
3. Future: Consider deprecating `backend/tests/conftest.py` after full migration

## Benefits of Consolidation

1. **Single Source of Truth** - One place to update test configuration
2. **Consistency** - All tests use same fixtures and setup
3. **Maintainability** - Update once, applies everywhere
4. **Reduced Duplication** - Eliminated ~230 lines of duplicate code
5. **Better Documentation** - Centralized fixture documentation

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running tests from the correct directory:

```bash
# From repo root (recommended)
pytest tests/

# From backend directory
cd backend && pytest tests/
```

### Database Errors

If you see database errors, ensure the test database is properly cleaned up:

```python
# The setup_database fixture handles this automatically
# If issues persist, check for:
# 1. Foreign key constraint violations
# 2. Missing table/column migrations
# 3. Incorrect model relationships
```

### Fixture Not Found

If pytest can't find a fixture:

1. Check it's listed in the fixtures section above
2. Verify you're using the correct fixture name
3. Ensure `conftest.py` is in the test path

## Contributing

When adding new test fixtures:

1. Add to `tests/conftest.py` (not backend/tests/)
2. Document in this README
3. Export in `backend/tests/conftest.py` `__all__` list (if needed for backward compatibility)
4. Follow existing naming conventions
5. Include docstrings

---

**Last Updated:** 2026-01-28
**Consolidation:** Merged duplicate test infrastructure into single conftest
