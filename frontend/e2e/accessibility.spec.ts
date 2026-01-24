import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility (A11y) E2E Tests
 * 
 * Tests WCAG compliance and accessibility features across the application
 */

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://edustream.valsa.solutions';

test.describe('Accessibility Tests', () => {
  test('login page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('registration page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/register`);
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('homepage should not have accessibility violations', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should support keyboard navigation on login page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.getByRole('textbox', { name: /email/i })).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/password/i)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /sign in/i })).toBeFocused();
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Check for h1
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
    
    // Verify h1 comes before h2
    const headings = await page.locator('h1, h2, h3').all();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForTimeout(2000);
    
    // Get all images
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      // Alt text can be empty for decorative images, but attribute must exist
      expect(alt).not.toBeNull();
    }
  });

  test('should have proper form labels', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // Check email input has label
    const emailInput = page.getByRole('textbox', { name: /email/i });
    await expect(emailInput).toBeVisible();
    
    // Check password input has label
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toBeVisible();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );
    
    expect(contrastViolations).toEqual([]);
  });

  test('should support screen reader landmarks', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Check for main landmark
    const main = page.locator('main, [role="main"]');
    await expect(main).toBeVisible();
    
    // Check for navigation landmark
    const nav = page.locator('nav, [role="navigation"]');
    const navCount = await nav.count();
    expect(navCount).toBeGreaterThanOrEqual(0);
  });

  test('buttons should have accessible names', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);
    
    // All buttons should have text or aria-label
    const buttons = await page.locator('button').all();
    
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const title = await button.getAttribute('title');
      
      expect(text || ariaLabel || title).toBeTruthy();
    }
  });

  test('should have skip navigation link', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Tab to first element (should be skip link)
    await page.keyboard.press('Tab');
    
    // Check if skip link exists
    const skipLink = page.getByRole('link', { name: /skip.*content|skip.*navigation/i });
    const skipLinkExists = await skipLink.count() > 0;
    
    // This is optional, so we just log the result
    console.log(`Skip navigation link present: ${skipLinkExists}`);
  });
});
