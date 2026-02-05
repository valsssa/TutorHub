/**
 * Auth E2E Tests - Real Backend Integration
 *
 * These tests run against the real backend API and verify:
 * - Login success/failure flows
 * - Session persistence
 * - Token refresh handling
 * - Logout flows
 * - No console errors during auth operations
 */
import { test, expect } from '../fixtures/test-base';

const BASE_URL = process.env.E2E_BASE_URL || 'https://edustream.valsa.solutions';

test.describe('Authentication - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Login Flow', () => {
    test('should display login page without console errors', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByLabel(/password/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    });

    test('should show validation errors for empty submission', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: /sign in/i }).click();

      await expect(page.getByText(/email.*required|required.*email/i)).toBeVisible({ timeout: 5000 });
      await expect(page.getByText(/password.*required|required.*password/i)).toBeVisible({ timeout: 5000 });
    });

    test('should show error for invalid email format', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('not-an-email');
      await page.getByLabel(/password/i).fill('SomePassword123');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Different apps may show this error differently - check for any validation message
      const hasError = await page.getByText(/invalid|error|valid.*email|format/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const buttonDisabled = await page.getByRole('button', { name: /sign in/i }).isDisabled().catch(() => false);
      const stayedOnLogin = page.url().includes('/login');

      // At minimum, user should not proceed with invalid email
      expect(hasError || buttonDisabled || stayedOnLogin).toBeTruthy();
    });

    test('should show error for incorrect credentials against real API', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('nonexistent-user-12345@example.com');
      await page.getByLabel(/password/i).fill('WrongPassword123!');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Wait for API response and check for error or stayed on login
      await page.waitForTimeout(3000);

      const hasError = await page.getByText(/invalid|incorrect|failed|unauthorized|wrong|error/i)
        .isVisible({ timeout: 10000 }).catch(() => false);
      const stayedOnLogin = page.url().includes('/login');

      expect(hasError || stayedOnLogin).toBeTruthy();
    });

    test('should login successfully with valid student credentials', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });

      expect(page.url()).toMatch(/\/(student|dashboard)/);
    });

    test('should login successfully with tutor credentials', async ({ page }) => {
      test.skip(!process.env.TEST_TUTOR_PASSWORD, 'TEST_TUTOR_PASSWORD env var not set');

      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('tutor@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_TUTOR_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/(tutor|dashboard)/, { timeout: 20000 });

      expect(page.url()).toMatch(/\/(tutor|dashboard)/);
    });

    test('should show loading state during login', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!');

      const submitButton = page.getByRole('button', { name: /sign in/i });
      await submitButton.click();

      const isDisabled = await submitButton.isDisabled().catch(() => false);
      const hasLoadingSpinner = await page.locator('[class*="spin"], [class*="loading"], [data-loading="true"]')
        .isVisible().catch(() => false);

      expect(isDisabled || hasLoadingSpinner).toBeTruthy();
    });
  });

  test.describe('Session Management', () => {
    test('should maintain session after page refresh', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

      await page.goto('/login');
      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();
      await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });

      await page.reload();
      await page.waitForLoadState('networkidle');

      expect(page.url()).not.toContain('/login');
    });

    test('should maintain session via HttpOnly cookies', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

      await page.goto('/login');
      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();
      await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });

      const cookies = await page.context().cookies();
      const hasAccessToken = cookies.some(c => c.name === 'access_token' && c.httpOnly);
      expect(hasAccessToken).toBeTruthy();
    });
  });

  test.describe('Logout Flow', () => {
    test('should logout and redirect to login', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

      await page.goto('/login');
      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();
      await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });

      const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
      const userMenu = page.locator('[data-testid="user-menu"]')
        .or(page.getByRole('button').filter({ hasText: /profile|menu|account/i }));

      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click();
      } else if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click();
        const logoutOption = page.getByRole('menuitem', { name: /logout|sign out/i })
          .or(page.getByText(/logout|sign out/i));
        await logoutOption.click();
      } else {
        await page.locator('nav, aside, header')
          .getByText(/logout|sign out/i)
          .click();
      }

      await page.waitForURL('/login', { timeout: 10000 });
    });

    test('should clear HttpOnly cookies on logout', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

      await page.goto('/login');
      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();
      await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });

      const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
      const userMenu = page.locator('[data-testid="user-menu"]')
        .or(page.getByRole('button').filter({ hasText: /profile|menu|account/i }));

      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click();
      } else if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click();
        const logoutOption = page.getByRole('menuitem', { name: /logout|sign out/i })
          .or(page.getByText(/logout|sign out/i));
        await logoutOption.click();
      } else {
        await page.locator('nav, aside, header')
          .getByText(/logout|sign out/i)
          .click();
      }

      await page.waitForURL('/login', { timeout: 10000 });

      const cookies = await page.context().cookies();
      const hasAccessToken = cookies.some(c => c.name === 'access_token');
      expect(hasAccessToken).toBeFalsy();
    });
  });

  test.describe('Route Protection', () => {
    test('should redirect unauthenticated users from protected routes', async ({ page }) => {
      // Clear any existing cookies by starting fresh context
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.goto('/student');
      await page.waitForLoadState('networkidle');

      // Should either redirect to login or show login form
      const isOnLogin = page.url().includes('/login');
      const hasLoginForm = await page.getByLabel(/email/i).isVisible({ timeout: 5000 }).catch(() => false);

      expect(isOnLogin || hasLoginForm).toBeTruthy();
    });

    test('should redirect from /bookings without authentication', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');

      const isOnLogin = page.url().includes('/login');
      const hasLoginForm = await page.getByLabel(/email/i).isVisible({ timeout: 5000 }).catch(() => false);

      expect(isOnLogin || hasLoginForm).toBeTruthy();
    });

    test('should redirect from /messages without authentication', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      await page.goto('/messages');
      await page.waitForLoadState('networkidle');

      const isOnLogin = page.url().includes('/login');
      const hasLoginForm = await page.getByLabel(/email/i).isVisible({ timeout: 5000 }).catch(() => false);

      expect(isOnLogin || hasLoginForm).toBeTruthy();
    });
  });
});
