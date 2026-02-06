/* eslint-disable react-hooks/rules-of-hooks */
import { test as base, expect, APIRequestContext } from '@playwright/test';

interface ApiFixtures {
  apiContext: APIRequestContext;
  getAuthToken: (email: string, password: string) => Promise<string>;
  apiRequest: <T>(method: string, endpoint: string, options?: {
    token?: string;
    data?: unknown;
  }) => Promise<{ status: number; data: T }>;
}

const API_BASE_URL = process.env.E2E_API_URL || 'https://api.valsa.solutions/api/v1';

export const test = base.extend<ApiFixtures>({
  apiContext: async ({ playwright }, use) => {
    const context = await playwright.request.newContext({
      baseURL: API_BASE_URL,
      extraHTTPHeaders: {
        'Content-Type': 'application/json',
      },
    });
    await use(context);
    await context.dispose();
  },

  getAuthToken: async ({ apiContext }, use) => {
    await use(async (email: string, password: string) => {
      const response = await apiContext.post('/auth/login', {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        form: {
          username: email,
          password: password,
        },
      });

      if (!response.ok()) {
        throw new Error(`Login failed: ${response.status()} - ${await response.text()}`);
      }

      const data = await response.json();
      return data.access_token;
    });
  },

  apiRequest: async ({ apiContext }, use) => {
    await use(async <T>(method: string, endpoint: string, options?: {
      token?: string;
      data?: unknown;
    }) => {
      const headers: Record<string, string> = {};
      if (options?.token) {
        headers['Authorization'] = `Bearer ${options.token}`;
      }

      const requestOptions: {
        headers: Record<string, string>;
        data?: unknown;
      } = { headers };

      if (options?.data) {
        requestOptions.data = options.data;
      }

      let response;
      switch (method.toUpperCase()) {
        case 'GET':
          response = await apiContext.get(endpoint, requestOptions);
          break;
        case 'POST':
          response = await apiContext.post(endpoint, requestOptions);
          break;
        case 'PUT':
          response = await apiContext.put(endpoint, requestOptions);
          break;
        case 'PATCH':
          response = await apiContext.patch(endpoint, requestOptions);
          break;
        case 'DELETE':
          response = await apiContext.delete(endpoint, requestOptions);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }

      let data: T;
      try {
        data = await response.json();
      } catch {
        data = undefined as T;
      }

      return { status: response.status(), data };
    });
  },
});

export { expect, API_BASE_URL };
