import { test as teardown } from '@playwright/test';

/**
 * Global teardown for E2E tests
 *
 * Runs after all tests to:
 * 1. Clean up any test data (if needed)
 * 2. Generate summary report
 */

teardown('cleanup and summarize', async () => {
  console.log('\n=== E2E Test Suite Complete ===\n');

  console.log('Test artifacts saved to:');
  console.log('  - playwright-report/index.html (HTML report)');
  console.log('  - test-results/ (screenshots, videos, traces)');

  if (process.env.CI) {
    console.log('  - test-results/junit.xml (JUnit report)');
  }

  console.log('\nTo view the report, run: npm run test:e2e:report');
});
