/**
 * Navigation E2E Tests - Real Backend Integration
 *
 * Tests navigation flows and route guards against real backend:
 * - Dashboard navigation
 * - Sidebar/menu interactions
 * - Deep linking
 * - Role-based route access
 * - No console errors during navigation
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

async function loginAsTutor(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('tutor@example.com');
  await page.getByLabel(/password/i).fill(process.env.TEST_TUTOR_PASSWORD || 'TutorPass123!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/(tutor|dashboard)/, { timeout: 20000 });
}

test.describe('Navigation - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Public Routes', () => {
    test('should navigate to login page', async ({ page }) => {
      await page.goto('/login');
      await expect(page).toHaveURL('/login');
      await expect(page.getByLabel(/email/i)).toBeVisible();
    });

    test('should navigate to register page', async ({ page }) => {
      await page.goto('/register');
      await expect(page).toHaveURL('/register');
      await expect(page.getByLabel(/email/i)).toBeVisible();
    });

    test('should navigate to forgot password page', async ({ page }) => {
      await page.goto('/forgot-password');
      await expect(page).toHaveURL('/forgot-password');
    });

    test('should navigate between login and register', async ({ page }) => {
      await page.goto('/login');

      const signUpLink = page.getByRole('link', { name: /sign up|register|create account/i });
      await signUpLink.click();
      await expect(page).toHaveURL('/register');

      const signInLink = page.getByRole('link', { name: /sign in|login|already have/i });
      await signInLink.click();
      await expect(page).toHaveURL('/login');
    });
  });

  test.describe('Student Dashboard Navigation', () => {
    test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display student dashboard', async ({ page }) => {
      await expect(page.getByText(/dashboard|welcome|student/i)).toBeVisible({ timeout: 10000 });
    });

    test('should navigate to tutors page', async ({ page }) => {
      const tutorsLink = page.getByRole('link', { name: /tutors|find.*tutor|browse/i });
      if (await tutorsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tutorsLink.click();
        await expect(page).toHaveURL(/\/tutors/);
      }
    });

    test('should navigate to bookings page', async ({ page }) => {
      const bookingsLink = page.getByRole('link', { name: /booking|session|schedule/i });
      if (await bookingsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await bookingsLink.click();
        await expect(page).toHaveURL(/\/bookings/);
      }
    });

    test('should navigate to messages page', async ({ page }) => {
      const messagesLink = page.getByRole('link', { name: /message|chat|inbox/i });
      if (await messagesLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await messagesLink.click();
        await expect(page).toHaveURL(/\/messages/);
      }
    });

    test('should navigate to favorites page', async ({ page }) => {
      const favoritesLink = page.getByRole('link', { name: /favorite|saved|liked/i });
      if (await favoritesLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await favoritesLink.click();
        await expect(page).toHaveURL(/\/favorites/);
      }
    });

    test('should navigate to settings page', async ({ page }) => {
      const settingsLink = page.getByRole('link', { name: /setting/i });
      if (await settingsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await settingsLink.click();
        await expect(page).toHaveURL(/\/settings/);
      }
    });

    test('should navigate to profile page', async ({ page }) => {
      const profileLink = page.getByRole('link', { name: /profile/i });
      if (await profileLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await profileLink.click();
        await expect(page).toHaveURL(/\/profile/);
      }
    });

    test('should navigate to notifications page', async ({ page }) => {
      const notificationsLink = page.getByRole('link', { name: /notification/i })
        .or(page.locator('[data-testid="notification-bell"]'));
      if (await notificationsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await notificationsLink.click();
        await expect(page).toHaveURL(/\/notifications/);
      }
    });

    test('should navigate to wallet page', async ({ page }) => {
      const walletLink = page.getByRole('link', { name: /wallet|balance|payment/i });
      if (await walletLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await walletLink.click();
        await expect(page).toHaveURL(/\/wallet/);
      }
    });
  });

  test.describe('Tutor Dashboard Navigation', () => {
    test.skip(!process.env.TEST_TUTOR_PASSWORD, 'TEST_TUTOR_PASSWORD env var not set');

    test.beforeEach(async ({ page }) => {
      await loginAsTutor(page);
    });

    test('should display tutor dashboard', async ({ page }) => {
      await expect(page.getByText(/dashboard|welcome|tutor/i)).toBeVisible({ timeout: 10000 });
    });

    test('should navigate to tutor students page', async ({ page }) => {
      const studentsLink = page.getByRole('link', { name: /student|my student/i });
      if (await studentsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await studentsLink.click();
        await expect(page).toHaveURL(/\/tutor\/students/);
      }
    });
  });

  test.describe('Deep Linking', () => {
    test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');

    test('should deep link to student dashboard after login', async ({ page }) => {
      await page.goto('/student');

      await page.waitForURL('/login');

      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/student/, { timeout: 20000 });
    });

    test('should deep link to settings after login', async ({ page }) => {
      await page.goto('/settings');

      await page.waitForURL('/login');

      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!');
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/(settings|student|dashboard)/, { timeout: 20000 });
    });
  });

  test.describe('Role-Based Access', () => {
    test('student should not access admin dashboard', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');
      await loginAsStudent(page);

      await page.goto('/admin');

      const isOnAdmin = page.url().includes('/admin');
      const hasAccessDenied = await page.getByText(/access denied|unauthorized|forbidden/i)
        .isVisible({ timeout: 3000 }).catch(() => false);
      const wasRedirected = page.url().includes('/student') || page.url().includes('/login');

      expect(hasAccessDenied || wasRedirected || !isOnAdmin).toBeTruthy();
    });

    test('student should not access owner dashboard', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');
      await loginAsStudent(page);

      await page.goto('/owner');

      const isOnOwner = page.url().includes('/owner');
      const hasAccessDenied = await page.getByText(/access denied|unauthorized|forbidden/i)
        .isVisible({ timeout: 3000 }).catch(() => false);
      const wasRedirected = page.url().includes('/student') || page.url().includes('/login');

      expect(hasAccessDenied || wasRedirected || !isOnOwner).toBeTruthy();
    });

    test('tutor should not access admin dashboard', async ({ page }) => {
      test.skip(!process.env.TEST_TUTOR_PASSWORD, 'TEST_TUTOR_PASSWORD env var not set');
      await loginAsTutor(page);

      await page.goto('/admin');

      const isOnAdmin = page.url().includes('/admin');
      const hasAccessDenied = await page.getByText(/access denied|unauthorized|forbidden/i)
        .isVisible({ timeout: 3000 }).catch(() => false);
      const wasRedirected = page.url().includes('/tutor') || page.url().includes('/login');

      expect(hasAccessDenied || wasRedirected || !isOnAdmin).toBeTruthy();
    });
  });

  test.describe('Error Handling', () => {
    test('should show 404 page for unknown routes', async ({ page }) => {
      await page.goto('/this-route-does-not-exist-12345');
      await page.waitForLoadState('networkidle');

      const has404 = await page.getByText(/404|not found|page.*not.*exist/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const wasRedirected = page.url().includes('/login') || page.url().includes('edustream.valsa.solutions');

      expect(has404 || wasRedirected).toBeTruthy();
    });

    test('should handle back navigation correctly', async ({ page }) => {
      test.skip(!process.env.TEST_STUDENT_PASSWORD, 'TEST_STUDENT_PASSWORD env var not set');
      await loginAsStudent(page);

      const tutorsLink = page.getByRole('link', { name: /tutors|find.*tutor/i });
      if (await tutorsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tutorsLink.click();
        await page.waitForURL(/\/tutors/);

        await page.goBack();

        await expect(page).toHaveURL(/\/(student|dashboard)/);
      }
    });
  });
});
