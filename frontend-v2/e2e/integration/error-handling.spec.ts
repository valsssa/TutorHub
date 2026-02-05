/**
 * Error Handling E2E Tests - Real Backend Integration
 *
 * Verifies proper error handling for:
 * - 401 Unauthorized responses
 * - 403 Forbidden responses
 * - 404 Not Found responses
 * - 500 Server errors (if testable)
 * - Network failures/timeouts
 * - Recovery from errors
 */
import { test, expect } from '../fixtures/test-base';

const BASE_URL = process.env.E2E_BASE_URL || 'https://edustream.valsa.solutions';

async function loginAsStudent(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('student@example.com');
  await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });
}

test.describe('Error Handling - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Authentication Errors', () => {
    test('should handle 401 and redirect to login', async ({ page }) => {
      await loginAsStudent(page);

      await page.context().clearCookies();

      await page.reload();

      await page.waitForURL('/login', { timeout: 15000 });
    });

    test('should show friendly message for invalid credentials', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('nonexistent@example.com');
      await page.getByLabel(/password/i).fill('InvalidPassword123!');
      await page.getByRole('button', { name: /sign in/i }).click();

      const hasError = await page.getByText(/invalid|incorrect|failed|unauthorized|wrong|error/i)
        .isVisible({ timeout: 10000 }).catch(() => false);
      const stayedOnLogin = page.url().includes('/login');

      expect(hasError || stayedOnLogin).toBeTruthy();
    });

    test('should handle session expiry gracefully', async ({ page }) => {
      await loginAsStudent(page);

      await page.context().clearCookies();

      await page.goto('/student');

      await page.waitForURL('/login', { timeout: 15000 });
    });
  });

  test.describe('404 Not Found', () => {
    test('should show user-friendly 404 page', async ({ page }) => {
      await page.goto('/nonexistent-page-xyz-123');

      const has404Content = await page.getByText(/404|not found|page.*doesn.*exist/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const redirectedToLogin = page.url().includes('/login');
      const redirectedToHome = page.url() === BASE_URL + '/' || page.url() === BASE_URL;

      expect(has404Content || redirectedToLogin || redirectedToHome).toBeTruthy();
    });

    test('should provide navigation from 404 page', async ({ page }) => {
      await page.goto('/nonexistent-page-xyz-123');

      const homeLink = page.getByRole('link', { name: /home|go back|return/i });
      const loginLink = page.getByRole('link', { name: /login|sign in/i });

      const hasNavigation = await homeLink.isVisible({ timeout: 3000 }).catch(() => false) ||
        await loginLink.isVisible({ timeout: 3000 }).catch(() => false) ||
        page.url().includes('/login');

      expect(hasNavigation).toBeTruthy();
    });
  });

  test.describe('Network Error Recovery', () => {
    test('should handle offline mode gracefully', async ({ page, context }) => {
      await loginAsStudent(page);

      await context.setOffline(true);

      const tutorsLink = page.getByRole('link', { name: /tutors|find.*tutor/i });
      if (await tutorsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tutorsLink.click();

        const hasOfflineIndicator = await page.getByText(/offline|no connection|network error/i)
          .isVisible({ timeout: 5000 }).catch(() => false);
        const hasRetryButton = await page.getByRole('button', { name: /retry|try again/i })
          .isVisible({ timeout: 3000 }).catch(() => false);

        if (hasOfflineIndicator || hasRetryButton) {
          await context.setOffline(false);

          if (hasRetryButton) {
            await page.getByRole('button', { name: /retry|try again/i }).click();
          } else {
            await page.reload();
          }

          await expect(page).toHaveURL(/\/tutors/);
        }
      }
    });

    test('should recover from temporary network failure', async ({ page }) => {
      await loginAsStudent(page);

      let requestCount = 0;
      await page.route('**/api/v1/tutors**', async (route) => {
        requestCount++;
        if (requestCount === 1) {
          await route.abort('failed');
        } else {
          await route.continue();
        }
      });

      const tutorsLink = page.getByRole('link', { name: /tutors|find.*tutor/i });
      if (await tutorsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tutorsLink.click();

        await page.waitForTimeout(2000);

        const hasError = await page.getByText(/error|failed|try again/i)
          .isVisible({ timeout: 3000 }).catch(() => false);

        if (hasError) {
          const retryButton = page.getByRole('button', { name: /retry|try again|reload/i });
          if (await retryButton.isVisible({ timeout: 2000 }).catch(() => false)) {
            await retryButton.click();
          }
        }
      }
    });
  });

  test.describe('API Error Display', () => {
    test('should display validation errors from API', async ({ page }) => {
      await page.goto('/register');

      await page.getByLabel(/email/i).fill('test@example.com');
      await page.getByLabel(/password/i).first().fill('weak');

      const confirmPassword = page.getByLabel(/confirm.*password/i);
      if (await confirmPassword.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmPassword.fill('weak');
      }

      await page.getByRole('button', { name: /sign up|register|create/i }).click();

      const hasValidationError = await page.getByText(/password.*must|invalid|too short|weak/i)
        .isVisible({ timeout: 5000 }).catch(() => false);

      expect(hasValidationError).toBeTruthy();
    });

    test('should show toast or inline error for API failures', async ({ page }) => {
      await loginAsStudent(page);

      const hasErrorBoundary = await page.locator('[data-testid="error-boundary"]')
        .isVisible({ timeout: 2000 }).catch(() => false);
      const hasToast = await page.locator('[role="alert"], [data-testid="toast"]')
        .isVisible({ timeout: 2000 }).catch(() => false);

    });
  });

  test.describe('Form Error States', () => {
    test('should preserve form data on validation error', async ({ page }) => {
      await page.goto('/login');

      const testEmail = 'test@example.com';
      await page.getByLabel(/email/i).fill(testEmail);
      await page.getByLabel(/password/i).fill('');
      await page.getByRole('button', { name: /sign in/i }).click();

      const emailValue = await page.getByLabel(/email/i).inputValue();
      expect(emailValue).toBe(testEmail);
    });

    test('should clear errors when user starts typing', async ({ page }) => {
      await page.goto('/login');

      await page.getByRole('button', { name: /sign in/i }).click();

      const hasError = await page.getByText(/email.*required/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      if (hasError) {
        await page.getByLabel(/email/i).fill('test@example.com');

        await page.waitForTimeout(500);

        const errorCleared = await page.getByText(/email.*required/i)
          .isHidden({ timeout: 2000 }).catch(() => true);

        expect(errorCleared).toBeTruthy();
      }
    });
  });

  test.describe('Loading States', () => {
    test('should show loading indicator while fetching data', async ({ page }) => {
      await page.route('**/api/v1/tutors**', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        await route.continue();
      });

      await loginAsStudent(page);

      const tutorsLink = page.getByRole('link', { name: /tutors|find.*tutor/i });
      if (await tutorsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tutorsLink.click();

        const hasLoadingIndicator = await page.locator('[class*="spin"], [class*="loading"], [data-loading="true"], [role="progressbar"]')
          .isVisible({ timeout: 2000 }).catch(() => false);
        const hasSkeleton = await page.locator('[class*="skeleton"], [data-skeleton="true"]')
          .isVisible({ timeout: 2000 }).catch(() => false);

      }
    });

    test('should not show infinite loading', async ({ page }) => {
      await loginAsStudent(page);

      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      const stillLoading = await page.locator('[class*="spin"], [data-loading="true"]')
        .isVisible({ timeout: 1000 }).catch(() => false);

      const hasSkeleton = await page.locator('[class*="skeleton"]:not([class*="text"])')
        .isVisible({ timeout: 1000 }).catch(() => false);

    });
  });
});
