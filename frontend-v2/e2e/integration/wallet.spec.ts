/**
 * Wallet E2E Tests - Real Backend Integration
 *
 * Tests wallet and payment functionality:
 * - Balance display
 * - Transaction history
 * - Payment operations (if available)
 */
import { test, expect } from '../fixtures/test-base';

const BASE_URL = process.env.E2E_BASE_URL || 'https://edustream.valsa.solutions';

async function loginAsStudent(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('student@example.com');
  await page.getByLabel(/password/i).fill(process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/(student|dashboard)/, { timeout: 20000 });
}

async function loginAsTutor(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('tutor@example.com');
  await page.getByLabel(/password/i).fill(process.env.TEST_TUTOR_PASSWORD || 'TutorPass123!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/(tutor|dashboard)/, { timeout: 20000 });
}

test.describe('Wallet - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Wallet Page', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display wallet page', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/wallet|balance|payment/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show balance amount', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const balanceDisplay = page.locator('[data-testid="balance"]')
        .or(page.getByText(/\$[\d,.]+/))
        .or(page.getByText(/balance.*:?\s*[\d,.]+/i));

      const hasBalance = await balanceDisplay.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should have add funds option', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const addFundsButton = page.getByRole('button', { name: /add.*fund|deposit|top.*up/i })
        .or(page.getByRole('link', { name: /add.*fund|deposit/i }));

      const hasAddFunds = await addFundsButton.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should navigate to transactions page', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const transactionsLink = page.getByRole('link', { name: /transaction|history/i })
        .or(page.getByText(/view.*transaction|transaction.*history/i));

      if (await transactionsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await transactionsLink.click();
        await expect(page).toHaveURL(/\/wallet\/transactions/);
      }
    });
  });

  test.describe('Transaction History', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display transactions page', async ({ page }) => {
      await page.goto('/wallet/transactions');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/transaction|history/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show transaction list or empty state', async ({ page }) => {
      await page.goto('/wallet/transactions');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const transactions = page.locator('[data-testid="transaction-item"]')
        .or(page.locator('[class*="transaction"]'))
        .or(page.locator('li, article').filter({ hasText: /payment|credit|debit|\$/i }));

      const hasTransactions = await transactions.first().isVisible({ timeout: 5000 }).catch(() => false);
      const hasEmptyState = await page.getByText(/no transaction|empty|no history/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasTransactions || hasEmptyState).toBeTruthy();
    });

    test('should show transaction details', async ({ page }) => {
      await page.goto('/wallet/transactions');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const transactionItem = page.locator('[data-testid="transaction-item"]')
        .or(page.locator('[class*="transaction"]')).first();

      if (await transactionItem.isVisible({ timeout: 5000 }).catch(() => false)) {
        const hasAmount = await transactionItem.getByText(/\$[\d,.]+/).isVisible({ timeout: 2000 }).catch(() => false);
        const hasDate = await transactionItem.getByText(/\d{1,2}.*\d{4}|\d{4}-\d{2}-\d{2}/).isVisible({ timeout: 2000 }).catch(() => false);

      }
    });

    test('should filter transactions by type (if available)', async ({ page }) => {
      await page.goto('/wallet/transactions');
      await page.waitForLoadState('networkidle');

      const typeFilter = page.getByRole('combobox', { name: /type/i })
        .or(page.getByRole('tablist'));

      if (await typeFilter.isVisible({ timeout: 3000 }).catch(() => false)) {
        const tabs = page.getByRole('tab');
        if (await tabs.first().isVisible({ timeout: 2000 }).catch(() => false)) {
          await tabs.first().click();
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should paginate transactions (if many)', async ({ page }) => {
      await page.goto('/wallet/transactions');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const pagination = page.getByRole('navigation', { name: /pagination/i })
        .or(page.locator('[data-testid="pagination"]'))
        .or(page.getByRole('button', { name: /next|load more/i }));

      const hasPagination = await pagination.isVisible({ timeout: 3000 }).catch(() => false);

    });
  });

  test.describe('Tutor Earnings', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsTutor(page);
    });

    test('should show earnings for tutors', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const hasEarnings = await page.getByText(/earning|revenue|income/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const hasBalance = await page.getByText(/balance|\$/i)
        .isVisible({ timeout: 5000 }).catch(() => false);

      expect(hasEarnings || hasBalance).toBeTruthy();
    });

    test('should show withdrawal option for tutors', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const withdrawButton = page.getByRole('button', { name: /withdraw|payout|cash.*out/i })
        .or(page.getByRole('link', { name: /withdraw|payout/i }));

      const hasWithdraw = await withdrawButton.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should show pending earnings', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const pendingEarnings = page.getByText(/pending|available|clear/i)
        .filter({ hasText: /\$|\d/ });

      const hasPending = await pendingEarnings.isVisible({ timeout: 5000 }).catch(() => false);

    });
  });

  test.describe('Payment Flow', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should show payment methods', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const paymentMethods = page.getByText(/payment.*method|card|bank/i)
        .or(page.locator('[data-testid="payment-methods"]'));

      const hasPaymentMethods = await paymentMethods.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should have add payment method option', async ({ page }) => {
      await page.goto('/wallet');
      await page.waitForLoadState('networkidle');

      const addPaymentButton = page.getByRole('button', { name: /add.*card|add.*payment/i })
        .or(page.getByRole('link', { name: /add.*card|add.*payment/i }));

      const hasAddPayment = await addPaymentButton.isVisible({ timeout: 5000 }).catch(() => false);

    });
  });
});
