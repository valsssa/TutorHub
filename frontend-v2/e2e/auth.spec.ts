import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.describe('Login Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
    });

    test('should display login form elements', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByLabel(/password/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /forgot password/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /sign up/i })).toBeVisible();
    });

    test('should show validation errors for empty form submission', async ({ page }) => {
      await page.getByRole('button', { name: /sign in/i }).click();

      await expect(page.getByText(/email is required/i)).toBeVisible();
      await expect(page.getByText(/password is required/i)).toBeVisible();
    });

    test('should show validation error for invalid email format', async ({ page }) => {
      await page.getByLabel(/email/i).fill('invalid-email');
      await page.getByLabel(/password/i).fill('somepassword');
      await page.getByRole('button', { name: /sign in/i }).click();

      await expect(page.getByText(/invalid email/i)).toBeVisible();
    });

    test('should show error message for invalid credentials', async ({ page }) => {
      await page.getByLabel(/email/i).fill('nonexistent@example.com');
      await page.getByLabel(/password/i).fill('WrongPassword123');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Wait for API response and error message
      await expect(page.getByText(/login failed|invalid credentials|unauthorized/i)).toBeVisible({
        timeout: 10000,
      });
    });

    test('should successfully login with valid credentials and redirect to dashboard', async ({ page }) => {
      // Mock successful login response
      await page.route('**/api/v1/auth/login', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-jwt-token',
            token_type: 'bearer',
          }),
        });
      });

      // Mock user me endpoint
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'student@example.com',
            first_name: 'Test',
            last_name: 'Student',
            role: 'student',
          }),
        });
      });

      await page.getByLabel(/email/i).fill('student@example.com');
      await page.getByLabel(/password/i).fill('ValidPassword123');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Should redirect to student dashboard
      await expect(page).toHaveURL(/\/student/);
    });

    test('should navigate to register page via link', async ({ page }) => {
      await page.getByRole('link', { name: /sign up/i }).click();
      await expect(page).toHaveURL('/register');
    });

    test('should navigate to forgot password page via link', async ({ page }) => {
      await page.getByRole('link', { name: /forgot password/i }).click();
      await expect(page).toHaveURL('/forgot-password');
    });

    test('should show loading state during login', async ({ page }) => {
      // Delay the API response to observe loading state
      await page.route('**/api/v1/auth/login', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-jwt-token',
            token_type: 'bearer',
          }),
        });
      });

      await page.getByLabel(/email/i).fill('test@example.com');
      await page.getByLabel(/password/i).fill('ValidPassword123');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Button should show loading state (disabled or loading indicator)
      const submitButton = page.getByRole('button', { name: /sign in/i });
      await expect(submitButton).toBeDisabled();
    });
  });

  test.describe('Logout Flow', () => {
    test.beforeEach(async ({ page }) => {
      // Set up authenticated state
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'student@example.com',
            first_name: 'Test',
            last_name: 'Student',
            role: 'student',
          }),
        });
      });
    });

    test('should logout and redirect to login page', async ({ page }) => {
      // Navigate to dashboard while authenticated
      await page.goto('/student');

      // Find and click logout button (usually in user menu or sidebar)
      const userMenuButton = page.getByRole('button', { name: /logout|sign out|ts/i });

      if (await userMenuButton.isVisible()) {
        await userMenuButton.click();

        // Look for logout option in dropdown
        const logoutOption = page.getByRole('menuitem', { name: /logout|sign out/i })
          .or(page.getByRole('button', { name: /logout|sign out/i }));

        if (await logoutOption.isVisible()) {
          await logoutOption.click();
        }
      }

      // After logout should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Session Persistence', () => {
    test('should maintain session across page refreshes', async ({ page }) => {
      // Mock authenticated state
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'student@example.com',
            first_name: 'Test',
            last_name: 'Student',
            role: 'student',
          }),
        });
      });

      await page.goto('/student');
      await expect(page.getByText(/dashboard/i)).toBeVisible();

      // Refresh the page
      await page.reload();

      // Should still be on dashboard (not redirected to login)
      await expect(page).toHaveURL(/\/student/);
    });

    test('should redirect to login when session expires', async ({ page }) => {
      // First request succeeds
      let requestCount = 0;
      await page.route('**/api/v1/auth/me', async (route) => {
        requestCount++;
        if (requestCount === 1) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 1,
              email: 'student@example.com',
              first_name: 'Test',
              last_name: 'Student',
              role: 'student',
            }),
          });
        } else {
          // Session expired on subsequent requests
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Not authenticated' }),
          });
        }
      });

      await page.goto('/student');
      await page.reload();

      // Should eventually redirect to login after 401
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });
  });
});
