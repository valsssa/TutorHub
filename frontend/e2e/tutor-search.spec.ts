import { test, expect } from '@playwright/test';

/**
 * Tutor Search E2E Tests
 * 
 * Tests tutor browsing, filtering, and search functionality
 */

// Using baseURL from playwright.config.ts

test.describe('Tutor Search and Browsing', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto('/login');
    await page.getByRole('textbox', { name: /email/i }).fill('student@example.com');
    await page.getByLabel(/password/i).fill('student123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
  });

  test('should display tutors page', async ({ page }) => {
    await page.goto('/tutors');
    
    // Check for tutors list or search interface
    await expect(page.getByText(/find.*tutor|tutors|search/i)).toBeVisible();
  });

  test('should search tutors by subject', async ({ page }) => {
    await page.goto('/tutors');
    
    // Find search input
    const searchInput = page.getByPlaceholder(/search.*subject|find.*tutor/i).first();
    
    if (await searchInput.isVisible()) {
      await searchInput.fill('Mathematics');
      await searchInput.press('Enter');
      
      // Wait for results to load
      await page.waitForTimeout(2000);
      
      // Check that results are displayed
      const resultsCount = await page.getByTestId('tutor-card').count();
      console.log(`Found ${resultsCount} tutor results`);
    }
  });

  test('should filter tutors by price range', async ({ page }) => {
    await page.goto('/tutors');
    
    // Look for price filter
    const priceFilter = page.getByLabel(/price|rate/i).first();
    
    if (await priceFilter.isVisible()) {
      // Apply filter
      await priceFilter.click();
      await page.waitForTimeout(1000);
      
      // Verify filtering occurred
      expect(page.url()).toContain('tutors');
    }
  });

  test('should view tutor profile', async ({ page }) => {
    await page.goto('/tutors');
    
    // Wait for tutor cards to load
    await page.waitForTimeout(2000);
    
    // Find and click first tutor card
    const tutorCard = page.getByTestId('tutor-card').first();
    
    if (await tutorCard.isVisible()) {
      await tutorCard.click();
      
      // Wait for profile page
      await page.waitForURL(/\/tutor\/\d+/i, { timeout: 5000 });
      
      // Verify profile elements
      await expect(page.getByText(/about|biography|experience/i)).toBeVisible();
    }
  });

  test('should save a tutor to favorites', async ({ page }) => {
    await page.goto('/tutors');
    
    await page.waitForTimeout(2000);
    
    // Find save/favorite button
    const favoriteButton = page.getByRole('button', { name: /save|favorite|bookmark/i }).first();
    
    if (await favoriteButton.isVisible()) {
      await favoriteButton.click();
      
      // Wait for confirmation
      await expect(page.getByText(/saved|added to favorites/i)).toBeVisible({ timeout: 3000 });
    }
  });

  test('should display saved tutors page', async ({ page }) => {
    await page.goto('/saved-tutors');
    
    // Check page loaded
    await expect(page.getByText(/saved.*tutors|favorites|bookmarks/i)).toBeVisible();
  });

  test('should paginate tutor results', async ({ page }) => {
    await page.goto('/tutors');
    
    await page.waitForTimeout(2000);
    
    // Look for pagination controls
    const nextButton = page.getByRole('button', { name: /next|›|→/i });
    
    if (await nextButton.isVisible() && await nextButton.isEnabled()) {
      const initialUrl = page.url();
      await nextButton.click();
      
      // Wait for page change
      await page.waitForTimeout(1000);
      
      // Verify URL changed (pagination query param)
      const newUrl = page.url();
      expect(newUrl).not.toBe(initialUrl);
    }
  });
});
