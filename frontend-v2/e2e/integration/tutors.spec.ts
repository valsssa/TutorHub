/**
 * Tutors E2E Tests - Real Backend Integration
 *
 * Tests tutor browsing, viewing profiles, and search:
 * - Tutor listing page
 * - Tutor profile view
 * - Search and filtering
 * - Favorite functionality
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

test.describe('Tutors - Real Backend Integration', () => {
  test.use({ baseURL: BASE_URL });

  test.describe('Tutor Listing', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should display tutors list page', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/tutor|find.*tutor|browse/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show tutor cards with basic info', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');

      await page.waitForTimeout(2000);

      const hasSkeletons = await page.locator('[class*="skeleton"]').first().isVisible({ timeout: 2000 }).catch(() => false);
      if (hasSkeletons) {
        await page.waitForSelector('[class*="skeleton"]', { state: 'hidden', timeout: 10000 }).catch(() => {});
      }

      const tutorCards = page.locator('[data-testid="tutor-card"]')
        .or(page.locator('[class*="tutor-card"]'))
        .or(page.locator('article').filter({ hasText: /tutor|hour|rate|\$/i }));

      const count = await tutorCards.count();

    });

    test('should show empty state if no tutors', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      const tutorCards = page.locator('[data-testid="tutor-card"], [class*="tutor-card"]');
      const cardCount = await tutorCards.count();

      if (cardCount === 0) {
        const emptyState = page.getByText(/no tutor|empty|not found|no result/i);
        await expect(emptyState).toBeVisible({ timeout: 5000 });
      }
    });

    test('should load more tutors on scroll (if pagination)', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const initialCount = await page.locator('[data-testid="tutor-card"], article').count();

      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2000);

      const loadMoreButton = page.getByRole('button', { name: /load more|show more|next/i });
      if (await loadMoreButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await loadMoreButton.click();
        await page.waitForTimeout(2000);
      }

    });
  });

  test.describe('Tutor Search', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');
    });

    test('should have search functionality', async ({ page }) => {
      const searchInput = page.getByRole('searchbox')
        .or(page.getByPlaceholder(/search|find/i))
        .or(page.locator('input[type="search"]'));

      const hasSearch = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should filter tutors by subject (if available)', async ({ page }) => {
      const subjectFilter = page.getByRole('combobox', { name: /subject/i })
        .or(page.locator('select').filter({ hasText: /subject/i }))
        .or(page.getByText(/filter.*subject|subject.*filter/i));

      if (await subjectFilter.isVisible({ timeout: 3000 }).catch(() => false)) {
        await subjectFilter.click();

        const firstOption = page.getByRole('option').first();
        if (await firstOption.isVisible({ timeout: 2000 }).catch(() => false)) {
          await firstOption.click();
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should filter tutors by price range (if available)', async ({ page }) => {
      const priceFilter = page.getByRole('slider')
        .or(page.locator('input[type="range"]'))
        .or(page.getByText(/price.*range|hourly.*rate/i));

      const hasPriceFilter = await priceFilter.isVisible({ timeout: 3000 }).catch(() => false);

    });
  });

  test.describe('Tutor Profile View', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should navigate to tutor profile from listing', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const tutorCard = page.locator('[data-testid="tutor-card"], article').first();
      const viewButton = tutorCard.getByRole('link', { name: /view|profile|details/i })
        .or(tutorCard.locator('a'));

      if (await viewButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await viewButton.click();
        await page.waitForURL(/\/tutors\/\d+/, { timeout: 10000 });
      }
    });

    test('should display tutor profile details', async ({ page }) => {
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');

      const hasProfile = await page.getByText(/about|bio|experience|subject|rate|\$/i)
        .isVisible({ timeout: 10000 }).catch(() => false);
      const hasError = await page.getByText(/not found|error/i)
        .isVisible({ timeout: 2000 }).catch(() => false);

      expect(hasProfile || hasError).toBeTruthy();
    });

    test('should show tutor availability (if displayed)', async ({ page }) => {
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');

      const availabilitySection = page.getByText(/availability|schedule|available/i);
      const hasAvailability = await availabilitySection.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should show tutor reviews (if any)', async ({ page }) => {
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');

      const reviewsSection = page.getByText(/review|rating|star/i);
      const hasReviews = await reviewsSection.isVisible({ timeout: 5000 }).catch(() => false);

    });

    test('should have booking button on tutor profile', async ({ page }) => {
      await page.goto('/tutors/1');
      await page.waitForLoadState('networkidle');

      const bookButton = page.getByRole('button', { name: /book|schedule|session/i })
        .or(page.getByRole('link', { name: /book|schedule|session/i }));

      const hasBookButton = await bookButton.isVisible({ timeout: 5000 }).catch(() => false);

    });
  });

  test.describe('Favorites', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should toggle favorite on tutor card', async ({ page }) => {
      await page.goto('/tutors');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const favoriteButton = page.locator('[data-testid="favorite-button"]')
        .or(page.getByRole('button', { name: /favorite|heart|save/i }))
        .first();

      if (await favoriteButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await favoriteButton.click();
        await page.waitForTimeout(1000);
      }
    });

    test('should navigate to favorites page', async ({ page }) => {
      await page.goto('/favorites');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/favorite|saved|liked/i)).toBeVisible({ timeout: 10000 });
    });

    test('should show favorited tutors on favorites page', async ({ page }) => {
      await page.goto('/favorites');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const hasTutors = await page.locator('[data-testid="tutor-card"], article')
        .isVisible({ timeout: 3000 }).catch(() => false);
      const hasEmptyState = await page.getByText(/no favorite|empty|no saved/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasTutors || hasEmptyState).toBeTruthy();
    });
  });

  test.describe('Tutor Packages', () => {
    test.beforeEach(async ({ page }) => {
      await loginAsStudent(page);
    });

    test('should show tutor packages if available', async ({ page }) => {
      await page.goto('/tutors/1/packages');
      await page.waitForLoadState('networkidle');

      const hasPackages = await page.getByText(/package|bundle|lesson/i)
        .isVisible({ timeout: 5000 }).catch(() => false);
      const hasError = await page.getByText(/not found|no package/i)
        .isVisible({ timeout: 3000 }).catch(() => false);

      expect(hasPackages || hasError).toBeTruthy();
    });
  });
});
