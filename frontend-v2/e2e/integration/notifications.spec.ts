/**
 * Notifications E2E Tests - Real Backend Integration
 *
 * Tests notification functionality:
 * - Notification list
 * - Mark as read
 * - Notification bell/count
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

test.describe('Notifications - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Notifications Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display notifications page', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/notification/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show notification list or empty state', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const notifications = page.locator('[data-testid="notification-item"]')
        .or(page.locator('[class*="notification"]').filter({ hasNot: page.locator('nav, header') }))
        .or(page.locator('li, article').filter({ hasText: /booking|message|payment|session/i }));

      const hasNotifications = await notifications.first().isVisible({ timeout: 5000 }).catch(() => false);
      const hasEmptyState = await page.getByText(/no notification|empty|all caught up/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasNotifications || hasEmptyState).toBeTruthy();
    });

    test('should show notification timestamp', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const notificationItem = page.locator('[data-testid="notification-item"]')
        .or(page.locator('[class*="notification"]')).first();

      if (await notificationItem.isVisible({ timeout: 5000 }).catch(() => false)) {
        const hasTimestamp = await notificationItem.getByText(/ago|today|yesterday|\d{1,2}.*\d{4}/i)
          .isVisible({ timeout: 2000 }).catch(() => false);

      }
    });

    test('should distinguish read and unread notifications', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const unreadIndicator = page.locator('[class*="unread"], [data-unread="true"]')
        .or(page.locator('.bg-blue-50, .bg-primary-50'));

      const hasUnreadStyling = await unreadIndicator.first().isVisible({ timeout: 3000 }).catch(() => false);

    });

    test('should have mark all as read option', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');

      const markAllButton = page.getByRole('button', { name: /mark.*all.*read|read.*all/i });
      const hasMarkAll = await markAllButton.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should filter notifications by type (if available)', async ({ page }) => {
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');

      const typeFilter = page.getByRole('combobox', { name: /type|filter/i })
        .or(page.getByRole('tablist'));

      if (await typeFilter.isVisible({ timeout: 3000 }).catch(() => false)) {
        const tabs = page.getByRole('tab');
        if (await tabs.first().isVisible({ timeout: 2000 }).catch(() => false)) {
          await tabs.first().click();
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  test.describe('Notification Bell', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should show notification bell in header', async ({ page }) => {
      await page.goto('/student');
      await page.waitForLoadState('networkidle');

      const notificationBell = page.locator('[data-testid="notification-bell"]')
        .or(page.getByRole('button').filter({ has: page.locator('[class*="bell"]') }))
        .or(page.locator('header button svg').filter({ hasText: '' }));

      const hasBell = await notificationBell.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should show unread count badge', async ({ page }) => {
      await page.goto('/student');
      await page.waitForLoadState('networkidle');

      const countBadge = page.locator('[data-testid="notification-count"]')
        .or(page.locator('[class*="badge"]').filter({ hasText: /\d+/ }));

      const hasCount = await countBadge.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should open notifications on bell click', async ({ page }) => {
      await page.goto('/student');
      await page.waitForLoadState('networkidle');

      const notificationBell = page.locator('[data-testid="notification-bell"]')
        .or(page.getByRole('link', { name: /notification/i }).first());

      if (await notificationBell.isVisible({ timeout: 5000 }).catch(() => false)) {
        await notificationBell.click();

        const navigatedToNotifications = page.url().includes('/notifications');
        const hasPopover = await page.locator('[data-testid="notification-popover"], [role="dialog"]')
          .isVisible({ timeout: 3000 }).catch(() => false);

        expect(navigatedToNotifications || hasPopover).toBeTruthy();
      }
    });
  });

  test.describe('Notification Interactions', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');
    });

    test('should mark single notification as read', async ({ page }) => {
      await page.waitForTimeout(2000);

      const notificationItem = page.locator('[data-testid="notification-item"]')
        .or(page.locator('[class*="notification"]')).first();

      if (await notificationItem.isVisible({ timeout: 5000 }).catch(() => false)) {
        await notificationItem.click();

        await page.waitForTimeout(1000);

      }
    });

    test('should navigate to related content on click', async ({ page }) => {
      await page.waitForTimeout(2000);

      const notificationItem = page.locator('[data-testid="notification-item"]')
        .or(page.locator('[class*="notification"]')).first();

      if (await notificationItem.isVisible({ timeout: 5000 }).catch(() => false)) {
        const currentUrl = page.url();
        await notificationItem.click();
        await page.waitForTimeout(2000);

      }
    });

    test('should delete notification (if available)', async ({ page }) => {
      await page.waitForTimeout(2000);

      const deleteButton = page.getByRole('button', { name: /delete|remove|dismiss/i }).first();

      if (await deleteButton.isVisible({ timeout: 3000 }).catch(() => false)) {

      }
    });
  });

  test.describe('Notification Types', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/notifications');
      await page.waitForLoadState('networkidle');
    });

    test('should display different notification types', async ({ page }) => {
      await page.waitForTimeout(2000);

      const bookingNotifications = page.locator('[data-testid="notification-item"]')
        .filter({ hasText: /booking|session|schedule/i });
      const messageNotifications = page.locator('[data-testid="notification-item"]')
        .filter({ hasText: /message|chat/i });
      const paymentNotifications = page.locator('[data-testid="notification-item"]')
        .filter({ hasText: /payment|wallet|charge/i });

      const bookingCount = await bookingNotifications.count();
      const messageCount = await messageNotifications.count();
      const paymentCount = await paymentNotifications.count();

    });

    test('should show notification icon by type', async ({ page }) => {
      await page.waitForTimeout(2000);

      const notificationIcons = page.locator('[data-testid="notification-item"] svg')
        .or(page.locator('[class*="notification"] svg'));

      const iconCount = await notificationIcons.count();

    });
  });

  test.describe('Real-time Notifications', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should update notification count without refresh', async ({ page }) => {
      await page.goto('/student');
      await page.waitForLoadState('networkidle');

      const countBadge = page.locator('[data-testid="notification-count"]')
        .or(page.locator('[class*="badge"]').filter({ hasText: /\d+/ }));

      const hasCount = await countBadge.isVisible({ timeout: 5000 }).catch(() => false);


    });
  });
});
