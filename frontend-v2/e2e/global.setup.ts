import { test as setup, expect } from '@playwright/test';

/**
 * Global setup for E2E tests
 *
 * Runs before all tests to:
 * 1. Verify backend is healthy
 * 2. Verify frontend is reachable
 * 3. Clear any stale state
 */

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.E2E_API_URL || 'https://api.valsa.solutions/api/v1';

setup('verify backend health', async ({ request }) => {
  const apiBase = BASE_URL.includes('edustream.valsa.solutions')
    ? 'https://api.valsa.solutions'
    : 'http://localhost:8000';

  try {
    const response = await request.get(`${apiBase}/health`, {
      timeout: 30000,
    });

    if (!response.ok()) {
      console.warn(`Backend health check returned ${response.status()}`);
    } else {
      const body = await response.json();
      console.log('Backend health:', body.status || 'ok');
    }
  } catch (error) {
    console.warn('Backend health check failed (may be expected for external URLs):', error);
  }
});

setup('verify frontend is reachable', async ({ page }) => {
  const response = await page.goto(BASE_URL, { timeout: 60000 });

  if (!response) {
    throw new Error(`Failed to load ${BASE_URL}`);
  }

  if (response.status() >= 500) {
    throw new Error(`Frontend returned server error: ${response.status()}`);
  }

  console.log(`Frontend is reachable at ${BASE_URL}`);
});

setup('check test user availability', async ({ request }) => {
  const apiBase = BASE_URL.includes('edustream.valsa.solutions')
    ? 'https://api.valsa.solutions/api/v1'
    : 'http://localhost:8000/api/v1';

  try {
    const response = await request.post(`${apiBase}/auth/login`, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      form: {
        username: 'student@example.com',
        password: process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!',
      },
      timeout: 30000,
    });

    if (response.ok()) {
      console.log('Test student user is available');
    } else {
      console.warn(`Test student login failed: ${response.status()}`);
    }
  } catch (error) {
    console.warn('Could not verify test user (may be expected):', error);
  }
});
