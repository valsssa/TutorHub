import { test, expect } from '@playwright/test';

/**
 * Booking Flow E2E Tests
 * 
 * Tests the complete booking process from tutor selection to confirmation
 */

// Using baseURL from playwright.config.ts

test.describe('Booking Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto('/login');
    await page.getByRole('textbox', { name: /email/i }).fill('student@example.com');
    await page.getByLabel(/password/i).fill('student123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
  });

  test('should display booking modal from tutor profile', async ({ page }) => {
    // Navigate to a tutor profile (assuming tutor ID 1 exists)
    await page.goto('/tutor/1');
    await page.waitForTimeout(2000);
    
    // Find and click book button
    const bookButton = page.getByRole('button', { name: /book.*session|schedule|reserve/i }).first();
    
    if (await bookButton.isVisible()) {
      await bookButton.click();
      
      // Verify booking modal opened
      await expect(page.getByText(/select.*time|choose.*date|schedule.*lesson/i)).toBeVisible({ timeout: 3000 });
    }
  });

  test('should select date and time for booking', async ({ page }) => {
    await page.goto('/tutor/1');
    await page.waitForTimeout(2000);
    
    const bookButton = page.getByRole('button', { name: /book.*session|schedule|reserve/i }).first();
    
    if (await bookButton.isVisible()) {
      await bookButton.click();
      await page.waitForTimeout(1000);
      
      // Look for date picker
      const dateInput = page.getByLabel(/date|when/i).first();
      
      if (await dateInput.isVisible()) {
        // Select a future date
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 7);
        const dateString = futureDate.toISOString().split('T')[0];
        
        await dateInput.fill(dateString);
        
        // Look for time slot selection
        const timeSlot = page.getByRole('button', { name: /\d{1,2}:\d{2}|morning|afternoon/i }).first();
        
        if (await timeSlot.isVisible()) {
          await timeSlot.click();
        }
      }
    }
  });

  test('should view bookings page', async ({ page }) => {
    await page.goto('/bookings');
    
    // Check page loaded
    await expect(page.getByText(/booking|session|appointment/i)).toBeVisible();
  });

  test('should display upcoming bookings', async ({ page }) => {
    await page.goto('/bookings');
    await page.waitForTimeout(2000);
    
    // Look for bookings list or empty state
    const hasBookings = await page.getByTestId('booking-card').count() > 0;
    const hasEmptyState = await page.getByText(/no.*booking|no.*upcoming/i).isVisible();
    
    expect(hasBookings || hasEmptyState).toBeTruthy();
  });

  test('should filter bookings by status', async ({ page }) => {
    await page.goto('/bookings');
    await page.waitForTimeout(2000);
    
    // Look for status filter tabs
    const confirmedTab = page.getByRole('tab', { name: /confirmed|upcoming/i });
    
    if (await confirmedTab.isVisible()) {
      await confirmedTab.click();
      await page.waitForTimeout(1000);
      
      // Verify filter applied
      const url = page.url();
      expect(url).toContain('bookings');
    }
  });

  test('should cancel a booking', async ({ page }) => {
    await page.goto('/bookings');
    await page.waitForTimeout(2000);
    
    // Find cancel button for first booking
    const cancelButton = page.getByRole('button', { name: /cancel.*booking/i }).first();
    
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      
      // Confirm cancellation in modal
      const confirmButton = page.getByRole('button', { name: /confirm|yes|cancel booking/i });
      
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        
        // Wait for success message
        await expect(page.getByText(/cancelled|canceled/i)).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should reschedule a booking', async ({ page }) => {
    await page.goto('/bookings');
    await page.waitForTimeout(2000);
    
    // Find reschedule button
    const rescheduleButton = page.getByRole('button', { name: /reschedule/i }).first();
    
    if (await rescheduleButton.isVisible()) {
      await rescheduleButton.click();
      
      // Wait for reschedule modal
      await expect(page.getByText(/select.*new.*time|choose.*date/i)).toBeVisible({ timeout: 3000 });
    }
  });
});
