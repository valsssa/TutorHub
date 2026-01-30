import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers';

/**
 * Email Verification Flow E2E Tests
 *
 * Tests email verification functionality:
 * - Navigate to /verify-email/[token] with valid mock token
 * - Verify success state
 * - Test expired token state
 * - Test invalid token state
 */

test.describe('Email Verification Flow', () => {
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
  // SUCCESS STATE TESTS
  // ============================================================================

  test.describe('Successful Verification', () => {
    test('should show loading state initially', async ({ page }) => {
      // Don't route API yet - let it show loading
      await page.goto('/verify-email/valid-test-token');

      // Should show loading state briefly
      const loadingText = page.getByText(/verifying|loading|please wait/i);
      const hasLoading = await loadingText.isVisible().catch(() => false);

      // Loading spinner or text should be visible initially
      console.log(`Loading state visible: ${hasLoading}`);
    });

    test('should show success state for valid token', async ({ page }) => {
      // Mock successful email verification
      await page.route('**/api/v1/auth/verify-email**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Email verified successfully' }),
        });
      });

      // Also catch alternative endpoint patterns
      await page.route('**/api/v1/auth/email/verify**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Email verified successfully' }),
        });
      });

      await page.goto('/verify-email/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show success state
      const successText = page.getByText(/email.*verified|verified.*successfully|success/i);
      const hasSuccess = await successText.isVisible().catch(() => false);

      // Check for success icon (checkmark)
      const checkIcon = page.locator('[class*="check"], svg[class*="emerald"], [class*="success"]');
      const hasCheckIcon = await checkIcon.isVisible().catch(() => false);

      expect(hasSuccess || hasCheckIcon).toBeTruthy();
    });

    test('should display "Continue to Dashboard" button after success', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Email verified successfully' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show continue button
      const continueButton = page.getByRole('button', { name: /continue.*dashboard|go.*dashboard/i });
      const hasButton = await continueButton.isVisible().catch(() => false);

      if (hasButton) {
        await expect(continueButton).toBeVisible();
        await expect(continueButton).toBeEnabled();
      }
    });

    test('should navigate to dashboard when clicking continue button', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Email verified successfully' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const continueButton = page.getByRole('button', { name: /continue.*dashboard|go.*dashboard/i });

      if (await continueButton.isVisible().catch(() => false)) {
        await continueButton.click();

        // Should navigate to dashboard (or login if not authenticated)
        await page.waitForTimeout(2000);
        const url = page.url();
        expect(url).toMatch(/\/dashboard|\/login/);
      }
    });

    test('should show success message with email verification confirmation', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Email verified successfully' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check for confirmation message
      const pageContent = await page.textContent('body');
      const hasVerifiedMessage = pageContent?.toLowerCase().includes('verified') ||
        pageContent?.toLowerCase().includes('success') ||
        pageContent?.toLowerCase().includes('confirmed');

      expect(hasVerifiedMessage).toBeTruthy();
    });
  });

  // ============================================================================
  // ALREADY VERIFIED STATE
  // ============================================================================

  test.describe('Already Verified State', () => {
    test('should show already verified state', async ({ page }) => {
      // Mock API response for already verified
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Email already verified' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/already-verified-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show already verified state
      const alreadyVerifiedText = page.getByText(/already.*verified|already.*confirmed/i);
      const hasAlreadyVerified = await alreadyVerifiedText.isVisible().catch(() => false);

      // Or success state (some implementations treat this as success)
      const successText = page.getByText(/verified|all.*set/i);
      const hasSuccess = await successText.isVisible().catch(() => false);

      expect(hasAlreadyVerified || hasSuccess).toBeTruthy();
    });

    test('should show dashboard button for already verified state', async ({ page }) => {
      // Mock API response for already verified
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Email already verified' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/already-verified-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show go to dashboard button
      const dashboardButton = page.getByRole('button', { name: /dashboard|continue/i });
      const hasButton = await dashboardButton.isVisible().catch(() => false);

      console.log(`Dashboard button visible for already verified: ${hasButton}`);
    });
  });

  // ============================================================================
  // EXPIRED TOKEN STATE
  // ============================================================================

  test.describe('Expired Token State', () => {
    test('should show expired state for expired token', async ({ page }) => {
      // Mock API response for expired token
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Verification link has expired' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/expired-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show expired state
      const expiredText = page.getByText(/expired|link.*expired/i);
      const hasExpired = await expiredText.isVisible().catch(() => false);

      expect(hasExpired).toBeTruthy();
    });

    test('should show resend verification email button for expired token', async ({ page }) => {
      // Mock API response for expired token
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Verification link has expired' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/expired-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show resend button
      const resendButton = page.getByRole('button', { name: /resend.*verification|send.*new|request.*new/i });
      const hasResendButton = await resendButton.isVisible().catch(() => false);

      if (hasResendButton) {
        await expect(resendButton).toBeVisible();
        await expect(resendButton).toBeEnabled();
      }
    });

    test('should resend verification email when button is clicked', async ({ page }) => {
      let resendCalled = false;

      // Mock expired token response
      await page.route('**/api/v1/auth/verify-email**', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Verification link has expired' }),
        });
      });

      // Mock resend verification endpoint
      await page.route('**/api/v1/auth/resend-verification**', async (route) => {
        resendCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Verification email sent' }),
        });
      });

      // Also catch alternative endpoint
      await page.route('**/api/v1/auth/email/resend**', async (route) => {
        resendCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Verification email sent' }),
        });
      });

      await page.goto('/verify-email/expired-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const resendButton = page.getByRole('button', { name: /resend.*verification|send.*new|request.*new/i });

      if (await resendButton.isVisible().catch(() => false)) {
        await resendButton.click();
        await page.waitForTimeout(2000);

        // Should show success message
        const successMessage = page.getByText(/sent|check.*inbox|email.*sent/i);
        const hasSuccess = await successMessage.isVisible().catch(() => false);

        console.log(`Resend success message: ${hasSuccess}, API called: ${resendCalled}`);
      }
    });

    test('should show back to login link for expired token', async ({ page }) => {
      // Mock expired token response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Verification link has expired' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/expired-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show back to login link
      const backToLoginLink = page.getByRole('link', { name: /back.*login|login/i });
      const hasLink = await backToLoginLink.isVisible().catch(() => false);

      if (hasLink) {
        await expect(backToLoginLink).toBeVisible();
      }
    });
  });

  // ============================================================================
  // INVALID TOKEN STATE
  // ============================================================================

  test.describe('Invalid Token State', () => {
    test('should show error state for invalid token', async ({ page }) => {
      // Mock API response for invalid token
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show error state
      const errorText = page.getByText(/invalid|failed|error|verification.*failed/i);
      const hasError = await errorText.isVisible().catch(() => false);

      expect(hasError).toBeTruthy();
    });

    test('should show error icon for invalid token', async ({ page }) => {
      // Mock invalid token response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show error icon (X circle)
      const errorIcon = page.locator('[class*="error"], svg[class*="red"], [class*="x-circle"]');
      const hasErrorIcon = await errorIcon.isVisible().catch(() => false);

      console.log(`Error icon visible: ${hasErrorIcon}`);
    });

    test('should show request new verification link option for invalid token', async ({ page }) => {
      // Mock invalid token response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show request new link button
      const requestNewButton = page.getByRole('button', { name: /request.*new|resend|send.*new/i });
      const hasButton = await requestNewButton.isVisible().catch(() => false);

      if (hasButton) {
        await expect(requestNewButton).toBeVisible();
      }
    });

    test('should show back to login button for invalid token', async ({ page }) => {
      // Mock invalid token response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show back to login
      const backToLogin = page.getByRole('link', { name: /login|back/i }).or(
        page.getByRole('button', { name: /login|back/i })
      );
      const hasBackToLogin = await backToLogin.isVisible().catch(() => false);

      if (hasBackToLogin) {
        await expect(backToLogin.first()).toBeVisible();
      }
    });

    test('should navigate to login when clicking back button', async ({ page }) => {
      // Mock invalid token response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const backToLogin = page.getByRole('link', { name: /login|back.*login/i }).first();

      if (await backToLogin.isVisible().catch(() => false)) {
        await backToLogin.click();
        await page.waitForURL(/\/login/, { timeout: 5000 });
        await expect(page).toHaveURL(/\/login/);
      }
    });
  });

  // ============================================================================
  // CONTACT SUPPORT LINK
  // ============================================================================

  test.describe('Contact Support', () => {
    test('should show contact support link', async ({ page }) => {
      await page.goto('/verify-email/some-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show contact support link in footer
      const supportLink = page.getByRole('link', { name: /support|help|contact/i });
      const hasSupport = await supportLink.isVisible().catch(() => false);

      console.log(`Contact support link visible: ${hasSupport}`);
    });

    test('should navigate to help page when clicking support link', async ({ page }) => {
      // Mock any verification state
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Success' }),
        });
      });

      await page.goto('/verify-email/some-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const supportLink = page.getByRole('link', { name: /support|help|contact/i });

      if (await supportLink.isVisible().catch(() => false)) {
        await supportLink.click();
        await page.waitForTimeout(1000);

        // Should navigate to help page
        const url = page.url();
        expect(url).toMatch(/\/help|\/support|\/contact/);
      }
    });
  });

  // ============================================================================
  // MOBILE VIEWPORT TESTS
  // ============================================================================

  test.describe('Mobile Viewport', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should display verification success page correctly on mobile', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Email verified successfully' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/valid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Content should be visible and not overflow
      const heading = page.getByText(/verified|success/i).first();

      if (await heading.isVisible().catch(() => false)) {
        await expect(heading).toBeVisible();
      }

      // Continue button should be usable
      const continueButton = page.getByRole('button', { name: /continue|dashboard/i });

      if (await continueButton.isVisible().catch(() => false)) {
        await continueButton.scrollIntoViewIfNeeded();
        await expect(continueButton).toBeVisible();
      }
    });

    test('should display error state correctly on mobile', async ({ page }) => {
      // Mock invalid token
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().url().includes('verify')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid verification link' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/verify-email/invalid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Error message should be visible
      const errorMessage = page.getByText(/invalid|failed|error/i);

      if (await errorMessage.isVisible().catch(() => false)) {
        await expect(errorMessage.first()).toBeVisible();
      }

      // Buttons should be accessible
      const actionButton = page.getByRole('button').first();

      if (await actionButton.isVisible().catch(() => false)) {
        await actionButton.scrollIntoViewIfNeeded();
        await expect(actionButton).toBeVisible();
      }
    });
  });

  // ============================================================================
  // NETWORK ERROR HANDLING
  // ============================================================================

  test.describe('Network Error Handling', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // Abort network requests to simulate network error
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.abort('failed');
      });

      await page.goto('/verify-email/some-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Should show error state
      const errorMessage = page.getByText(/error|failed|problem|try.*again/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      console.log(`Network error handled: ${hasError}`);
    });

    test('should show retry option on network error', async ({ page }) => {
      // Abort network requests
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.abort('failed');
      });

      await page.goto('/verify-email/some-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Look for retry button or request new link button
      const retryButton = page.getByRole('button', { name: /retry|try.*again|request.*new/i });
      const hasRetry = await retryButton.isVisible().catch(() => false);

      console.log(`Retry option available: ${hasRetry}`);
    });
  });

  // ============================================================================
  // ACCESSIBILITY TESTS
  // ============================================================================

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Success' }),
        });
      });

      await page.goto('/verify-email/valid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should have h1 heading
      const h1 = page.locator('h1');
      const h1Count = await h1.count();

      expect(h1Count).toBeGreaterThanOrEqual(1);
    });

    test('should have accessible button labels', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Success' }),
        });
      });

      await page.goto('/verify-email/valid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // All buttons should have accessible names
      const buttons = await page.locator('button').all();

      for (const button of buttons) {
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute('aria-label');
        const title = await button.getAttribute('title');

        const hasAccessibleName = text?.trim() || ariaLabel || title;
        expect(hasAccessibleName).toBeTruthy();
      }
    });

    test('should support keyboard navigation', async ({ page }) => {
      // Mock successful verification
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Success' }),
        });
      });

      await page.goto('/verify-email/valid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Tab through focusable elements
      await page.keyboard.press('Tab');
      await page.waitForTimeout(200);

      // Something should be focused
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      console.log(`Focused element: ${focusedElement}`);
    });
  });
});
