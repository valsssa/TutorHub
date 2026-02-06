import { test, expect } from '@playwright/test';

test.describe('Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test.describe('Registration Form Display', () => {
    test('should display registration form elements', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /create your account/i })).toBeVisible();

      // Role selection buttons
      await expect(page.getByRole('button', { name: /learn/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /teach/i })).toBeVisible();

      // Form fields
      await expect(page.getByLabel(/first name/i)).toBeVisible();
      await expect(page.getByLabel(/last name/i)).toBeVisible();
      await expect(page.getByLabel(/^email$/i)).toBeVisible();
      await expect(page.getByLabel(/^password$/i)).toBeVisible();
      await expect(page.getByLabel(/confirm password/i)).toBeVisible();

      // Submit button
      await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();

      // Login link
      await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
    });

    test('should default to student role', async ({ page }) => {
      const learnButton = page.getByRole('button', { name: /learn/i });

      // Student role button should have active/selected styling
      await expect(learnButton).toHaveClass(/border-primary|bg-primary/);
    });

    test('should accept role from URL query parameter', async ({ page }) => {
      await page.goto('/register?role=tutor');

      const teachButton = page.getByRole('button', { name: /teach/i });

      // Tutor role button should have active/selected styling
      await expect(teachButton).toHaveClass(/border-primary|bg-primary/);
    });
  });

  test.describe('Role Selection', () => {
    test('should allow switching between student and tutor roles', async ({ page }) => {
      const learnButton = page.getByRole('button', { name: /learn/i });
      const teachButton = page.getByRole('button', { name: /teach/i });

      // Initially student is selected
      await expect(learnButton).toHaveClass(/border-primary|bg-primary/);

      // Click tutor role
      await teachButton.click();

      // Now tutor should be selected
      await expect(teachButton).toHaveClass(/border-primary|bg-primary/);

      // Click back to student
      await learnButton.click();

      // Student should be selected again
      await expect(learnButton).toHaveClass(/border-primary|bg-primary/);
    });
  });

  test.describe('Form Validation', () => {
    test('should show validation errors for empty form submission', async ({ page }) => {
      await page.getByRole('button', { name: /create account/i }).click();

      await expect(page.getByText(/first name is required/i)).toBeVisible();
      await expect(page.getByText(/last name is required/i)).toBeVisible();
      await expect(page.getByText(/email is required/i)).toBeVisible();
    });

    test('should show validation error for invalid email', async ({ page }) => {
      await page.getByLabel(/first name/i).fill('John');
      await page.getByLabel(/last name/i).fill('Doe');
      await page.getByLabel(/^email$/i).fill('invalid-email');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('ValidPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      await expect(page.getByText(/invalid email/i)).toBeVisible();
    });

    test('should show validation errors for weak password', async ({ page }) => {
      await page.getByLabel(/first name/i).fill('John');
      await page.getByLabel(/last name/i).fill('Doe');
      await page.getByLabel(/^email$/i).fill('john@example.com');
      await page.getByLabel(/^password$/i).fill('weak');
      await page.getByLabel(/confirm password/i).fill('weak');

      await page.getByRole('button', { name: /create account/i }).click();

      // Should show one or more password validation errors
      await expect(page.getByText(/at least 8 characters|uppercase|lowercase|number/i)).toBeVisible();
    });

    test('should show error when passwords do not match', async ({ page }) => {
      await page.getByLabel(/first name/i).fill('John');
      await page.getByLabel(/last name/i).fill('Doe');
      await page.getByLabel(/^email$/i).fill('john@example.com');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('DifferentPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      await expect(page.getByText(/passwords do not match/i)).toBeVisible();
    });

    test('should show password requirements hint', async ({ page }) => {
      await expect(page.getByText(/min 8 characters|uppercase.*lowercase.*number/i)).toBeVisible();
    });
  });

  test.describe('Successful Registration', () => {
    test('should successfully register as student and redirect to login', async ({ page }) => {
      // Mock successful registration
      await page.route('**/api/v1/auth/register', async (route) => {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'newstudent@example.com',
            first_name: 'New',
            last_name: 'Student',
            role: 'student',
          }),
        });
      });

      await page.getByLabel(/first name/i).fill('New');
      await page.getByLabel(/last name/i).fill('Student');
      await page.getByLabel(/^email$/i).fill('newstudent@example.com');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('ValidPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      // Should redirect to login page with success indicator
      await expect(page).toHaveURL(/\/login.*registered=true/);
    });

    test('should successfully register as tutor', async ({ page }) => {
      // Mock successful registration
      await page.route('**/api/v1/auth/register', async (route) => {
        const requestBody = JSON.parse(route.request().postData() || '{}');

        // Verify role is tutor
        expect(requestBody.role).toBe('tutor');

        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            email: 'newtutor@example.com',
            first_name: 'New',
            last_name: 'Tutor',
            role: 'tutor',
          }),
        });
      });

      // Select tutor role
      await page.getByRole('button', { name: /teach/i }).click();

      await page.getByLabel(/first name/i).fill('New');
      await page.getByLabel(/last name/i).fill('Tutor');
      await page.getByLabel(/^email$/i).fill('newtutor@example.com');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('ValidPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Registration Errors', () => {
    test('should show error when email is already registered', async ({ page }) => {
      await page.route('**/api/v1/auth/register', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Email already registered',
          }),
        });
      });

      await page.getByLabel(/first name/i).fill('Existing');
      await page.getByLabel(/last name/i).fill('User');
      await page.getByLabel(/^email$/i).fill('existing@example.com');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('ValidPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      await expect(page.getByText(/already registered|registration failed/i)).toBeVisible({
        timeout: 10000,
      });
    });

    test('should show loading state during registration', async ({ page }) => {
      await page.route('**/api/v1/auth/register', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            role: 'student',
          }),
        });
      });

      await page.getByLabel(/first name/i).fill('Test');
      await page.getByLabel(/last name/i).fill('User');
      await page.getByLabel(/^email$/i).fill('test@example.com');
      await page.getByLabel(/^password$/i).fill('ValidPassword123');
      await page.getByLabel(/confirm password/i).fill('ValidPassword123');

      await page.getByRole('button', { name: /create account/i }).click();

      // Button should be disabled during loading
      const submitButton = page.getByRole('button', { name: /create account/i });
      await expect(submitButton).toBeDisabled();
    });
  });

  test.describe('Navigation', () => {
    test('should navigate to login page via link', async ({ page }) => {
      await page.getByRole('link', { name: /sign in/i }).click();
      await expect(page).toHaveURL('/login');
    });
  });
});
