# Playwright E2E Testing Guide

Complete guide for running and writing Playwright end-to-end tests.

## Table of Contents

- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Structure](#test-structure)
- [Docker Support](#docker-support)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
npx playwright install chromium
```

### 2. Run Tests

```bash
# Run all tests
npm run test:e2e

# Run with UI (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed
```

### 3. View Results

```bash
# Open HTML report
npm run test:e2e:report
```

## Running Tests

### NPM Scripts

```bash
# Run all E2E tests
npm run test:e2e

# Interactive UI mode (best for development)
npm run test:e2e:ui

# Headed mode (show browser)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

### Using Shell Script

```bash
# Run all tests
./run-playwright-tests.sh

# Interactive mode
./run-playwright-tests.sh --ui

# Run specific test file
./run-playwright-tests.sh --file e2e/auth-flow.spec.ts

# Run tests matching pattern
./run-playwright-tests.sh --grep "login"

# Run with multiple workers
./run-playwright-tests.sh --workers 4

# Show browser during tests
./run-playwright-tests.sh --headed

# Debug mode
./run-playwright-tests.sh --debug
```

### Direct Playwright Commands

```bash
# Run all tests
npx playwright test

# Run specific file
npx playwright test e2e/auth-flow.spec.ts

# Run tests matching pattern
npx playwright test --grep "should login"

# Run with specific browser
npx playwright test --project=firefox

# Run in headed mode
npx playwright test --headed

# Debug mode
npx playwright test --debug

# Update snapshots
npx playwright test --update-snapshots

# Generate code (record actions)
npx playwright codegen http://localhost:3000
```

## Test Files Overview

### 1. Authentication Tests (`auth-flow.spec.ts`)

Tests user authentication flows:
- Login page display
- Registration page display
- New user registration
- Valid/invalid login
- Logout functionality
- Protected routes
- Form validation

**Example:**
```typescript
test('should login with valid credentials', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/login`);
  await page.getByRole('textbox', { name: /email/i }).fill('student@example.com');
  await page.getByLabel(/password/i).fill('student123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
  await expect(page).toHaveURL(/\/dashboard/i);
});
```

### 2. Tutor Search Tests (`tutor-search.spec.ts`)

Tests tutor browsing and search:
- Display tutors page
- Search by subject
- Filter by price
- View tutor profiles
- Save favorites
- Pagination

**Example:**
```typescript
test('should search tutors by subject', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/tutors`);
  const searchInput = page.getByPlaceholder(/search.*subject/i).first();
  await searchInput.fill('Mathematics');
  await searchInput.press('Enter');
  await page.waitForTimeout(2000);
  const resultsCount = await page.getByTestId('tutor-card').count();
  console.log(`Found ${resultsCount} tutor results`);
});
```

### 3. Booking Flow Tests (`booking-flow.spec.ts`)

Tests booking functionality:
- Display booking modal
- Select date and time
- View bookings
- Filter by status
- Cancel bookings
- Reschedule bookings

**Example:**
```typescript
test('should display booking modal from tutor profile', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/tutor/1`);
  const bookButton = page.getByRole('button', { name: /book.*session/i }).first();
  await bookButton.click();
  await expect(page.getByText(/select.*time/i)).toBeVisible({ timeout: 3000 });
});
```

### 4. Messaging Tests (`messaging.spec.ts`)

Tests real-time messaging:
- Display messages page
- Conversation list
- Open conversations
- Send messages
- Unread counts
- Search conversations
- Message timestamps

**Example:**
```typescript
test('should send a message', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/messages`);
  const firstConversation = page.getByTestId('conversation-item').first();
  await firstConversation.click();
  const messageInput = page.getByPlaceholder(/type.*message/i);
  const testMessage = `Test message ${Date.now()}`;
  await messageInput.fill(testMessage);
  await messageInput.press('Enter');
  await expect(page.getByText(testMessage)).toBeVisible({ timeout: 5000 });
});
```

### 5. Accessibility Tests (`accessibility.spec.ts`)

Tests WCAG compliance:
- No accessibility violations
- Keyboard navigation
- Heading hierarchy
- Image alt text
- Form labels
- Color contrast
- Screen reader landmarks
- Accessible button names

**Example:**
```typescript
test('login page should not have accessibility violations', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/login`);
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Test Helpers

The `helpers.ts` file provides utilities for common test operations:

### TestHelpers Class

```typescript
import { TestHelpers } from './helpers';

// Login helpers
await TestHelpers.loginAsStudent(page);
await TestHelpers.loginAsTutor(page);
await TestHelpers.loginAsAdmin(page);
await TestHelpers.logout(page);

// Data generation
const email = TestHelpers.generateTestEmail();
const password = TestHelpers.generatePassword();

// API utilities
await TestHelpers.waitForApiResponse(page, '/api/users');
await TestHelpers.mockApiResponse(page, /api\/tutors/, mockData);

// Element utilities
await TestHelpers.waitForElement(page, '.element');
const exists = await TestHelpers.elementExists(page, '.element');
await TestHelpers.scrollToElement(page, '.element');

// Session management
await TestHelpers.clearSession(page);
const isAuth = await TestHelpers.isAuthenticated(page);

// Screenshots
await TestHelpers.takeScreenshot(page, 'test-name');
```

### TestData Class

```typescript
import { TestData } from './helpers';

// Pre-configured users
const student = TestData.student; // { email, password }
const tutor = TestData.tutor;
const admin = TestData.admin;

// Generate test data
const user = TestData.generateUser();
const booking = TestData.generateBooking();
const message = TestData.generateMessage();
```

### CustomAssertions Class

```typescript
import { CustomAssertions } from './helpers';

await CustomAssertions.assertPageTitle(page, /Dashboard/);
await CustomAssertions.assertUrl(page, /\/dashboard/);
await CustomAssertions.assertElementVisible(page, '.welcome');
await CustomAssertions.assertElementHidden(page, '.error');
await CustomAssertions.assertTextContent(page, '.title', 'Welcome');
await CustomAssertions.assertElementCount(page, '.item', 5);
```

## Writing New Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.context().clearCookies();
    await page.goto(FRONTEND_URL);
  });

  test('should do something', async ({ page }) => {
    // Test implementation
  });

  test.afterEach(async ({ page }) => {
    // Cleanup after each test
  });
});
```

### Using Locators

```typescript
// Recommended: Semantic locators
page.getByRole('button', { name: /sign in/i })
page.getByLabel(/email/i)
page.getByPlaceholder(/search/i)
page.getByText(/welcome/i)
page.getByTestId('user-profile')

// Alternative: CSS selectors
page.locator('.button-primary')
page.locator('#login-form')
page.locator('[data-testid="user-profile"]')
```

### Waiting Strategies

```typescript
// Wait for navigation
await page.waitForURL(/\/dashboard/);

// Wait for element
await page.waitForSelector('.element', { state: 'visible' });

// Wait for API response
await page.waitForResponse(response => 
  response.url().includes('/api/data') && response.status() === 200
);

// Wait for load state
await page.waitForLoadState('networkidle');

// Wait for timeout (use sparingly)
await page.waitForTimeout(2000);
```

### Assertions

```typescript
// Page assertions
await expect(page).toHaveTitle(/Dashboard/);
await expect(page).toHaveURL(/\/dashboard/);

// Element assertions
await expect(element).toBeVisible();
await expect(element).toBeHidden();
await expect(element).toBeEnabled();
await expect(element).toBeDisabled();
await expect(element).toBeFocused();
await expect(element).toContainText('Expected text');
await expect(element).toHaveAttribute('href', '/dashboard');
await expect(element).toHaveCount(5);

// Negation
await expect(element).not.toBeVisible();
```

## Docker Support

### Build and Run

```bash
# Build Playwright Docker image
docker build -f Dockerfile.playwright -t playwright-tests .

# Run tests in Docker
docker run --rm \
  -e NEXT_PUBLIC_API_URL=http://test-backend:8000 \
  -e NEXT_PUBLIC_FRONTEND_URL=http://test-frontend:3000 \
  --network project1-splitversion_default \
  playwright-tests

# Run with volume for reports
docker run --rm \
  -v $(pwd)/playwright-report:/app/playwright-report \
  -v $(pwd)/test-results:/app/test-results \
  playwright-tests
```

### Docker Compose

```bash
# Run all test services including Playwright
docker compose -f docker-compose.test.yml up --build playwright-tests

# Run and clean up
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit playwright-tests
docker compose -f docker-compose.test.yml down -v
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  playwright-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 20
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Install Playwright browsers
        run: |
          cd frontend
          npx playwright install --with-deps chromium
      
      - name: Run Playwright tests
        run: |
          cd frontend
          npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Configuration

### Environment Variables

```bash
# Frontend URL
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# CI mode
CI=true

# Test user credentials
DEFAULT_STUDENT_EMAIL=student@example.com
DEFAULT_STUDENT_PASSWORD=student123
```

### Playwright Config

Edit `playwright.config.ts` to customize:

```typescript
export default defineConfig({
  testDir: './e2e',
  timeout: 30 * 1000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
});
```

## Troubleshooting

### Common Issues

1. **Tests timeout**
   - Increase timeout in config
   - Add explicit waits
   - Check if services are running

2. **Element not found**
   - Verify selector is correct
   - Check if element is in iframe/shadow DOM
   - Add wait before interaction

3. **Flaky tests**
   - Replace timeouts with proper waits
   - Use `waitForSelector` instead of `waitForTimeout`
   - Enable retries in config

4. **Browser not launching**
   ```bash
   npx playwright install --force chromium
   ```

5. **Permission denied (script)**
   ```bash
   chmod +x run-playwright-tests.sh
   ```

### Debug Mode

```bash
# Step through tests
npx playwright test --debug

# Pause on failure
npx playwright test --headed --debug

# Use inspector
PWDEBUG=1 npx playwright test
```

### View Traces

```bash
# Generate trace
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

## Best Practices

1. **Use semantic locators** - Prefer `getByRole`, `getByLabel` over CSS selectors
2. **Wait for navigation** - Always wait for URL changes after actions
3. **Clean state** - Clear cookies/storage between tests
4. **Isolate tests** - Each test should be independent
5. **Descriptive names** - Use clear test descriptions
6. **Avoid hardcoded waits** - Use proper wait conditions
7. **Handle async operations** - Wait for API responses
8. **Test data helpers** - Use utility functions for data generation
9. **Screenshot on failure** - Already configured in config
10. **Accessibility** - Include a11y tests for all pages

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
