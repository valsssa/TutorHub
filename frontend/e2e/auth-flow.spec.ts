import { test, expect } from '@playwright/test';

/**
 * Authentication Flow E2E Tests
 * 
 * Tests user registration, login, logout, and protected routes
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear cookies and local storage before each test
    await page.context().clearCookies();
    await page.goto(FRONTEND_URL);
  });

  test('should display login page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // Check page title (flexible - either with or without "Login")
    await expect(page).toHaveTitle(/EduConnect|Login/i);
    
    // Check form elements
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i }).first()).toBeVisible();
    
    // Check link to registration
    await expect(page.getByRole('link', { name: /sign up|register/i }).first()).toBeVisible();
  });

  test('should display registration page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/register`);
    
    // Check page title (flexible)
    await expect(page).toHaveTitle(/EduConnect|Register|Sign Up/i);
    
    // Check form elements
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
    await expect(page.getByLabel(/confirm password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign up|register/i }).first()).toBeVisible();
  });

  test('should register a new user', async ({ page }) => {
    const timestamp = Date.now();
    const testEmail = `test-${timestamp}@example.com`;
    const testPassword = 'Test123!@#';

    await page.goto(`${FRONTEND_URL}/register`);
    
    // Fill registration form
    await page.getByRole('textbox', { name: /email/i }).fill(testEmail);
    await page.getByLabel(/^password$/i).fill(testPassword);
    await page.getByLabel(/confirm password/i).fill(testPassword);
    
    // Submit form
    await page.getByRole('button', { name: /sign up|register/i }).first().click();
    
    // Wait for success message or redirect
    await page.waitForURL(/\/(dashboard|login)/i, { timeout: 10000 });
    
    // Verify we're redirected (either to dashboard or login)
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/(dashboard|login)/i);
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // Use default student credentials
    await page.getByRole('textbox', { name: /email/i }).fill('student@example.com');
    await page.getByLabel(/password/i).fill('student123');
    
    // Submit form (use first button to get main submit, not OAuth buttons)
    await page.getByRole('button', { name: /^sign in$/i }).first().click();
    
    // Wait for redirect to dashboard
    await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/\/dashboard/i);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // Try to login with invalid credentials
    await page.getByRole('textbox', { name: /email/i }).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    
    // Submit form
    await page.getByRole('button', { name: /^sign in$/i }).first().click();
    
    // Wait for error message
    await expect(page.getByText(/invalid.*credentials|incorrect.*email|incorrect.*password/i)).toBeVisible({ timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto(`${FRONTEND_URL}/login`);
    await page.getByRole('textbox', { name: /email/i }).fill('student@example.com');
    await page.getByLabel(/password/i).fill('student123');
    await page.getByRole('button', { name: /^sign in$/i }).first().click();
    
    // Wait for dashboard
    await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
    
    // Find and click logout button
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i }).first();
    await logoutButton.click();
    
    // Wait for redirect to login
    await page.waitForURL(/\/login/i, { timeout: 5000 });
    
    // Verify we're on login page
    await expect(page).toHaveURL(/\/login/i);
  });

  test('should protect dashboard route when not authenticated', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // Should redirect to login
    await page.waitForURL(/\/login/i, { timeout: 5000 });
    
    // Verify redirect
    await expect(page).toHaveURL(/\/login/i);
  });

  test('should validate email format', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/register`);
    
    // Try invalid email
    await page.getByRole('textbox', { name: /email/i }).fill('invalid-email');
    await page.getByLabel(/^password$/i).fill('Test123!@#');
    await page.getByLabel(/confirm password/i).fill('Test123!@#');
    
    // Submit form
    await page.getByRole('button', { name: /sign up|register/i }).first().click();
    
    // Check for validation message
    const emailInput = page.getByRole('textbox', { name: /email/i });
    const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    expect(validationMessage).toBeTruthy();
  });

  test('should validate password match', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/register`);
    
    // Fill form with mismatched passwords
    await page.getByRole('textbox', { name: /email/i }).fill('test@example.com');
    await page.getByLabel(/^password$/i).fill('Test123!@#');
    await page.getByLabel(/confirm password/i).fill('DifferentPassword123');
    
    // Submit form
    await page.getByRole('button', { name: /sign up|register/i }).first().click();
    
    // Check for error message (flexible matching)
    await expect(page.getByText(/password.*match|password.*same|passwords.*not.*match/i)).toBeVisible({ timeout: 3000 });
  });
});
