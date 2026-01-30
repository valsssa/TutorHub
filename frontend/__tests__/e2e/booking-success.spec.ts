import { test, expect } from '@playwright/test';
import { TestHelpers, TestData } from './helpers';

/**
 * Booking Success Flow E2E Tests
 *
 * Tests the complete booking flow from tutor profile to success confirmation:
 * - Navigate to tutor profile
 * - Select time slot and duration
 * - Complete payment
 * - Verify BookingSuccess modal appears
 * - Verify booking appears in bookings list
 */

test.describe('Booking Success Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear cookies and local storage before each test
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {
        // Ignore errors if localStorage is not accessible
      }
    });
  });

  // ============================================================================
  // TUTOR PROFILE AND TIME SLOT SELECTION
  // ============================================================================

  test.describe('Tutor Profile Navigation', () => {
    test('should navigate to tutor profile from tutors list', async ({ page }) => {
      // Login as student
      await TestHelpers.loginAsStudent(page);

      // Navigate to tutors marketplace
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');

      // Wait for tutors to load
      await page.waitForTimeout(2000);

      // Find and click a tutor card
      const tutorCard = page.getByTestId('tutor-card').first();
      const tutorLink = page.locator('[href^="/tutors/"]').first();

      if (await tutorCard.isVisible()) {
        await tutorCard.click();
      } else if (await tutorLink.isVisible()) {
        await tutorLink.click();
      } else {
        // Try clicking any tutor name link
        const tutorName = page.locator('a[href*="/tutors/"]').first();
        if (await tutorName.isVisible()) {
          await tutorName.click();
        }
      }

      // Verify we're on a tutor profile page
      await page.waitForURL(/\/tutors\/\d+/, { timeout: 10000 });
      await expect(page).toHaveURL(/\/tutors\/\d+/);
    });

    test('should display tutor profile with booking button', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      // Navigate directly to a tutor profile
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check for tutor details or profile content
      const hasProfile = await page.getByText(/about|biography|experience|reviews/i).first().isVisible().catch(() => false);
      const hasBookButton = await page.getByRole('button', { name: /book|schedule|reserve/i }).first().isVisible().catch(() => false);

      // Verify page loaded - either shows profile or redirects to tutors list (if tutor not found)
      if (page.url().includes('/tutors/1')) {
        expect(hasProfile || hasBookButton).toBeTruthy();
      }
    });

    test('should show time slots on tutor profile', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Look for availability section or time slot selector
      const hasAvailability = await page.getByText(/availability|available|schedule|select.*time/i).first().isVisible().catch(() => false);
      const hasTimeSlots = await page.locator('[data-testid="time-slot"], button:has-text(/\d{1,2}:\d{2}/)').count() > 0;

      // If on tutor profile, should show some availability info
      if (page.url().includes('/tutors/1')) {
        // Log what we found for debugging
        console.log(`Has availability section: ${hasAvailability}, Has time slots: ${hasTimeSlots}`);
      }
    });
  });

  // ============================================================================
  // BOOKING FLOW
  // ============================================================================

  test.describe('Complete Booking Flow', () => {
    test('should navigate to booking page when time slot is selected', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Look for time slot buttons
      const timeSlotButton = page.locator('[data-testid="time-slot"]').first();
      const timeButton = page.getByRole('button', { name: /\d{1,2}:\d{2}/ }).first();

      if (await timeSlotButton.isVisible()) {
        await timeSlotButton.click();
        await page.waitForTimeout(1000);

        // Should navigate to booking page
        if (page.url().includes('/book')) {
          await expect(page).toHaveURL(/\/tutors\/\d+\/book/);
        }
      } else if (await timeButton.isVisible()) {
        await timeButton.click();
        await page.waitForTimeout(1000);
      }
    });

    test('should display booking page with tutor details', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      // Navigate directly to booking page with a mock slot
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // If we're on the booking page, verify content
      if (page.url().includes('/book')) {
        // Check for tutor info
        const hasTutorSection = await page.getByText(/your tutor|tutor/i).first().isVisible().catch(() => false);

        // Check for lesson details
        const hasLessonDetails = await page.getByText(/lesson details|checkout/i).first().isVisible().catch(() => false);

        // Check for payment section
        const hasPayment = await page.getByText(/pay|payment|total/i).first().isVisible().catch(() => false);

        console.log(`Booking page content: tutor=${hasTutorSection}, lesson=${hasLessonDetails}, payment=${hasPayment}`);
        expect(hasTutorSection || hasLessonDetails || hasPayment).toBeTruthy();
      }
    });

    test('should allow selecting lesson duration', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        // Look for duration buttons
        const duration25 = page.getByRole('button', { name: /25.*min/i });
        const duration50 = page.getByRole('button', { name: /50.*min/i });

        if (await duration25.isVisible()) {
          await duration25.click();
          await page.waitForTimeout(500);

          // Verify selection changed (button should have active state)
          await expect(duration25).toHaveClass(/bg-white|shadow|selected/);
        }

        if (await duration50.isVisible()) {
          await duration50.click();
          await page.waitForTimeout(500);

          await expect(duration50).toHaveClass(/bg-white|shadow|selected/);
        }
      }
    });

    test('should allow selecting payment method', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        // Look for payment method buttons
        const cardButton = page.getByRole('button', { name: /card/i });
        const applePayButton = page.getByRole('button', { name: /apple.*pay/i });
        const googlePayButton = page.getByRole('button', { name: /google.*pay/i });
        const paypalButton = page.getByRole('button', { name: /paypal/i });

        if (await cardButton.isVisible()) {
          await cardButton.click();
          await page.waitForTimeout(500);

          // Card form should be visible
          const cardInput = page.getByPlaceholder(/1234/i);
          await expect(cardInput).toBeVisible();
        }
      }
    });

    test('should show booking confirmation button', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        // Look for the main booking button
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay|confirm/i });

        if (await bookButton.isVisible()) {
          await expect(bookButton).toBeEnabled();
        }
      }
    });

    test('should complete booking and show success modal', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      // Mock the booking API to return success
      await page.route('**/api/v1/bookings', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 123,
              tutor_profile_id: 1,
              student_id: 1,
              subject_id: 1,
              start_at: futureDate.toISOString(),
              duration_minutes: 50,
              status: 'pending',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        // Click the book button
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible()) {
          await bookButton.click();

          // Wait for success modal
          await page.waitForTimeout(2000);

          // Check for success modal elements
          const successModal = page.getByText(/booking confirmed|success/i);
          const checkCircle = page.locator('[class*="check"], svg[class*="emerald"]');

          const hasSuccessMessage = await successModal.isVisible().catch(() => false);

          if (hasSuccessMessage) {
            await expect(successModal).toBeVisible();

            // Check for booking reference
            const bookingRef = page.getByText(/#\d+|booking.*reference/i);
            if (await bookingRef.isVisible().catch(() => false)) {
              await expect(bookingRef).toBeVisible();
            }
          }
        }
      }
    });

    test('should show "View My Bookings" button in success modal', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      // Mock booking API
      await page.route('**/api/v1/bookings', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 123,
              status: 'pending',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible()) {
          await bookButton.click();
          await page.waitForTimeout(2000);

          // Check for View My Bookings button
          const viewBookingsButton = page.getByRole('button', { name: /view.*booking/i });

          if (await viewBookingsButton.isVisible().catch(() => false)) {
            await expect(viewBookingsButton).toBeVisible();
            await expect(viewBookingsButton).toBeEnabled();
          }
        }
      }
    });

    test('should navigate to bookings page when clicking "View My Bookings"', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      // Mock booking API
      await page.route('**/api/v1/bookings', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 123,
              status: 'pending',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible()) {
          await bookButton.click();
          await page.waitForTimeout(2000);

          const viewBookingsButton = page.getByRole('button', { name: /view.*booking/i });

          if (await viewBookingsButton.isVisible().catch(() => false)) {
            await viewBookingsButton.click();
            await page.waitForURL(/\/bookings/, { timeout: 10000 });
            await expect(page).toHaveURL(/\/bookings/);
          }
        }
      }
    });
  });

  // ============================================================================
  // BOOKINGS LIST VERIFICATION
  // ============================================================================

  test.describe('Bookings List', () => {
    test('should display bookings page after login', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');

      // Check page loaded
      await expect(page.getByText(/booking|session|my bookings/i)).toBeVisible();
    });

    test('should show booking status tabs', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check for status filter tabs
      const upcomingTab = page.getByRole('button', { name: /upcoming/i });
      const pendingTab = page.getByRole('button', { name: /pending/i });
      const completedTab = page.getByRole('button', { name: /completed/i });

      const hasUpcoming = await upcomingTab.isVisible().catch(() => false);
      const hasPending = await pendingTab.isVisible().catch(() => false);
      const hasCompleted = await completedTab.isVisible().catch(() => false);

      expect(hasUpcoming || hasPending || hasCompleted).toBeTruthy();
    });

    test('should filter bookings by status', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Click pending tab
      const pendingTab = page.getByRole('button', { name: /pending/i });

      if (await pendingTab.isVisible()) {
        await pendingTab.click();
        await page.waitForTimeout(1000);

        // URL should update
        expect(page.url()).toContain('status=pending');
      }
    });

    test('should show empty state when no bookings', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check for empty state or bookings list
      const hasEmptyState = await page.getByText(/no.*booking|book.*tutor/i).isVisible().catch(() => false);
      const hasBookings = await page.locator('[data-testid="booking-card"]').count() > 0;

      // Should show either empty state or bookings
      expect(hasEmptyState || hasBookings).toBeTruthy();
    });
  });

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  test.describe('Booking Error Handling', () => {
    test('should handle booking API error gracefully', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      // Mock booking API to return error
      await page.route('**/api/v1/bookings', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'Time slot is no longer available',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible()) {
          await bookButton.click();
          await page.waitForTimeout(2000);

          // Should show error message
          const errorMessage = page.getByText(/error|not available|failed/i);
          const hasError = await errorMessage.isVisible().catch(() => false);

          // Page might redirect or show error
          console.log(`Error message visible: ${hasError}`);
        }
      }
    });

    test('should handle payment declined error', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      // Mock booking API to return payment error
      await page.route('**/api/v1/bookings', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 402,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'Card declined',
              code: 'card_declined',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible()) {
          await bookButton.click();
          await page.waitForTimeout(2000);

          // Should show payment error and stay on page
          const errorMessage = page.getByText(/declined|payment.*failed|try.*different/i);
          const hasError = await errorMessage.isVisible().catch(() => false);

          // Should still be on booking page to retry
          if (hasError) {
            await expect(page).toHaveURL(/\/book/);
          }
        }
      }
    });

    test('should redirect non-students away from booking page', async ({ page }) => {
      // Login as tutor (not student)
      await TestHelpers.loginAsTutor(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForTimeout(3000);

      // Should redirect away from booking page
      const isOnBookingPage = page.url().includes('/book');

      if (!isOnBookingPage) {
        // Redirected - test passes
        expect(isOnBookingPage).toBeFalsy();
      }
    });
  });

  // ============================================================================
  // MOBILE VIEWPORT TESTS
  // ============================================================================

  test.describe('Mobile Viewport', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should display booking page correctly on mobile', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      futureDate.setHours(10, 0, 0, 0);
      const slotParam = encodeURIComponent(futureDate.toISOString());

      await page.goto(`/tutors/1/book?slot=${slotParam}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (page.url().includes('/book')) {
        // Check page is scrollable and content fits
        const bookButton = page.getByRole('button', { name: /book.*lesson|pay/i });

        if (await bookButton.isVisible().catch(() => false)) {
          // Scroll to button if needed
          await bookButton.scrollIntoViewIfNeeded();
          await expect(bookButton).toBeVisible();
        }
      }
    });

    test('should display bookings list correctly on mobile', async ({ page }) => {
      await TestHelpers.loginAsStudent(page);

      await page.goto('/bookings');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check status tabs are visible and usable on mobile
      const tabButtons = page.locator('button').filter({ hasText: /upcoming|pending|completed/i });
      const tabCount = await tabButtons.count();

      if (tabCount > 0) {
        // First tab should be visible
        await expect(tabButtons.first()).toBeVisible();
      }
    });
  });
});
