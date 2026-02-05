import { test as base, expect, Page, BrowserContext } from '@playwright/test';

interface TestUser {
  email: string;
  password: string;
  role: 'student' | 'tutor' | 'admin' | 'owner';
  firstName?: string;
  lastName?: string;
}

const TEST_USERS: Record<string, TestUser> = {
  student: {
    email: 'student@example.com',
    password: process.env.TEST_STUDENT_PASSWORD || 'StudentPass123!',
    role: 'student',
    firstName: 'Test',
    lastName: 'Student',
  },
  tutor: {
    email: 'tutor@example.com',
    password: process.env.TEST_TUTOR_PASSWORD || 'TutorPass123!',
    role: 'tutor',
    firstName: 'Test',
    lastName: 'Tutor',
  },
  admin: {
    email: 'admin@example.com',
    password: process.env.TEST_ADMIN_PASSWORD || 'AdminPass123!',
    role: 'admin',
    firstName: 'Admin',
    lastName: 'User',
  },
  owner: {
    email: 'owner@example.com',
    password: process.env.TEST_OWNER_PASSWORD || 'OwnerPass123!',
    role: 'owner',
    firstName: 'Owner',
    lastName: 'User',
  },
};

interface AuthFixtures {
  testUsers: typeof TEST_USERS;
  login: (page: Page, role: keyof typeof TEST_USERS) => Promise<void>;
  loginAs: (page: Page, email: string, password: string) => Promise<void>;
  logout: (page: Page) => Promise<void>;
  authenticatedPage: (role: keyof typeof TEST_USERS) => Promise<Page>;
  studentPage: Page;
  tutorPage: Page;
  adminPage: Page;
}

async function performLogin(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in/i }).click();

  await page.waitForURL(/\/(student|tutor|admin|owner|dashboard)/, { timeout: 15000 });
}

async function performLogout(page: Page): Promise<void> {
  const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
  if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutButton.click();
  } else {
    const userMenu = page.locator('[data-testid="user-menu"]').or(page.getByRole('button', { name: /menu|profile/i }));
    if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
      await userMenu.click();
      const logoutOption = page.getByRole('menuitem', { name: /logout|sign out/i });
      await logoutOption.click();
    }
  }
  await page.waitForURL('/login', { timeout: 10000 });
}

export const test = base.extend<AuthFixtures>({
  testUsers: TEST_USERS,

  login: async ({}, use) => {
    await use(async (page: Page, role: keyof typeof TEST_USERS) => {
      const user = TEST_USERS[role];
      await performLogin(page, user.email, user.password);
    });
  },

  loginAs: async ({}, use) => {
    await use(async (page: Page, email: string, password: string) => {
      await performLogin(page, email, password);
    });
  },

  logout: async ({}, use) => {
    await use(async (page: Page) => {
      await performLogout(page);
    });
  },

  authenticatedPage: async ({ browser }, use) => {
    await use(async (role: keyof typeof TEST_USERS) => {
      const context = await browser.newContext();
      const page = await context.newPage();
      await performLogin(page, TEST_USERS[role].email, TEST_USERS[role].password);
      return page;
    });
  },

  studentPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await performLogin(page, TEST_USERS.student.email, TEST_USERS.student.password);
    await use(page);
    await context.close();
  },

  tutorPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await performLogin(page, TEST_USERS.tutor.email, TEST_USERS.tutor.password);
    await use(page);
    await context.close();
  },

  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await performLogin(page, TEST_USERS.admin.email, TEST_USERS.admin.password);
    await use(page);
    await context.close();
  },
});

export { expect, TEST_USERS };
export type { TestUser };
