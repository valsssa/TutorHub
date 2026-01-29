# Playwright E2E Tests

This directory contains end-to-end tests using Playwright.

## Test Files

- `auth-flow.spec.ts` - Authentication tests (login, registration, logout)
- `tutor-search.spec.ts` - Tutor browsing and search functionality
- `booking-flow.spec.ts` - Complete booking workflow tests
- `messaging.spec.ts` - Real-time messaging system tests
- `accessibility.spec.ts` - WCAG compliance and a11y tests
- `helpers.ts` - Test utilities and helper functions

## Running Tests

### Local Development

```bash
# Run all tests
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug

# Run specific test file
npx playwright test e2e/auth-flow.spec.ts

# Run tests matching a pattern
npx playwright test --grep "should login"

# View test report
npm run test:e2e:report
```

### Docker

```bash
# Build Playwright test container
docker build -f Dockerfile.playwright -t playwright-tests .

# Run tests in Docker
docker run --rm \
  -e NEXT_PUBLIC_API_URL=http://test-backend:8000 \
  -e NEXT_PUBLIC_FRONTEND_URL=http://test-frontend:3000 \
  --network project1-splitversion_default \
  playwright-tests

# Run with volume mount to preserve reports
docker run --rm \
  -v $(pwd)/playwright-report:/app/playwright-report \
  -e NEXT_PUBLIC_API_URL=https://api.valsa.solutions/\
  --network project1-splitversion_default \
  playwright-tests
```

### CI/CD

Tests run automatically in CI with these environment variables:
- `CI=true` - Enables CI mode
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_FRONTEND_URL` - Frontend URL

## Test Structure

### Using Helpers

```typescript
import { TestHelpers, TestData } from './helpers';

test('example test', async ({ page }) => {
  // Login as student
  await TestHelpers.loginAsStudent(page);
  
  // Generate test data
  const user = TestData.generateUser();
  
  // Wait for API response
  await TestHelpers.waitForApiResponse(page, '/api/users');
});
```

### Custom Assertions

```typescript
import { CustomAssertions } from './helpers';

test('example test', async ({ page }) => {
  await CustomAssertions.assertPageTitle(page, /Dashboard/);
  await CustomAssertions.assertElementVisible(page, '.welcome-message');
});
```

## Configuration

### Playwright Config (`playwright.config.ts`)

- **Timeout**: 30 seconds per test
- **Retries**: 2 retries in CI, 0 locally
- **Workers**: 1 in CI, auto locally
- **Browsers**: Chromium (additional browsers commented out)
- **Screenshots**: On failure only
- **Video**: On retry only
- **Trace**: On first retry

### Environment Variables

```bash
# Frontend URL
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Test user credentials (from backend)
DEFAULT_STUDENT_EMAIL=student@example.com
DEFAULT_STUDENT_PASSWORD=student123
```

## Writing Tests

### Best Practices

1. **Use Semantic Locators**
   ```typescript
   // Good
   page.getByRole('button', { name: /sign in/i })
   page.getByLabel(/email/i)
   
   // Avoid
   page.locator('.btn-primary')
   page.locator('#email-input')
   ```

2. **Wait for Navigation**
   ```typescript
   await page.getByRole('button').click();
   await page.waitForURL(/\/dashboard/);
   ```

3. **Handle Async Operations**
   ```typescript
   await TestHelpers.waitForApiResponse(page, '/api/data');
   await page.waitForLoadState('networkidle');
   ```

4. **Clean State Between Tests**
   ```typescript
   test.beforeEach(async ({ page }) => {
     await page.context().clearCookies();
     await page.goto('/');
   });
   ```

5. **Use Test Data Helpers**
   ```typescript
   const email = TestHelpers.generateTestEmail();
   const password = TestHelpers.generatePassword();
   ```

## Accessibility Testing

Accessibility tests use `@axe-core/playwright` to check WCAG compliance:

```typescript
import AxeBuilder from '@axe-core/playwright';

test('should not have a11y violations', async ({ page }) => {
  await page.goto('/');
  
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Debugging

### Visual Debugging

```bash
# UI mode - interactive test runner
npm run test:e2e:ui

# Debug mode - step through tests
npm run test:e2e:debug

# Headed mode - see browser
npm run test:e2e:headed
```

### Screenshots and Videos

Failed tests automatically capture:
- Screenshot at failure point
- Video of the test run
- Trace file for inspection

View traces:
```bash
npx playwright show-trace trace.zip
```

## Common Issues

### Tests Timing Out

- Increase timeout in `playwright.config.ts`
- Add explicit waits: `await page.waitForTimeout(2000)`
- Wait for specific conditions: `await page.waitForSelector('.element')`

### Flaky Tests

- Use `test.describe.configure({ retries: 2 })`
- Add proper waits instead of hardcoded timeouts
- Check for race conditions

### Element Not Found

- Verify element exists with `await page.locator('.element').count()`
- Check if element is in shadow DOM
- Use more specific selectors

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)
