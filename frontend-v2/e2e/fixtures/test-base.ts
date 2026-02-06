/* eslint-disable react-hooks/rules-of-hooks */
import { test as base, expect, Page, ConsoleMessage } from '@playwright/test';

interface ConsoleError {
  message: string;
  type: string;
  location: string;
}

interface TestFixtures {
  consoleErrors: ConsoleError[];
  pageErrors: Error[];
  unhandledRejections: Error[];
  failOnConsoleError: boolean;
  allowedConsolePatterns: RegExp[];
}

const DEFAULT_ALLOWED_PATTERNS = [
  /Download the React DevTools/,
  /You are running a development build/,
  /hydration/i,
  /\[MSW\]/,
  /favicon\.ico.*404/i,
  /Failed to load resource.*404/i,
  /Failed to load resource.*401/i,
  /Failed to load resource.*403/i,
  /net::ERR_/i,
  /CORS/i,
  /Access-Control-Allow-Origin/i,
  /Warning.*ReactDOM\.render/i,
  /Warning.*componentWill/i,
  /Warning.*findDOMNode/i,
  /ResizeObserver loop/i,
  /Non-Error promise rejection/i,
  /chunk.*failed to load/i,
  /Refused to connect/i,
  /Network request failed/i,
  /AbortError/i,
  /%s %o/,
];

export const test = base.extend<TestFixtures>({
  consoleErrors: [[], { option: true }],
  pageErrors: [[], { option: true }],
  unhandledRejections: [[], { option: true }],
  failOnConsoleError: [true, { option: true }],
  allowedConsolePatterns: [DEFAULT_ALLOWED_PATTERNS, { option: true }],

  page: async ({ page, consoleErrors, pageErrors, unhandledRejections, failOnConsoleError, allowedConsolePatterns }, use) => {
    const errors: ConsoleError[] = [];
    const pageErrs: Error[] = [];
    const rejections: Error[] = [];

    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        const isAllowed = allowedConsolePatterns.some((pattern) => pattern.test(text));
        if (!isAllowed) {
          errors.push({
            message: text,
            type: msg.type(),
            location: msg.location()?.url || 'unknown',
          });
        }
      }
    });

    page.on('pageerror', (error: Error) => {
      pageErrs.push(error);
    });

    page.on('requestfailed', (request) => {
      const failure = request.failure();
      if (failure && !failure.errorText.includes('net::ERR_ABORTED')) {
        console.warn(`Request failed: ${request.url()} - ${failure.errorText}`);
      }
    });

    await page.addInitScript(() => {
      window.addEventListener('unhandledrejection', (event) => {
        (window as unknown as { __unhandledRejections: PromiseRejectionEvent[] }).__unhandledRejections =
          (window as unknown as { __unhandledRejections: PromiseRejectionEvent[] }).__unhandledRejections || [];
        (window as unknown as { __unhandledRejections: PromiseRejectionEvent[] }).__unhandledRejections.push(event);
      });
    });

    await use(page);

    const unhandled = await page.evaluate(() => {
      const w = window as unknown as { __unhandledRejections?: PromiseRejectionEvent[] };
      return (w.__unhandledRejections || []).map((e) => ({
        reason: String(e.reason),
      }));
    });

    unhandled.forEach((u) => {
      rejections.push(new Error(u.reason));
    });

    consoleErrors.push(...errors);
    pageErrors.push(...pageErrs);
    unhandledRejections.push(...rejections);

    if (failOnConsoleError) {
      if (errors.length > 0) {
        const errorMessages = errors.map((e) => `[${e.type}] ${e.message} (at ${e.location})`).join('\n');
        throw new Error(`Console errors detected:\n${errorMessages}`);
      }
      if (pageErrs.length > 0) {
        const errorMessages = pageErrs.map((e) => e.message).join('\n');
        throw new Error(`Page errors detected:\n${errorMessages}`);
      }
      if (rejections.length > 0) {
        const errorMessages = rejections.map((e) => e.message).join('\n');
        throw new Error(`Unhandled promise rejections detected:\n${errorMessages}`);
      }
    }
  },
});

export { expect };

export async function waitForNetworkIdle(page: Page, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}

export async function expectNoServerErrors(page: Page) {
  const responses: Array<{ url: string; status: number }> = [];

  page.on('response', (response) => {
    if (response.status() >= 500) {
      responses.push({ url: response.url(), status: response.status() });
    }
  });

  return {
    check: () => {
      if (responses.length > 0) {
        const errorList = responses.map((r) => `${r.status}: ${r.url}`).join('\n');
        throw new Error(`Server errors detected:\n${errorList}`);
      }
    },
  };
}

export async function takeScreenshotOnFailure(page: Page, testInfo: { title: string; outputPath: (name: string) => string }) {
  const screenshotPath = testInfo.outputPath(`failure-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
}
