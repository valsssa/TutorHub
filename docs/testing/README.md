# Testing Documentation

Complete testing strategy and guides for TutorHub.

---

## Overview

TutorHub uses a comprehensive testing strategy covering:
- **Unit Tests** - Individual functions and components
- **Integration Tests** - Component interactions
- **E2E Tests** - Full user workflows (Playwright)
- **API Tests** - Backend endpoint testing (pytest)

---

## Documentation Files

### [TESTING_GUIDE.md](./TESTING_GUIDE.md)
**Comprehensive testing strategy and best practices**

- Testing pyramid (unit → integration → E2E)
- Test organization and structure
- Mocking and fixtures
- Coverage requirements
- CI/CD integration
- Testing conventions

### [PLAYWRIGHT_GUIDE.md](./PLAYWRIGHT_GUIDE.md)
**Complete Playwright E2E testing guide**

- Playwright setup and configuration
- Writing E2E tests
- Page Object Model (POM) pattern
- Test fixtures and helpers
- Running tests in different browsers
- Debugging failed tests
- Visual regression testing
- Accessibility testing

### [PLAYWRIGHT_QUICK_START.md](./PLAYWRIGHT_QUICK_START.md)
**Quick setup guide for Playwright**

- Installation steps
- Basic test examples
- Running your first test
- Common commands
- Quick troubleshooting

### [PLAYWRIGHT_README.md](./PLAYWRIGHT_README.md)
**Detailed Playwright implementation documentation**

- Project-specific Playwright configuration
- Custom fixtures and utilities
- Test data management
- Authentication helpers
- API mocking strategies
- Performance testing

---

## Quick Start

### Run All Tests
```bash
# Full test suite (lint + unit + E2E)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Backend Tests (pytest)
```bash
# Run backend tests only
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit

# Run specific test file
docker compose exec backend pytest tests/test_auth.py -v

# Run with coverage
docker compose exec backend pytest --cov=. --cov-report=html
```

### Frontend Unit Tests (Jest)
```bash
# Run frontend unit tests
docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit

# Run specific test file
cd frontend
npm test -- __tests__/components/LoginPage.test.tsx

# Run with coverage
npm test -- --coverage
```

### E2E Tests (Playwright)
```bash
# Run E2E tests
docker compose -f docker-compose.test.yml up e2e-tests --abort-on-container-exit

# Run locally
cd frontend
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test
npx playwright test e2e/auth.spec.ts

# Debug mode
npx playwright test --debug

# View HTML report
npx playwright show-report
```

---

## Testing Structure

### Backend Tests (`backend/tests/`)
```
backend/tests/
├── conftest.py           # Pytest fixtures
├── test_auth.py          # Authentication tests
├── test_bookings.py      # Booking tests
├── test_users.py         # User management tests
└── test_integration.py   # Integration tests
```

**Example Test:**
```python
def test_user_registration(client):
    """Test user registration flow."""
    response = client.post("/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert "id" in response.json()
```

### Frontend Unit Tests (`frontend/__tests__/`)
```
frontend/__tests__/
├── components/           # Component tests
├── hooks/                # Custom hook tests
├── integration/          # Integration tests
└── utils/                # Utility function tests
```

**Example Test:**
```typescript
describe('LoginPage', () => {
  it('submits login form', async () => {
    render(<LoginPage />)
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    })
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })
})
```

### E2E Tests (`frontend/e2e/`)
```
frontend/e2e/
├── auth.spec.ts          # Authentication E2E tests
├── booking.spec.ts       # Booking flow tests
├── messaging.spec.ts     # Messaging tests
└── fixtures/             # Test fixtures
```

**Example Test:**
```typescript
test('user can login', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[name="email"]', 'student@example.com')
  await page.fill('[name="password"]', 'student123')
  await page.click('button[type="submit"]')

  await expect(page).toHaveURL('/dashboard')
  await expect(page.locator('h1')).toContainText('Dashboard')
})
```

---

## Test Coverage Goals

- **Backend**: ≥80% code coverage
- **Frontend Components**: ≥70% code coverage
- **Critical Paths**: 100% E2E coverage
  - Authentication flow
  - Booking flow
  - Payment processing
  - Admin user management

---

## Testing Best Practices

### DO ✅
- Write tests before pushing code
- Test both happy paths and error cases
- Use descriptive test names
- Keep tests independent (no shared state)
- Mock external dependencies (APIs, databases)
- Use fixtures for test data
- Clean up after tests (reset DB state)
- Test accessibility (WCAG compliance)

### DON'T ❌
- Skip tests for "simple" code
- Test only happy paths
- Use production data in tests
- Make tests dependent on each other
- Ignore failing tests
- Commit commented-out tests
- Mock everything (integration tests need real interactions)

---

## Test Data Management

### Backend Test Data
```python
# conftest.py
@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        role="student"
    )
    db.add(user)
    db.commit()
    yield user
    db.delete(user)
    db.commit()
```

### Frontend Test Data
```typescript
// fixtures/users.ts
export const mockStudent = {
  id: 1,
  email: 'student@example.com',
  role: 'student',
  is_active: true
}

export const mockTutor = {
  id: 2,
  email: 'tutor@example.com',
  role: 'tutor',
  is_active: true
}
```

---

## Debugging Tests

### Backend
```bash
# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Stop at first failure
pytest -x

# Run last failed tests
pytest --lf

# Set breakpoint in test
import pdb; pdb.set_trace()
```

### Frontend
```bash
# Run in watch mode
npm test -- --watch

# Debug in VS Code
# Add to launch.json:
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/frontend/node_modules/.bin/jest",
  "args": ["--runInBand"]
}
```

### Playwright
```bash
# Debug mode (step through)
npx playwright test --debug

# UI mode (interactive)
npx playwright test --ui

# Headed mode (see browser)
npx playwright test --headed

# Record test
npx playwright codegen http://localhost:3000
```

---

## CI/CD Integration

Tests run automatically on:
- Pull request creation
- Push to main branch
- Manual workflow dispatch

**GitHub Actions workflow:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Accessibility Testing

Playwright includes automated accessibility testing:

```typescript
import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

test('login page is accessible', async ({ page }) => {
  await page.goto('/login')
  await injectAxe(page)
  await checkA11y(page)
})
```

---

## Performance Testing

Basic performance testing with Playwright:

```typescript
test('page load performance', async ({ page }) => {
  const startTime = Date.now()
  await page.goto('/dashboard')
  const loadTime = Date.now() - startTime

  expect(loadTime).toBeLessThan(3000) // < 3 seconds
})
```

---

## Related Documentation

- **[User Flows](../flows/)** - User journey documentation
- **[API Reference](../API_REFERENCE.md)** - API endpoint documentation
- **[Frontend Integration Tests](../../frontend/__tests__/integration/README.md)** - Integration test guide
- **[E2E Tests](../../frontend/e2e/README.md)** - E2E test documentation

---

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain coverage thresholds
4. Update test documentation
5. Add E2E tests for critical paths

---

**Last Updated**: 2026-01-28
