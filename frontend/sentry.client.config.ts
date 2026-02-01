// This file configures the initialization of Sentry on the client.
// The config you add here will be used whenever a user loads a page in their browser.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;

// Validate DSN format - must be https://<key>@<host>/<project_id>
const isValidDsn = (dsn: string | undefined): boolean => {
  if (!dsn) return false;
  const trimmed = dsn.trim().toLowerCase();
  // Check for placeholder values
  if (["your_sentry_dsn", "your-sentry-dsn", "placeholder", "none", "null", ""].includes(trimmed)) {
    return false;
  }
  // Must start with https:// and contain @
  return dsn.startsWith("https://") && dsn.includes("@");
};

if (isValidDsn(SENTRY_DSN)) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Environment
    environment: process.env.NODE_ENV,

    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions

    // Session Replay (optional - can be expensive)
    replaysSessionSampleRate: 0, // Disabled by default
    replaysOnErrorSampleRate: 0.1, // 10% on errors

    // Debug mode (only in development)
    debug: process.env.NODE_ENV === "development",

    // Filter out common expected errors
    beforeSend(event, hint) {
      const error = hint.originalException;

      // Ignore network errors (user offline, etc.)
      if (error instanceof TypeError && error.message === "Failed to fetch") {
        return null;
      }

      // Ignore canceled requests
      if (error instanceof Error && error.name === "AbortError") {
        return null;
      }

      // Ignore 401/403 errors (expected auth failures)
      const exceptionValue = event.exception?.values?.[0]?.value;
      if (typeof exceptionValue === "string") {
        if (exceptionValue.includes("401") || exceptionValue.includes("403")) {
          return null;
        }
      }

      return event;
    },

    // Filter out noisy transactions
    beforeSendTransaction(event) {
      // Skip health check endpoints
      if (event.transaction === "/health") {
        return null;
      }

      return event;
    },

    // Integrations
    integrations: [
      Sentry.browserTracingIntegration(),
      // Replay integration is optional and can be enabled later
      // Sentry.replayIntegration(),
    ],
  });
}
