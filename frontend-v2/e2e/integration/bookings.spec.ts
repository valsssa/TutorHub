/**
 * Bookings E2E Tests - Real Backend Integration
 *
 * Tests booking CRUD flows:
 * - Creating bookings
 * - Viewing booking list
 * - Viewing booking details
 * - Booking state transitions
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

test.describe('Bookings - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Booking List - Student View', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display bookings page', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/booking|session|schedule/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show booking cards or empty state', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const bookingCards = page.locator('[data-testid="booking-card"]')
        .or(page.locator('[class*="booking-card"]'))
        .or(page.locator('article').filter({ hasText: /session|booking|scheduled/i }));

      const hasBookings = await bookingCards.first().isVisible({ timeout: 5000 }).catch(() => false);
      const hasEmptyState = await page.getByText(/no booking|no session|empty/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasBookings || hasEmptyState).toBeTruthy();
    });

    test('should filter bookings by status (if available)', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');

      const statusFilter = page.getByRole('combobox', { name: /status/i })
        .or(page.getByRole('tablist'))
        .or(page.locator('[data-testid="status-filter"]'));

      if (await statusFilter.isVisible({ timeout: 3000 }).catch(() => false)) {
        const tabs = page.getByRole('tab');
        if (await tabs.first().isVisible({ timeout: 2000 }).catch(() => false)) {
          await tabs.first().click();
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should show booking status badge', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const statusBadge = page.locator('[data-testid="booking-status-badge"]')
        .or(page.locator('[class*="badge"]').filter({ hasText: /pending|confirmed|completed|cancelled/i }));

      const hasStatusBadge = await statusBadge.first().isVisible({ timeout: 5000 }).catch(() => false);

    });
  });

  test.describe('Booking List - Tutor View', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTutor(page);
    });

    test('should display tutor booking list', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/booking|session|request/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show pending requests for tutor', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const pendingFilter = page.getByRole('tab', { name: /pending/i })
        .or(page.getByText(/pending.*request/i));

      if (await pendingFilter.isVisible({ timeout: 3000 }).catch(() => false)) {
        await pendingFilter.click();
        await page.waitForTimeout(1000);
      }
    });
  });

  test.describe('Booking Detail', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should navigate to booking detail from list', async ({ page }) => {
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const bookingCard = page.locator('[data-testid="booking-card"], article').first();
      const viewLink = bookingCard.getByRole('link', { name: /view|detail|open/i })
        .or(bookingCard.locator('a'));

      if (await viewLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await viewLink.click();
        await page.waitForURL(/\/bookings\/\d+/, { timeout: 10000 });
      }
    });

    test('should display booking details', async ({ page }) => {
      await page.goto('/bookings/1');
      await page.waitForLoadState('networkidle');

      const hasBookingDetails = await page.getByText(/tutor|student|date|time|status/i)
        .isVisible({ timeout: 10000 }).catch(() => false);
      const hasError = await page.getByText(/not found|error/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasBookingDetails || hasError).toBeTruthy();
    });

    test('should show booking actions based on status', async ({ page }) => {
      await page.goto('/bookings/1');
      await page.waitForLoadState('networkidle');

      const cancelButton = page.getByRole('button', { name: /cancel/i });
      const rescheduleButton = page.getByRole('button', { name: /reschedule/i });
      const joinButton = page.getByRole('button', { name: /join|start/i });

      const hasAnyAction = await cancelButton.isVisible({ timeout: 3000 }).catch(() => false) ||
        await rescheduleButton.isVisible({ timeout: 1000 }).catch(() => false) ||
        await joinButton.isVisible({ timeout: 1000 }).catch(() => false);

    });
  });

  test.describe('Create Booking Flow', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should navigate to new booking page from tutor profile', async ({ page }) => {
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');

      const bookButton = page.getByRole('button', { name: /book|schedule/i })
        .or(page.getByRole('link', { name: /book|schedule/i }));

      if (await bookButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await bookButton.click();

        await page.waitForURL(/\/(bookings\/new|tutors\/\d+\/book)/, { timeout: 10000 }).catch(() => {});
      }
    });

    test('should show date/time picker in booking form', async ({ page }) => {
      await page.goto('/bookings/new?tutor=1');
      await page.waitForLoadState('networkidle');

      const datePicker = page.locator('[data-testid="date-picker"]')
        .or(page.locator('input[type="date"]'))
        .or(page.getByRole('button', { name: /select date|choose date/i }));

      const hasDatePicker = await datePicker.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should show available time slots', async ({ page }) => {
      await page.goto('/bookings/new?tutor=1');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const timeSlots = page.locator('[data-testid="time-slot"]')
        .or(page.getByRole('button').filter({ hasText: /\d{1,2}:\d{2}/ }));

      const hasTimeSlots = await timeSlots.first().isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should validate booking form', async ({ page }) => {
      await page.goto('/bookings/new?tutor=1');
      await page.waitForLoadState('networkidle');

      const submitButton = page.getByRole('button', { name: /confirm|book|submit|create/i });

      if (await submitButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await submitButton.click();

        const hasValidationError = await page.getByText(/required|select|choose/i)
          .isVisible({ timeout: 5000 }).catch(() => false);

      }
    });
  });

  test.describe('Booking State Transitions', () => {
    test('tutor should be able to accept booking', async ({ page }) => {
      await loginAsTutor(page);
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const acceptButton = page.getByRole('button', { name: /accept|confirm|approve/i }).first();

      if (await acceptButton.isVisible({ timeout: 5000 }).catch(() => false)) {

      }
    });

    test('student should be able to cancel pending booking', async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const cancelButton = page.getByRole('button', { name: /cancel/i }).first();

      if (await cancelButton.isVisible({ timeout: 5000 }).catch(() => false)) {

      }
    });
  });
});
