# 🎭 Playwright E2E Tests

## Quick Start

```bash
cd frontend
npm run test:e2e:ui
```

## Test Statistics

- **Total Tests**: 42
- **Test Files**: 5
- **Categories**: Authentication, Tutor Search, Booking, Messaging, Accessibility

## Test Coverage

| Category | Tests | Files |
|----------|-------|-------|
| Authentication | 9 tests | `e2e/auth-flow.spec.ts` |
| Tutor Search | 7 tests | `e2e/tutor-search.spec.ts` |
| Booking Flow | 7 tests | `e2e/booking-flow.spec.ts` |
| Messaging | 8 tests | `e2e/messaging.spec.ts` |
| Accessibility | 11 tests | `e2e/accessibility.spec.ts` |

## Running Tests

### Interactive Mode (Recommended)
```bash
npm run test:e2e:ui
```

### Headless Mode
```bash
npm run test:e2e
```

### Show Browser
```bash
npm run test:e2e:headed
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### View Report
```bash
npm run test:e2e:report
```

## Docker

```bash
# Run Playwright tests in Docker
docker compose -f docker-compose.test.yml up --build playwright-tests

# With cleanup
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit playwright-tests
docker compose -f docker-compose.test.yml down -v
```

## Documentation

- **Quick Start**: `PLAYWRIGHT_QUICK_START.md`
- **Complete Guide**: `frontend/PLAYWRIGHT_COMPLETE.md`
- **Comprehensive Guide**: `docs/PLAYWRIGHT_GUIDE.md`
- **Implementation Summary**: `docs/PLAYWRIGHT_IMPLEMENTATION_SUMMARY.md`
- **E2E README**: `frontend/e2e/README.md`

## Test Examples

### Run specific tests
```bash
# Run authentication tests
npx playwright test e2e/auth-flow.spec.ts

# Run tests matching pattern
npx playwright test --grep "login"

# List all tests
npx playwright test --list
```

## Features

✅ Comprehensive E2E coverage  
✅ Accessibility testing (WCAG 2.1 AA)  
✅ Test utilities and helpers  
✅ Docker integration  
✅ CI/CD ready  
✅ Screenshot/video on failure  
✅ HTML reports  
✅ Interactive UI mode  

## Prerequisites

### For local testing:
```bash
# Start backend
docker compose up backend db -d

# Start frontend
cd frontend && npm run dev
```

### For full integration:
```bash
# Start everything
docker compose up --build -d
```

## Verification

```bash
# Should show: "Total: 42 tests in 5 files"
npx playwright test --list
```

## Support

For issues or questions, see documentation:
- `PLAYWRIGHT_QUICK_START.md` - Quick reference
- `frontend/PLAYWRIGHT_COMPLETE.md` - Complete guide
- `docs/PLAYWRIGHT_GUIDE.md` - Detailed documentation

---

**Status**: ✅ Ready to use  
**Version**: 1.0.0  
**Created**: January 24, 2026
