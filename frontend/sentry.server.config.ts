// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
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

    // Debug mode (only in development)
    debug: false,

    // Filter out common expected errors
    beforeSend(event, hint) {
      const error = hint.originalException;

      // Ignore network errors
      if (error instanceof Error && error.message.includes("ECONNREFUSED")) {
        return null;
      }

      return event;
    },
  });
}
