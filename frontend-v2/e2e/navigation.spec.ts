import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated users from /student to /login', async ({ page }) => {
      // Mock unauthenticated state
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/student');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /tutor to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/tutor');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /bookings to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/bookings');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /messages to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/messages');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /wallet to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/wallet');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /settings to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/settings');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /admin to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/admin');

      await expect(page).toHaveURL(/\/login/);
    });

    test('should redirect unauthenticated users from /owner to /login', async ({ page }) => {
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      });

      await page.goto('/owner');

      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Sidebar Navigation (Authenticated)', () => {
    test.beforeEach(async ({ page }) => {
      // Mock authenticated student user
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

      // Mock empty responses for dashboard data
      await page.route('**/api/v1/**', async (route) => {
        if (route.request().url().includes('/auth/me')) {
          return; // Already handled above
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      });
    });

    test('should display sidebar with navigation items for student', async ({ page }) => {
      await page.goto('/student');

      // Check for student-specific navigation items
      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /find tutors/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /my bookings/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /messages/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /packages/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /favorites/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /wallet/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /notifications/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    });

    test('should navigate to tutors page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /find tutors/i }).click();

      await expect(page).toHaveURL('/tutors');
    });

    test('should navigate to bookings page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /my bookings/i }).click();

      await expect(page).toHaveURL('/bookings');
    });

    test('should navigate to messages page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /messages/i }).click();

      await expect(page).toHaveURL('/messages');
    });

    test('should navigate to favorites page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /favorites/i }).click();

      await expect(page).toHaveURL('/favorites');
    });

    test('should navigate to wallet page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /wallet/i }).click();

      await expect(page).toHaveURL('/wallet');
    });

    test('should navigate to settings page', async ({ page }) => {
      await page.goto('/student');

      await page.getByRole('link', { name: /settings/i }).click();

      await expect(page).toHaveURL('/settings');
    });

    test('should highlight active navigation item', async ({ page }) => {
      await page.goto('/bookings');

      const bookingsLink = page.getByRole('link', { name: /my bookings/i });

      // Should have active styling
      await expect(bookingsLink).toHaveClass(/bg-primary|text-primary/);
    });
  });

  test.describe('Tutor Sidebar Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Mock authenticated tutor user
      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            email: 'tutor@example.com',
            first_name: 'Test',
            last_name: 'Tutor',
            role: 'tutor',
          }),
        });
      });

      await page.route('**/api/v1/**', async (route) => {
        if (route.request().url().includes('/auth/me')) {
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      });
    });

    test('should display sidebar with tutor-specific navigation items', async ({ page }) => {
      await page.goto('/tutor');

      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /my bookings/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /messages/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /my profile/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /wallet/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /notifications/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    });
  });

  test.describe('404 Page', () => {
    test('should display 404 page for non-existent routes', async ({ page }) => {
      await page.goto('/this-page-does-not-exist');

      await expect(page.getByRole('heading', { name: /page not found/i })).toBeVisible();
      await expect(page.getByText(/404/i)).toBeVisible();
    });

    test('should have link to go home on 404 page', async ({ page }) => {
      await page.goto('/non-existent-page');

      await expect(page.getByRole('link', { name: /go home/i })).toBeVisible();
    });

    test('should have link to go back on 404 page', async ({ page }) => {
      await page.goto('/non-existent-page');

      await expect(page.getByRole('link', { name: /go back/i })).toBeVisible();
    });

    test('should navigate to home from 404 page', async ({ page }) => {
      await page.goto('/non-existent-page');

      await page.getByRole('link', { name: /go home/i }).click();

      await expect(page).toHaveURL('/');
    });
  });

  test.describe('Header/Topbar Navigation', () => {
    test.beforeEach(async ({ page }) => {
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

      await page.route('**/api/v1/**', async (route) => {
        if (route.request().url().includes('/auth/me')) {
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      });
    });

    test('should display EduStream logo/branding', async ({ page }) => {
      await page.goto('/student');

      await expect(page.getByText(/edustream/i).first()).toBeVisible();
    });

    test('should display user avatar or initials in header', async ({ page }) => {
      await page.goto('/student');

      // Look for avatar or user initials (TS for Test Student)
      const userIndicator = page.getByRole('button', { name: /ts|test student/i })
        .or(page.locator('[data-testid="user-avatar"]'))
        .or(page.getByText(/ts/i).filter({ hasNot: page.getByRole('heading') }));

      await expect(userIndicator.first()).toBeVisible();
    });
  });

  test.describe('Mobile Navigation', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test.beforeEach(async ({ page }) => {
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

      await page.route('**/api/v1/**', async (route) => {
        if (route.request().url().includes('/auth/me')) {
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      });
    });

    test('should show mobile menu toggle on small screens', async ({ page }) => {
      await page.goto('/student');

      // Look for hamburger menu button
      const menuToggle = page.getByRole('button', { name: /menu|toggle/i })
        .or(page.locator('[data-testid="mobile-menu-toggle"]'))
        .or(page.getByLabel(/menu/i));

      await expect(menuToggle.first()).toBeVisible();
    });

    test('should open mobile menu when toggle is clicked', async ({ page }) => {
      await page.goto('/student');

      const menuToggle = page.getByRole('button', { name: /menu|toggle/i })
        .or(page.locator('[data-testid="mobile-menu-toggle"]'))
        .or(page.getByLabel(/menu/i));

      await menuToggle.first().click();

      // Navigation items should become visible
      await expect(page.getByRole('link', { name: /find tutors/i })).toBeVisible();
    });
  });
});
