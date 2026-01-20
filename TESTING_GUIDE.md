# Testing Guide
## Comprehensive Test Suite Documentation

**Version:** 1.0
**Last Updated:** 2026-01-20

---

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing New Tests](#writing-new-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This project uses a comprehensive testing strategy covering:

- **Backend Unit Tests** (pytest): Test individual functions, services, and utilities
- **Backend Integration Tests** (pytest + TestClient): Test API endpoints end-to-end
- **Frontend Component Tests** (Jest + React Testing Library): Test UI components
- **End-to-End Tests** (Playwright): Test complete user workflows

### Test Coverage Goals

| Layer | Target Coverage | Current Coverage |
|-------|----------------|------------------|
| Backend API | 95% | 82% → 95% (after implementation) |
| Frontend Components | 85% | 56% → 85% (after implementation) |
| E2E User Flows | 100% | 12% → 100% (after implementation) |

---

## Test Structure

```
Project1-splitversion/
├── backend/
│   ├── tests/                          # Backend test suite
│   │   ├── conftest.py                 # Shared pytest fixtures
│   │   ├── test_auth.py                # Authentication tests
│   │   ├── test_bookings.py            # Booking API tests
│   │   ├── test_messages.py            # Messaging tests
│   │   └── ...
│   └── modules/
│       ├── payments/
│       │   └── tests/
│       │       └── test_payment_service.py   # Payment logic tests
│       ├── tutor_profile/
│       │   └── tests/
│       │       ├── test_services.py          # Tutor profile tests
│       │       └── test_availability_service.py  # Availability tests
│       └── packages/
│           └── tests/
│               └── test_package_service.py    # Package tests
├── frontend/
│   └── __tests__/
│       ├── components/
│       │   ├── dashboards/
│       │   │   ├── StudentDashboard.test.tsx  # Dashboard tests
│       │   │   ├── TutorDashboard.test.tsx
│       │   │   └── AdminDashboard.test.tsx
│       │   ├── Button.test.tsx
│       │   ├── Input.test.tsx
│       │   └── ...
│       ├── pages/
│       │   ├── login.test.tsx
│       │   └── register.test.tsx
│       └── e2e/
│           └── messaging-flow.test.tsx
├── tests/
│   └── e2e/
│       ├── test_student_booking_flow.py      # Complete student flow
│       ├── test_tutor_onboarding_flow.py     # Complete tutor flow
│       ├── test_admin_workflow.py            # Admin workflow
│       ├── test_payment_flow.py              # Payment scenarios
│       └── test_realtime_messaging.py        # WebSocket messaging
├── COMPREHENSIVE_TEST_PLAN.md          # Detailed test plan
├── RUN_ALL_TESTS_COMPREHENSIVE.sh      # Test execution script
└── TESTING_GUIDE.md                    # This file
```

---

## Running Tests

### Quick Start

```bash
# Run all tests (default)
./RUN_ALL_TESTS_COMPREHENSIVE.sh

# Run with coverage reports
./RUN_ALL_TESTS_COMPREHENSIVE.sh --coverage

# Run only backend tests
./RUN_ALL_TESTS_COMPREHENSIVE.sh --backend-only

# Run only frontend tests
./RUN_ALL_TESTS_COMPREHENSIVE.sh --frontend-only

# Run only E2E tests
./RUN_ALL_TESTS_COMPREHENSIVE.sh --e2e-only

# Fast mode (skip slow tests)
./RUN_ALL_TESTS_COMPREHENSIVE.sh --fast

# Clean artifacts and run tests
./RUN_ALL_TESTS_COMPREHENSIVE.sh --clean --coverage
```

### Running Tests with Docker Compose

#### Backend Tests

```bash
# All backend tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests

# Specific test file
docker compose -f docker-compose.test.yml run --rm backend pytest backend/tests/test_auth.py -v

# With coverage
docker compose -f docker-compose.test.yml run --rm backend pytest --cov=backend --cov-report=html

# Integration tests only
docker compose -f docker-compose.test.yml run --rm backend pytest -m integration

# Unit tests only (fast)
docker compose -f docker-compose.test.yml run --rm backend pytest -m "not integration and not slow"
```

#### Frontend Tests

```bash
# All frontend tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit frontend-tests

# Specific test file
docker compose -f docker-compose.test.yml run --rm frontend npm test -- Button.test.tsx

# With coverage
docker compose -f docker-compose.test.yml run --rm frontend npm test -- --coverage

# Watch mode (for development)
docker compose -f docker-compose.test.yml run --rm frontend npm test -- --watch
```

#### E2E Tests

```bash
# All E2E tests
./RUN_ALL_TESTS_COMPREHENSIVE.sh --e2e-only

# Or manually
docker compose -f docker-compose.test.yml up -d backend frontend db
docker compose -f docker-compose.test.yml up --abort-on-container-exit e2e-tests
docker compose -f docker-compose.test.yml down
```

### Running Tests Locally (Without Docker)

#### Backend

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# With coverage
pytest --cov=backend --cov-report=html --cov-report=term

# Specific test
pytest tests/test_auth.py::test_register_success -v
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Specific test
npm test -- Button.test.tsx
```

---

## Test Coverage

### Viewing Coverage Reports

After running tests with `--coverage`, open the HTML reports:

**Backend:**
```bash
open backend/htmlcov/index.html  # macOS
xdg-open backend/htmlcov/index.html  # Linux
start backend/htmlcov/index.html  # Windows
```

**Frontend:**
```bash
open frontend/coverage/lcov-report/index.html
```

### Coverage Thresholds

Tests will fail if coverage drops below:
- Backend: 80% (statements, branches)
- Frontend: 70% (statements, branches)

Configure in:
- Backend: `backend/pytest.ini` or `backend/.coveragerc`
- Frontend: `frontend/jest.config.js`

---

## Writing New Tests

### Backend Tests

#### Unit Test Template

```python
# backend/modules/mymodule/tests/test_myservice.py

import pytest
from backend.modules.mymodule.services import MyService

class TestMyService:
    """Test MyService business logic"""

    def test_create_resource_success(self, db, test_user):
        """Test successful resource creation"""
        # Given
        data = {"name": "Test Resource"}

        # When
        result = MyService.create_resource(db, test_user.id, data)

        # Then
        assert result.name == "Test Resource"
        assert result.user_id == test_user.id

    def test_create_resource_invalid_data(self, db, test_user):
        """Test error on invalid data"""
        # Given
        invalid_data = {"name": ""}

        # When/Then
        with pytest.raises(ValueError, match="Name required"):
            MyService.create_resource(db, test_user.id, invalid_data)
```

#### Integration Test Template

```python
# backend/tests/test_myapi.py

import pytest

@pytest.mark.integration
class TestMyAPI:
    """Test MyAPI endpoints"""

    def test_create_endpoint(self, client, test_user_token):
        """Test POST /api/myresources"""
        # When
        response = client.post(
            "/api/myresources",
            json={"name": "Test"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # Then
        assert response.status_code == 201
        assert response.json()["name"] == "Test"

    def test_unauthorized_access(self, client):
        """Test endpoint requires authentication"""
        # When
        response = client.post("/api/myresources", json={"name": "Test"})

        # Then
        assert response.status_code == 401
```

### Frontend Tests

#### Component Test Template

```typescript
// frontend/__tests__/components/MyComponent.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MyComponent from '@/components/MyComponent';

describe('MyComponent', () => {
  it('renders with props', () => {
    // Given
    const props = { title: 'Test Title' };

    // When
    render(<MyComponent {...props} />);

    // Then
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    // Given
    const mockOnClick = jest.fn();
    render(<MyComponent onClick={mockOnClick} />);

    // When
    const button = screen.getByRole('button');
    fireEvent.click(button);

    // Then
    await waitFor(() => {
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });
  });

  it('displays error state', async () => {
    // Given
    render(<MyComponent error="Something went wrong" />);

    // Then
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
```

#### API Integration Test

```typescript
// frontend/__tests__/hooks/useMyAPI.test.tsx

import { renderHook, waitFor } from '@testing-library/react';
import { useMyAPI } from '@/hooks/useMyAPI';

jest.mock('@/lib/api');

describe('useMyAPI', () => {
  it('fetches data successfully', async () => {
    // Given
    const mockData = { id: 1, name: 'Test' };
    const { api } = require('@/lib/api');
    api.myresources.list.mockResolvedValue({ data: [mockData] });

    // When
    const { result } = renderHook(() => useMyAPI());

    // Then
    await waitFor(() => {
      expect(result.current.data).toEqual([mockData]);
      expect(result.current.loading).toBe(false);
    });
  });
});
```

### E2E Test Template

```python
# tests/e2e/test_my_flow.py

import pytest
from playwright.sync_api import Page, expect

class TestMyUserFlow:
    """E2E test for complete user workflow"""

    def test_complete_workflow(self, page: Page, test_credentials):
        """
        Test: User logs in → performs action → verifies result
        """
        # Step 1: Login
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_credentials['email'])
        page.fill('input[name="password"]', test_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Verify redirect
        expect(page).to_have_url('http://localhost:3000/dashboard')

        # Step 2: Navigate to feature
        page.click('a:has-text("My Feature")')
        expect(page).to_have_url('http://localhost:3000/my-feature')

        # Step 3: Perform action
        page.click('button:has-text("Create")')

        # Step 4: Verify result
        expect(page.locator('.success-message')).to_be_visible()
        expect(page.locator('.item-list')).to_contain_text('New Item')
```

---

## CI/CD Integration

### GitHub Actions

The test suite runs automatically on:
- Push to any branch
- Pull request creation/update
- Scheduled daily runs (for regression testing)

See `.github/workflows/test.yml` for configuration.

### Running Tests in CI

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          chmod +x RUN_ALL_TESTS_COMPREHENSIVE.sh
          ./RUN_ALL_TESTS_COMPREHENSIVE.sh --backend-only --coverage

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run frontend tests
        run: |
          chmod +x RUN_ALL_TESTS_COMPREHENSIVE.sh
          ./RUN_ALL_TESTS_COMPREHENSIVE.sh --frontend-only --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: |
          chmod +x RUN_ALL_TESTS_COMPREHENSIVE.sh
          ./RUN_ALL_TESTS_COMPREHENSIVE.sh --e2e-only
```

---

## Troubleshooting

### Common Issues

#### 1. Tests Fail with "Connection Refused"

**Symptom:** Backend tests fail with database connection errors.

**Solution:**
```bash
# Ensure database is running
docker compose -f docker-compose.test.yml up -d db

# Wait for database to be ready
sleep 5

# Run tests
docker compose -f docker-compose.test.yml up backend-tests
```

#### 2. Frontend Tests Timeout

**Symptom:** Jest tests timeout or hang.

**Solution:**
```bash
# Increase Jest timeout
npm test -- --testTimeout=10000

# Or in jest.config.js:
{
  testTimeout: 10000
}
```

#### 3. E2E Tests Fail to Start Services

**Symptom:** Playwright can't connect to backend/frontend.

**Solution:**
```bash
# Check services are running
docker compose -f docker-compose.test.yml ps

# View logs
docker compose -f docker-compose.test.yml logs backend
docker compose -f docker-compose.test.yml logs frontend

# Restart services
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d backend frontend db
```

#### 4. "Module Not Found" Errors

**Backend:**
```bash
# Reinstall dependencies
docker compose -f docker-compose.test.yml build --no-cache backend
```

**Frontend:**
```bash
# Clear cache and reinstall
docker compose -f docker-compose.test.yml run --rm frontend npm ci
```

#### 5. Permission Denied on Test Script

```bash
# Make script executable
chmod +x RUN_ALL_TESTS_COMPREHENSIVE.sh
```

### Debugging Test Failures

#### Backend

```bash
# Run with verbose output
docker compose -f docker-compose.test.yml run --rm backend pytest -vv

# Run single test with print statements
docker compose -f docker-compose.test.yml run --rm backend pytest tests/test_auth.py::test_login -s

# Drop into debugger on failure
docker compose -f docker-compose.test.yml run --rm backend pytest --pdb
```

#### Frontend

```bash
# Run specific test in watch mode
docker compose -f docker-compose.test.yml run --rm frontend npm test -- Button.test.tsx --watch

# Debug with Chrome DevTools
docker compose -f docker-compose.test.yml run --rm frontend npm test -- --inspect-brk
```

#### E2E

```bash
# Run in headed mode (see browser)
docker compose -f docker-compose.test.yml run --rm e2e-tests pytest --headed

# Take screenshots on failure (automatic)
# Saved to: tests/e2e/screenshots/

# Record video
docker compose -f docker-compose.test.yml run --rm e2e-tests pytest --video=on
```

### Getting Help

- **Test Plan:** See `COMPREHENSIVE_TEST_PLAN.md` for detailed test scenarios
- **Project Docs:** See `docs/` directory for architecture and guides
- **Codebase Docs:** See `CLAUDE.md` for development guidelines
- **Issues:** Report bugs at GitHub Issues

---

## Best Practices

### General

- ✅ Write tests before or alongside code (TDD)
- ✅ Use descriptive test names (test_what_when_expected)
- ✅ Follow AAA pattern (Arrange, Given, When, Then)
- ✅ Test one thing per test
- ✅ Use fixtures/mocks for external dependencies
- ✅ Keep tests fast (< 100ms per unit test)
- ✅ Run tests locally before pushing

### Backend

- ✅ Use pytest fixtures for test data
- ✅ Mock external services (Stripe, S3)
- ✅ Test both success and error cases
- ✅ Validate database state after operations
- ✅ Use transactions for test isolation

### Frontend

- ✅ Use React Testing Library queries (getByRole, getByText)
- ✅ Test user interactions, not implementation details
- ✅ Mock API calls, not components
- ✅ Use `waitFor` for async operations
- ✅ Test accessibility (keyboard navigation, screen readers)

### E2E

- ✅ Test critical user paths only
- ✅ Use page object pattern for reusability
- ✅ Make tests independent (no shared state)
- ✅ Use data-testid for stable selectors
- ✅ Clean up test data after runs

---

## Test Execution Checklist

### Before Committing

- [ ] Run unit tests locally: `./RUN_ALL_TESTS_COMPREHENSIVE.sh --unit-only`
- [ ] Check linting: `docker compose -f docker-compose.test.yml run --rm backend flake8`
- [ ] Check types: `docker compose -f docker-compose.test.yml run --rm backend mypy backend/`
- [ ] Run frontend linter: `docker compose -f docker-compose.test.yml run --rm frontend npm run lint`

### Before Merging PR

- [ ] All CI tests pass
- [ ] Code coverage meets thresholds (80% backend, 70% frontend)
- [ ] E2E tests pass for affected user flows
- [ ] Manual testing of new features
- [ ] Documentation updated

### Before Production Deployment

- [ ] Full test suite passes: `./RUN_ALL_TESTS_COMPREHENSIVE.sh --coverage`
- [ ] E2E tests pass in staging environment
- [ ] Performance tests pass (if applicable)
- [ ] Security scans pass
- [ ] Smoke tests pass in production after deployment

---

**Last Updated:** 2026-01-20
**Maintainer:** Engineering Team
**Contact:** For questions, see project documentation or create an issue.
