// Integration test setup - NO MOCKS, uses real API

// Set required environment variables for tests (only if not already set)
if (!process.env.NEXT_PUBLIC_API_URL) {
  process.env.NEXT_PUBLIC_API_URL = 'http://test-backend:8000'
}

// Set longer timeout for integration tests (they make real API calls)
jest.setTimeout(30000)

// Global test utilities
globalThis.sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
