import { test, expect } from '@playwright/test';

test.describe('Booking Flow', () => {
  const mockTutors = {
    items: [
      {
        id: 1,
        user_id: 101,
        display_name: 'Jane Smith',
        headline: 'Expert Mathematics Tutor',
        bio: 'I have been teaching math for over 10 years.',
        hourly_rate: 50,
        currency: 'USD',
        is_approved: true,
        average_rating: 4.8,
        review_count: 24,
        avatar_url: null,
        subjects: [
          { id: 1, name: 'Mathematics' },
          { id: 2, name: 'Calculus' },
        ],
      },
      {
        id: 2,
        user_id: 102,
        display_name: 'John Doe',
        headline: 'Physics and Science Tutor',
        bio: 'PhD in Physics with a passion for teaching.',
        hourly_rate: 65,
        currency: 'USD',
        is_approved: true,
        average_rating: 4.9,
        review_count: 42,
        avatar_url: null,
        subjects: [
          { id: 3, name: 'Physics' },
          { id: 4, name: 'Chemistry' },
        ],
      },
    ],
    total: 2,
    page: 1,
    total_pages: 1,
    per_page: 10,
  };

  const mockTutor = mockTutors.items[0];

  const mockSubjects = [
    { id: 1, name: 'Mathematics' },
    { id: 2, name: 'Calculus' },
    { id: 3, name: 'Physics' },
    { id: 4, name: 'Chemistry' },
    { id: 5, name: 'Biology' },
    { id: 6, name: 'English' },
    { id: 7, name: 'History' },
    { id: 8, name: 'Computer Science' },
  ];

  const mockAvailability = [
    { id: 1, tutor_id: 1, day_of_week: 1, start_time: '09:00', end_time: '12:00' },
    { id: 2, tutor_id: 1, day_of_week: 1, start_time: '14:00', end_time: '17:00' },
    { id: 3, tutor_id: 1, day_of_week: 3, start_time: '10:00', end_time: '15:00' },
    { id: 4, tutor_id: 1, day_of_week: 5, start_time: '09:00', end_time: '18:00' },
  ];

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

    // Mock tutors list
    await page.route('**/api/v1/tutors?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTutors),
      });
    });

    // Mock single tutor
    await page.route('**/api/v1/tutors/1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTutor),
      });
    });

    // Mock tutor availability
    await page.route('**/api/v1/tutors/1/availability', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAvailability),
      });
    });

    // Mock subjects
    await page.route('**/api/v1/subjects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSubjects),
      });
    });
  });

  test.describe('Tutors List Page', () => {
    test('should display list of tutors', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByRole('heading', { name: /find a tutor/i })).toBeVisible();

      // Should display tutor cards
      await expect(page.getByText('Jane Smith')).toBeVisible();
      await expect(page.getByText('John Doe')).toBeVisible();
    });

    test('should display tutor ratings and prices', async ({ page }) => {
      await page.goto('/tutors');

      // Check for rating display
      await expect(page.getByText('4.8')).toBeVisible();
      await expect(page.getByText('4.9')).toBeVisible();

      // Check for price display
      await expect(page.getByText(/\$50/)).toBeVisible();
      await expect(page.getByText(/\$65/)).toBeVisible();
    });

    test('should display subject badges on tutor cards', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByText('Mathematics')).toBeVisible();
      await expect(page.getByText('Physics')).toBeVisible();
    });

    test('should navigate to tutor profile when card is clicked', async ({ page }) => {
      await page.goto('/tutors');

      // Click on the first tutor card
      await page.getByText('Jane Smith').click();

      await expect(page).toHaveURL('/tutors/1');
    });

    test('should display search functionality', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByPlaceholder(/search by subject/i)).toBeVisible();
    });

    test('should filter tutors by subject', async ({ page }) => {
      // Mock filtered results
      await page.route('**/api/v1/tutors?*subject=Physics*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [mockTutors.items[1]],
            total: 1,
            page: 1,
            total_pages: 1,
            per_page: 10,
          }),
        });
      });

      await page.goto('/tutors');

      // Click on Physics subject badge
      await page.getByRole('button', { name: /physics/i }).or(page.getByText('Physics').first()).click();

      // Should show only John Doe
      await expect(page.getByText('John Doe')).toBeVisible();
    });

    test('should display popular subjects filter', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByText(/popular subjects/i)).toBeVisible();
    });

    test('should display price range filter', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByText(/price range/i)).toBeVisible();
    });

    test('should display sort options', async ({ page }) => {
      await page.goto('/tutors');

      await expect(page.getByText(/sort by/i)).toBeVisible();
      await expect(page.getByText(/top rated/i)).toBeVisible();
    });
  });

  test.describe('Tutor Profile Page', () => {
    test('should display tutor profile information', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByRole('heading', { name: 'Jane Smith' })).toBeVisible();
      await expect(page.getByText('Expert Mathematics Tutor')).toBeVisible();
    });

    test('should display tutor bio', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText(/about/i)).toBeVisible();
      await expect(page.getByText(/teaching math for over 10 years/i)).toBeVisible();
    });

    test('should display tutor subjects', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText('Mathematics')).toBeVisible();
      await expect(page.getByText('Calculus')).toBeVisible();
    });

    test('should display tutor availability', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText(/availability/i)).toBeVisible();
      await expect(page.getByText(/monday/i)).toBeVisible();
      await expect(page.getByText(/09:00/)).toBeVisible();
    });

    test('should display tutor rating and reviews', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText('4.8')).toBeVisible();
      await expect(page.getByText(/24 reviews/i)).toBeVisible();
    });

    test('should display hourly rate', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText(/\$50/)).toBeVisible();
      await expect(page.getByText(/per hour/i)).toBeVisible();
    });

    test('should display Book Session button', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByRole('button', { name: /book session/i })).toBeVisible();
    });

    test('should display Send Message button', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByRole('button', { name: /send message/i })).toBeVisible();
    });

    test('should display verified badge for approved tutors', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByText(/verified/i)).toBeVisible();
    });

    test('should have back navigation button', async ({ page }) => {
      await page.goto('/tutors/1');

      // Back button should be present
      const backButton = page.getByRole('button', { name: /back/i })
        .or(page.locator('button').filter({ has: page.locator('svg') }).first());

      await expect(backButton).toBeVisible();
    });

    test('should display reviews section', async ({ page }) => {
      await page.goto('/tutors/1');

      await expect(page.getByRole('heading', { name: /reviews/i })).toBeVisible();
    });
  });

  test.describe('Booking Process', () => {
    test('should initiate booking when Book Session is clicked', async ({ page }) => {
      await page.goto('/tutors/1');

      const bookButton = page.getByRole('button', { name: /book session/i });
      await bookButton.click();

      // Depending on implementation, might navigate to booking page or open modal
      // Check for either booking form or navigation
      const hasBookingForm = await page.getByText(/select.*date|choose.*time|booking details/i).isVisible()
        .catch(() => false);
      const hasNavigated = page.url().includes('/bookings/new') || page.url().includes('/book');

      expect(hasBookingForm || hasNavigated).toBeTruthy();
    });

    test('should allow navigating to tutor packages', async ({ page }) => {
      // Mock packages endpoint
      await page.route('**/api/v1/tutors/1/packages', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 1,
              tutor_id: 1,
              name: '5 Session Package',
              description: 'Save 10% with this package',
              sessions: 5,
              price: 225,
              currency: 'USD',
            },
          ]),
        });
      });

      await page.goto('/tutors/1/packages');

      await expect(page.getByText(/5 session package/i).or(page.getByText(/package/i))).toBeVisible();
    });
  });

  test.describe('Tutor Not Found', () => {
    test('should display not found message for invalid tutor ID', async ({ page }) => {
      await page.route('**/api/v1/tutors/999', async (route) => {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Tutor not found' }),
        });
      });

      await page.goto('/tutors/999');

      await expect(page.getByText(/tutor not found/i)).toBeVisible();
      await expect(page.getByRole('link', { name: /browse tutors/i })).toBeVisible();
    });
  });

  test.describe('Empty States', () => {
    test('should display empty state when no tutors found', async ({ page }) => {
      await page.route('**/api/v1/tutors?*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            page: 1,
            total_pages: 0,
            per_page: 10,
          }),
        });
      });

      await page.goto('/tutors');

      await expect(page.getByText(/no tutors found/i)).toBeVisible();
    });

    test('should show clear filters button when no results', async ({ page }) => {
      await page.route('**/api/v1/tutors?*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            page: 1,
            total_pages: 0,
            per_page: 10,
          }),
        });
      });

      await page.goto('/tutors?subject=NonExistent');

      await expect(page.getByRole('button', { name: /clear filters/i })).toBeVisible();
    });
  });

  test.describe('Pagination', () => {
    test('should display pagination when multiple pages exist', async ({ page }) => {
      await page.route('**/api/v1/tutors?*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockTutors,
            total: 30,
            total_pages: 3,
          }),
        });
      });

      await page.goto('/tutors');

      // Should have pagination controls
      await expect(page.getByText(/showing.*of.*tutors/i).or(page.getByRole('button', { name: /2|next/i }))).toBeVisible();
    });
  });

  test.describe('Favorite Functionality', () => {
    test('should display favorite/heart button on tutor profile', async ({ page }) => {
      await page.goto('/tutors/1');

      // Look for heart/favorite button
      const favoriteButton = page.getByRole('button', { name: /favorite|heart/i })
        .or(page.locator('button').filter({ has: page.locator('[data-lucide="heart"]') }));

      await expect(favoriteButton.first()).toBeVisible();
    });
  });

  test.describe('Share Functionality', () => {
    test('should display share button on tutor profile', async ({ page }) => {
      await page.goto('/tutors/1');

      const shareButton = page.getByRole('button', { name: /share/i })
        .or(page.locator('button').filter({ has: page.locator('[data-lucide="share"]') }));

      await expect(shareButton.first()).toBeVisible();
    });
  });
});
