import { Page, expect } from '@playwright/test';

/**
 * Helper utilities for Playwright E2E tests
 */

export class TestHelpers {
  /**
   * Login helper - logs in a user with the given credentials
   */
  static async login(page: Page, email: string, password: string) {
    const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://edustream.valsa.solutions';
    
    await page.goto(`${FRONTEND_URL}/login`);
    await page.getByRole('textbox', { name: /email/i }).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/dashboard/i, { timeout: 10000 });
  }

  /**
   * Login as student
   */
  static async loginAsStudent(page: Page) {
    await this.login(page, 'student@example.com', 'student123');
  }

  /**
   * Login as tutor
   */
  static async loginAsTutor(page: Page) {
    await this.login(page, 'tutor@example.com', 'tutor123');
  }

  /**
   * Login as admin
   */
  static async loginAsAdmin(page: Page) {
    await this.login(page, 'admin@example.com', 'admin123');
  }

  /**
   * Logout helper
   */
  static async logout(page: Page) {
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    await logoutButton.click();
    await page.waitForURL(/\/login/i, { timeout: 5000 });
  }

  /**
   * Wait for API response
   */
  static async waitForApiResponse(page: Page, urlPattern: string | RegExp, timeout = 10000) {
    return page.waitForResponse(
      response => {
        const url = response.url();
        const matches = typeof urlPattern === 'string' 
          ? url.includes(urlPattern)
          : urlPattern.test(url);
        return matches && response.status() === 200;
      },
      { timeout }
    );
  }

  /**
   * Take a screenshot with a descriptive name
   */
  static async takeScreenshot(page: Page, name: string) {
    await page.screenshot({ 
      path: `screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * Wait for element to be visible
   */
  static async waitForElement(page: Page, selector: string, timeout = 5000) {
    await page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * Check if element exists without throwing error
   */
  static async elementExists(page: Page, selector: string): Promise<boolean> {
    return await page.locator(selector).count() > 0;
  }

  /**
   * Fill form field by label
   */
  static async fillFormField(page: Page, label: string | RegExp, value: string) {
    const field = page.getByLabel(label);
    await field.fill(value);
  }

  /**
   * Click button by text
   */
  static async clickButton(page: Page, text: string | RegExp) {
    const button = page.getByRole('button', { name: text });
    await button.click();
  }

  /**
   * Generate unique email for testing
   */
  static generateTestEmail(prefix = 'test'): string {
    return `${prefix}-${Date.now()}@example.com`;
  }

  /**
   * Generate random password
   */
  static generatePassword(length = 12): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < length; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
  }

  /**
   * Clear all cookies and storage
   */
  static async clearSession(page: Page) {
    await page.context().clearCookies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  }

  /**
   * Check if user is authenticated
   */
  static async isAuthenticated(page: Page): Promise<boolean> {
    try {
      const cookies = await page.context().cookies();
      return cookies.some(cookie => cookie.name === 'token');
    } catch {
      return false;
    }
  }

  /**
   * Wait for toast notification
   */
  static async waitForToast(page: Page, message?: string | RegExp, timeout = 5000) {
    const toastSelector = '[role="alert"], .toast, .notification';
    await page.waitForSelector(toastSelector, { state: 'visible', timeout });
    
    if (message) {
      await expect(page.locator(toastSelector)).toContainText(message);
    }
  }

  /**
   * Scroll to element
   */
  static async scrollToElement(page: Page, selector: string) {
    await page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * Get text content of element
   */
  static async getTextContent(page: Page, selector: string): Promise<string> {
    return await page.locator(selector).textContent() || '';
  }

  /**
   * Check if page has error
   */
  static async hasPageError(page: Page): Promise<boolean> {
    return await this.elementExists(page, '.error, [role="alert"]');
  }

  /**
   * Wait for loading to complete
   */
  static async waitForLoadingComplete(page: Page, timeout = 10000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Mock API response
   */
  static async mockApiResponse(page: Page, url: string | RegExp, response: any) {
    await page.route(url, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * Intercept API call
   */
  static async interceptApiCall(page: Page, url: string | RegExp) {
    return new Promise((resolve) => {
      page.on('response', response => {
        const matches = typeof url === 'string' 
          ? response.url().includes(url)
          : url.test(response.url());
        
        if (matches) {
          resolve(response);
        }
      });
    });
  }
}

/**
 * Test data generators
 */
export class TestData {
  static student = {
    email: 'student@example.com',
    password: 'student123'
  };

  static tutor = {
    email: 'tutor@example.com',
    password: 'tutor123'
  };

  static admin = {
    email: 'admin@example.com',
    password: 'admin123'
  };

  static generateUser() {
    return {
      email: TestHelpers.generateTestEmail(),
      password: TestHelpers.generatePassword()
    };
  }

  static generateBooking() {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    
    return {
      date: futureDate.toISOString().split('T')[0],
      time: '10:00',
      duration: 60,
      subject: 'Mathematics'
    };
  }

  static generateMessage() {
    return {
      text: `Test message ${Date.now()}`,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Custom assertions
 */
export class CustomAssertions {
  static async assertPageTitle(page: Page, expectedTitle: string | RegExp) {
    await expect(page).toHaveTitle(expectedTitle);
  }

  static async assertUrl(page: Page, expectedUrl: string | RegExp) {
    await expect(page).toHaveURL(expectedUrl);
  }

  static async assertElementVisible(page: Page, selector: string) {
    await expect(page.locator(selector)).toBeVisible();
  }

  static async assertElementHidden(page: Page, selector: string) {
    await expect(page.locator(selector)).toBeHidden();
  }

  static async assertTextContent(page: Page, selector: string, expectedText: string | RegExp) {
    await expect(page.locator(selector)).toContainText(expectedText);
  }

  static async assertElementCount(page: Page, selector: string, expectedCount: number) {
    await expect(page.locator(selector)).toHaveCount(expectedCount);
  }
}
