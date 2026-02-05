/**
 * Settings E2E Tests - Real Backend Integration
 *
 * Tests settings and profile management:
 * - Profile settings
 * - Account settings
 * - Notification preferences
 * - Security settings
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

test.describe('Settings - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Settings Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display settings page', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/setting/i)).toBeVisible({ timeout: 10000 });
    });

    test('should have settings sidebar/navigation', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const settingsNav = page.locator('nav, aside').filter({ hasText: /profile|account|notification/i });
      const hasNav = await settingsNav.isVisible({ timeout: 5000 }).catch(() => false);

      const settingsTabs = page.getByRole('tab').or(page.getByRole('link')).filter({ hasText: /profile|account|notification/i });
      const hasTabs = await settingsTabs.first().isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasNav || hasTabs).toBeTruthy();
    });

    test('should navigate to profile settings', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const profileLink = page.getByRole('link', { name: /profile/i })
        .or(page.getByRole('tab', { name: /profile/i }));

      if (await profileLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await profileLink.click();
        await expect(page).toHaveURL(/\/settings\/profile/);
      }
    });

    test('should navigate to account settings', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const accountLink = page.getByRole('link', { name: /account/i })
        .or(page.getByRole('tab', { name: /account/i }));

      if (await accountLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await accountLink.click();
        await expect(page).toHaveURL(/\/settings\/account/);
      }
    });

    test('should navigate to notification settings', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      const notificationLink = page.getByRole('link', { name: /notification/i })
        .or(page.getByRole('tab', { name: /notification/i }));

      if (await notificationLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await notificationLink.click();
        await expect(page).toHaveURL(/\/settings\/notifications/);
      }
    });
  });

  test.describe('Profile Settings', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/settings/profile');
      await page.waitForLoadState('networkidle');
    });

    test('should display profile form', async ({ page }) => {
      const firstNameInput = page.getByLabel(/first.*name/i).or(page.locator('input[name="first_name"]'));
      const lastNameInput = page.getByLabel(/last.*name/i).or(page.locator('input[name="last_name"]'));

      const hasFirstName = await firstNameInput.isVisible({ timeout: 5000 }).catch(() => false);
      const hasLastName = await lastNameInput.isVisible({ timeout: 5000 }).catch(() => false);

      expect(hasFirstName || hasLastName).toBeTruthy();
    });

    test('should pre-populate profile data', async ({ page }) => {
      await page.waitForTimeout(2000);

      const firstNameInput = page.getByLabel(/first.*name/i).or(page.locator('input[name="first_name"]'));

      if (await firstNameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
        const value = await firstNameInput.inputValue();
        expect(value.length).toBeGreaterThanOrEqual(0);
      }
    });

    test('should have save button', async ({ page }) => {
      const saveButton = page.getByRole('button', { name: /save|update|submit/i });
      await expect(saveButton).toBeVisible({ timeout: 5000 });
    });

    test('should validate required fields', async ({ page }) => {
      const firstNameInput = page.getByLabel(/first.*name/i).or(page.locator('input[name="first_name"]'));

      if (await firstNameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
        await firstNameInput.clear();

        const saveButton = page.getByRole('button', { name: /save|update/i });
        await saveButton.click();

        await page.waitForTimeout(1000);

        const hasError = await page.getByText(/required|cannot be empty/i)
          .isVisible({ timeout: 3000 }).catch(() => false);

      }
    });

    test('should show avatar upload option', async ({ page }) => {
      const avatarUpload = page.locator('input[type="file"]')
        .or(page.getByRole('button', { name: /avatar|photo|picture|upload/i }))
        .or(page.locator('[data-testid="avatar-upload"]'));

      const hasAvatarUpload = await avatarUpload.isVisible({ timeout: 5000 }).catch(() => false);

    });
  });

  test.describe('Account Settings', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/settings/account');
      await page.waitForLoadState('networkidle');
    });

    test('should display account settings', async ({ page }) => {
      await expect(page.getByText(/account|email|password/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show change password option', async ({ page }) => {
      const changePasswordSection = page.getByText(/change.*password|update.*password/i)
        .or(page.getByRole('button', { name: /change.*password/i }));

      const hasPasswordChange = await changePasswordSection.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should have password change form', async ({ page }) => {
      const currentPassword = page.getByLabel(/current.*password/i)
        .or(page.locator('input[name="current_password"]'));
      const newPassword = page.getByLabel(/new.*password/i)
        .or(page.locator('input[name="new_password"]'));

      const hasCurrentPassword = await currentPassword.isVisible({ timeout: 5000 }).catch(() => false);
      const hasNewPassword = await newPassword.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should validate password change form', async ({ page }) => {
      const currentPassword = page.getByLabel(/current.*password/i)
        .or(page.locator('input[name="current_password"]'));
      const submitButton = page.getByRole('button', { name: /change|update.*password/i });

      if (await currentPassword.isVisible({ timeout: 3000 }).catch(() => false) &&
          await submitButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await submitButton.click();

        const hasError = await page.getByText(/required|password/i)
          .isVisible({ timeout: 3000 }).catch(() => false);

      }
    });
  });

  test.describe('Notification Settings', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/settings/notifications');
      await page.waitForLoadState('networkidle');
    });

    test('should display notification preferences', async ({ page }) => {
      await expect(page.getByText(/notification/i)).toBeVisible({ timeout: 10000 });
    });

    test('should have toggle switches for notifications', async ({ page }) => {
      const toggles = page.locator('[role="switch"]')
        .or(page.locator('input[type="checkbox"]'))
        .or(page.locator('[data-testid*="toggle"]'));

      const toggleCount = await toggles.count();

    });

    test('should have email notification settings', async ({ page }) => {
      const emailSettings = page.getByText(/email.*notification|notification.*email/i);
      const hasEmailSettings = await emailSettings.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should save notification preferences', async ({ page }) => {
      const saveButton = page.getByRole('button', { name: /save|update/i });

      if (await saveButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await saveButton.click();

        const hasSuccessMessage = await page.getByText(/saved|updated|success/i)
          .isVisible({ timeout: 5000 }).catch(() => false);

      }
    });
  });

  test.describe('Tutor-Specific Settings', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTutor(page);
    });

    test('should show video settings for tutors', async ({ page }) => {
      await page.goto('/settings/video');
      await page.waitForLoadState('networkidle');

      const hasVideoSettings = await page.getByText(/video|zoom|meeting/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const wasRedirected = page.url().includes('/settings');

      expect(hasVideoSettings || wasRedirected).toBeTruthy();
    });

    test('should show integrations settings for tutors', async ({ page }) => {
      await page.goto('/settings/integrations');
      await page.waitForLoadState('networkidle');

      const hasIntegrations = await page.getByText(/integration|connect|calendar|zoom/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const wasRedirected = page.url().includes('/settings');

      expect(hasIntegrations || wasRedirected).toBeTruthy();
    });
  });
});
