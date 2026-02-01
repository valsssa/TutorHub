const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

// Integration test configuration - NO MOCKS
const customJestConfig = {
  testEnvironment: 'node', // Use node environment for real HTTP calls
  setupFilesAfterEnv: ['<rootDir>/jest.setup.integration.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: ['**/__tests__/integration/**/*.test.{ts,tsx}'],
  transformIgnorePatterns: [
    'node_modules/(?!(lucide-react|@lucide)/)',
  ],
  // Increase timeout for real API calls
  testTimeout: 30000,
}

module.exports = createJestConfig(customJestConfig)
