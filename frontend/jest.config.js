const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testPathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/node_modules/',
    '<rootDir>/__tests__/test-utils.tsx',
    '<rootDir>/__tests__/utils/',
    '<rootDir>/__tests__/integration/', // Exclude integration tests from default run
    '<rootDir>/__tests__/e2e/.*\\.spec\\.ts$', // Playwright tests run separately
  ],
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
  ],
  // Fix Next.js 14.2.33 SWC compatibility issue
  transformIgnorePatterns: [
    'node_modules/(?!(lucide-react|@lucide)/)',
  ],
  // Unit tests use jest.setup.js with mocks
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
