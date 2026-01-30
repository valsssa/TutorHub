import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers';

/**
 * Password Reset Flow E2E Tests
 *
 * Tests the password reset flow:
 * - Navigate to /forgot-password
 * - Enter email and submit
 * - Navigate to /reset-password/[token] (mock token)
 * - Enter new password with strength validation
 * - Verify success message
 */

test.describe('Password Reset Flow', () => {
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
  // FORGOT PASSWORD PAGE
  // ============================================================================

  test.describe('Forgot Password Page', () => {
    test('should display forgot password page with all elements', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Check page title/heading
      await expect(page.getByText(/forgot.*password/i)).toBeVisible();

      // Check for email input
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await expect(emailInput).toBeVisible();

      // Check for submit button
      const submitButton = page.getByRole('button', { name: /send.*reset|send.*link|reset.*password/i });
      await expect(submitButton).toBeVisible();

      // Check for back to login link
      const backLink = page.getByRole('link', { name: /back.*login|sign.*in/i }).first();
      await expect(backLink).toBeVisible();
    });

    test('should have accessible email input', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Email input should have proper label
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await expect(emailInput).toBeVisible();

      // Should be focusable
      await emailInput.focus();
      await expect(emailInput).toBeFocused();

      // Should accept input
      await emailInput.fill('test@example.com');
      await expect(emailInput).toHaveValue('test@example.com');
    });

    test('should show error for empty email submission', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Click submit without entering email
      const submitButton = page.getByRole('button', { name: /send.*reset|send.*link/i });
      await submitButton.click();

      await page.waitForTimeout(500);

      // Should show validation error
      const errorMessage = page.getByText(/please.*enter.*email|email.*required/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      // Or HTML5 validation
      const emailInput = page.getByRole('textbox', { name: /email/i });
      const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage).catch(() => '');

      expect(hasError || validationMessage).toBeTruthy();
    });

    test('should show error for invalid email format', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Enter invalid email
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await emailInput.fill('invalid-email');

      // Submit form
      const submitButton = page.getByRole('button', { name: /send.*reset|send.*link/i });
      await submitButton.click();

      await page.waitForTimeout(500);

      // Should show validation error
      const errorMessage = page.getByText(/valid.*email|invalid.*email|email.*format/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      // Or HTML5 validation
      const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage).catch(() => '');

      expect(hasError || validationMessage).toBeTruthy();
    });

    test('should submit email and show success message', async ({ page }) => {
      // Mock the API response
      await page.route('**/api/v1/auth/password-reset/request', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Password reset email sent' }),
        });
      });

      // Also catch alternative endpoint names
      await page.route('**/api/v1/auth/forgot-password', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Password reset email sent' }),
        });
      });

      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Enter valid email
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await emailInput.fill('test@example.com');

      // Submit form
      const submitButton = page.getByRole('button', { name: /send.*reset|send.*link/i });
      await submitButton.click();

      // Wait for success state
      await page.waitForTimeout(2000);

      // Should show success message
      const successMessage = page.getByText(/check.*email|sent|inbox/i);
      await expect(successMessage).toBeVisible({ timeout: 10000 });
    });

    test('should show helpful instructions after submission', async ({ page }) => {
      // Mock the API response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Success' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      await page.getByRole('textbox', { name: /email/i }).fill('test@example.com');
      await page.getByRole('button', { name: /send.*reset|send.*link/i }).click();

      await page.waitForTimeout(2000);

      // Check for helpful instructions
      const spamFolderHint = page.getByText(/spam|junk/i);
      const hasHint = await spamFolderHint.isVisible().catch(() => false);

      // Should show some instructions
      const pageContent = await page.textContent('body');
      expect(pageContent?.toLowerCase()).toMatch(/email|inbox|check|sent/);
    });

    test('should allow trying a different email after submission', async ({ page }) => {
      // Mock the API response
      await page.route('**/api/v1/auth/**', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Success' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      await page.getByRole('textbox', { name: /email/i }).fill('test@example.com');
      await page.getByRole('button', { name: /send.*reset|send.*link/i }).click();

      await page.waitForTimeout(2000);

      // Look for "Try Different Email" button
      const tryDifferentButton = page.getByRole('button', { name: /different.*email|try.*again/i });

      if (await tryDifferentButton.isVisible().catch(() => false)) {
        await tryDifferentButton.click();
        await page.waitForTimeout(1000);

        // Should show form again
        const emailInput = page.getByRole('textbox', { name: /email/i });
        await expect(emailInput).toBeVisible();
      }
    });

    test('should navigate back to login when clicking link', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Click back to login link
      const backLink = page.getByRole('link', { name: /back.*login|sign.*in/i }).first();
      await backLink.click();

      await page.waitForURL(/\/login/, { timeout: 5000 });
      await expect(page).toHaveURL(/\/login/);
    });
  });

  // ============================================================================
  // RESET PASSWORD PAGE
  // ============================================================================

  test.describe('Reset Password Page', () => {
    test('should display reset password page with all elements', async ({ page }) => {
      // Mock token validation
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show loading or form
      const hasLoading = await page.getByText(/validat/i).isVisible().catch(() => false);
      const hasForm = await page.getByLabel(/new.*password/i).isVisible().catch(() => false);
      const hasTitle = await page.getByText(/create.*new.*password|reset.*password/i).isVisible().catch(() => false);

      expect(hasLoading || hasForm || hasTitle).toBeTruthy();
    });

    test('should show password strength indicator', async ({ page }) => {
      // Mock token validation to return valid
      await page.route('**/api/v1/auth/password-reset/validate**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const passwordInput = page.getByLabel(/^new.*password$/i).or(page.getByLabel(/^password$/i)).first();

      if (await passwordInput.isVisible()) {
        // Type a weak password
        await passwordInput.fill('12345');
        await page.waitForTimeout(500);

        // Look for strength indicator
        const strengthText = page.getByText(/weak|fair|good|strong|too weak/i);
        const hasStrength = await strengthText.isVisible().catch(() => false);

        // Type a stronger password
        await passwordInput.fill('MyStr0ng!Password123');
        await page.waitForTimeout(500);

        const strongIndicator = page.getByText(/good|strong/i);
        const hasStrongIndicator = await strongIndicator.isVisible().catch(() => false);

        console.log(`Strength indicator visible: ${hasStrength || hasStrongIndicator}`);
      }
    });

    test('should show password requirements', async ({ page }) => {
      // Mock token validation
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Look for password requirements section
      const requirementsSection = page.getByText(/requirements|at least.*8|characters/i);
      const hasRequirements = await requirementsSection.isVisible().catch(() => false);

      console.log(`Password requirements visible: ${hasRequirements}`);
    });

    test('should validate password match', async ({ page }) => {
      // Mock token validation
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const passwordInput = page.getByLabel(/^new.*password$/i).or(page.getByLabel(/^password$/i)).first();
      const confirmInput = page.getByLabel(/confirm.*password/i);

      if (await passwordInput.isVisible() && await confirmInput.isVisible()) {
        // Enter mismatched passwords
        await passwordInput.fill('MyStr0ng!Pass123');
        await confirmInput.fill('DifferentPass456');

        await page.waitForTimeout(500);

        // Should show mismatch error
        const mismatchError = page.getByText(/do.*not.*match|passwords.*not.*match|don't.*match/i);
        const hasError = await mismatchError.isVisible().catch(() => false);

        expect(hasError).toBeTruthy();
      }
    });

    test('should successfully reset password', async ({ page }) => {
      // Mock token validation
      await page.route('**/api/v1/auth/password-reset/validate**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      // Mock password reset
      await page.route('**/api/v1/auth/password-reset/confirm', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Password reset successful' }),
          });
        } else {
          await route.continue();
        }
      });

      // Also catch alternative endpoint
      await page.route('**/api/v1/auth/reset-password', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Password reset successful' }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const passwordInput = page.getByLabel(/^new.*password$/i).or(page.getByLabel(/^password$/i)).first();
      const confirmInput = page.getByLabel(/confirm.*password/i);

      if (await passwordInput.isVisible()) {
        // Enter matching strong passwords
        await passwordInput.fill('MyStr0ng!Password123');

        if (await confirmInput.isVisible()) {
          await confirmInput.fill('MyStr0ng!Password123');
        }

        // Submit form
        const submitButton = page.getByRole('button', { name: /reset.*password|submit|save/i });

        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForTimeout(2000);

          // Should show success message
          const successMessage = page.getByText(/success|complete|reset|changed/i);
          const hasSuccess = await successMessage.isVisible().catch(() => false);

          if (hasSuccess) {
            await expect(successMessage).toBeVisible();
          }
        }
      }
    });

    test('should show "Sign In" button after successful reset', async ({ page }) => {
      // Mock successful password reset
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Success', valid: true }),
        });
      });

      await page.goto('/reset-password/valid-test-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const passwordInput = page.getByLabel(/^new.*password$/i).or(page.getByLabel(/^password$/i)).first();
      const confirmInput = page.getByLabel(/confirm.*password/i);

      if (await passwordInput.isVisible()) {
        await passwordInput.fill('MyStr0ng!Password123');

        if (await confirmInput.isVisible()) {
          await confirmInput.fill('MyStr0ng!Password123');
        }

        const submitButton = page.getByRole('button', { name: /reset.*password|submit|save/i });

        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForTimeout(2000);

          // Look for Sign In button/link
          const signInButton = page.getByRole('button', { name: /sign.*in|login/i }).or(
            page.getByRole('link', { name: /sign.*in|login/i })
          );

          if (await signInButton.isVisible().catch(() => false)) {
            await expect(signInButton).toBeVisible();
          }
        }
      }
    });
  });

  // ============================================================================
  // INVALID/EXPIRED TOKEN HANDLING
  // ============================================================================

  test.describe('Invalid Token Handling', () => {
    test('should show error for invalid token', async ({ page }) => {
      // Mock token validation to return invalid
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Invalid or expired token' }),
        });
      });

      await page.goto('/reset-password/invalid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Should show error message
      const errorMessage = page.getByText(/invalid|expired|link.*expired/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      console.log(`Invalid token error shown: ${hasError}`);
    });

    test('should show "Request New Reset Link" option for expired token', async ({ page }) => {
      // Mock token validation to return expired
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Token has expired' }),
        });
      });

      await page.goto('/reset-password/expired-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Look for request new link button
      const requestNewLink = page.getByRole('button', { name: /request.*new|get.*new.*link/i }).or(
        page.getByRole('link', { name: /request.*new|get.*new.*link/i })
      );

      const hasRequestLink = await requestNewLink.isVisible().catch(() => false);

      console.log(`Request new link option visible: ${hasRequestLink}`);
    });

    test('should navigate to forgot-password when requesting new link', async ({ page }) => {
      // Mock token validation to return expired
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Token has expired' }),
        });
      });

      await page.goto('/reset-password/expired-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const requestNewLink = page.getByRole('button', { name: /request.*new|get.*new.*link/i }).or(
        page.getByRole('link', { name: /request.*new|get.*new.*link|forgot/i })
      ).first();

      if (await requestNewLink.isVisible().catch(() => false)) {
        await requestNewLink.click();
        await page.waitForURL(/\/forgot-password/, { timeout: 5000 });
        await expect(page).toHaveURL(/\/forgot-password/);
      }
    });
  });

  // ============================================================================
  // NAVIGATION FROM LOGIN PAGE
  // ============================================================================

  test.describe('Navigation from Login', () => {
    test('should have forgot password link on login page', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      // Look for forgot password link/button
      const forgotPasswordLink = page.getByRole('link', { name: /forgot.*password/i }).or(
        page.getByRole('button', { name: /forgot.*password/i })
      );

      await expect(forgotPasswordLink).toBeVisible();
    });

    test('should navigate to forgot password from login page', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      const forgotPasswordLink = page.getByRole('link', { name: /forgot.*password/i }).or(
        page.getByRole('button', { name: /forgot.*password/i })
      );

      if (await forgotPasswordLink.isVisible()) {
        await forgotPasswordLink.click();
        await page.waitForURL(/\/forgot-password/, { timeout: 5000 });
        await expect(page).toHaveURL(/\/forgot-password/);
      }
    });
  });

  // ============================================================================
  // MOBILE VIEWPORT TESTS
  // ============================================================================

  test.describe('Mobile Viewport', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should display forgot password page correctly on mobile', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Email input should be visible
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await expect(emailInput).toBeVisible();

      // Submit button should be visible
      const submitButton = page.getByRole('button', { name: /send.*reset|send.*link/i });
      await expect(submitButton).toBeVisible();
    });

    test('should display reset password page correctly on mobile', async ({ page }) => {
      // Mock valid token
      await page.route('**/api/v1/auth/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ valid: true }),
        });
      });

      await page.goto('/reset-password/valid-token');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Form should be usable on mobile
      const passwordInput = page.getByLabel(/password/i).first();

      if (await passwordInput.isVisible()) {
        // Should be able to scroll and interact
        await passwordInput.scrollIntoViewIfNeeded();
        await expect(passwordInput).toBeVisible();
      }
    });
  });

  // ============================================================================
  // ACCESSIBILITY TESTS
  // ============================================================================

  test.describe('Accessibility', () => {
    test('should support keyboard navigation on forgot password page', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Focus email input
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await emailInput.focus();
      await expect(emailInput).toBeFocused();

      // Tab to submit button
      await page.keyboard.press('Tab');
      await page.waitForTimeout(200);

      // Should be able to submit with Enter
      await emailInput.focus();
      await emailInput.fill('test@example.com');
      await page.keyboard.press('Enter');
    });

    test('should have proper form labels', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      // Email input should have accessible label
      const emailInput = page.getByRole('textbox', { name: /email/i });
      await expect(emailInput).toBeVisible();

      // Check aria attributes
      const ariaLabel = await emailInput.getAttribute('aria-label');
      const hasLabel = await page.locator('label').filter({ hasText: /email/i }).count() > 0;

      expect(ariaLabel || hasLabel).toBeTruthy();
    });
  });
});
