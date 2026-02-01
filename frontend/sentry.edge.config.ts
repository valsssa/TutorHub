// This file configures the initialization of Sentry for edge features (middleware, edge routes, etc.)
// The config you add here will be used whenever an edge function is executed.
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
    tracesSampleRate: 0.1,

    // Debug mode
    debug: false,
  });
}
