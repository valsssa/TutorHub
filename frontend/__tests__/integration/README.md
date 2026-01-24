# Integration Tests - Using Real API

This directory contains integration tests that make real HTTP requests to the backend API instead of using mocks.

## Overview

Unlike unit tests (which use mocked data), these integration tests:
- ✅ Connect to a real backend API running in Docker
- ✅ Use real database with test data
- ✅ Test actual HTTP requests/responses
- ✅ Verify end-to-end functionality
- ✅ Ensure API contracts are working

## Running Integration Tests

### Using Docker Compose (Recommended)

This is the easiest way as it handles all service dependencies:

```bash
# Start test infrastructure and run integration tests
docker compose -f docker-compose.test.yml up frontend-integration-tests --build --abort-on-container-exit

# Clean up after tests
docker compose -f docker-compose.test.yml down -v
```

### Running Locally

If you want to run tests locally (requires backend to be running):

```bash
# 1. Start the backend test services
docker compose -f docker-compose.test.yml up test-backend test-db test-minio -d

# 2. Wait for services to be healthy
docker compose -f docker-compose.test.yml ps

# 3. Run integration tests from your machine
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8001 npm run test:integration

# 4. Clean up
docker compose -f docker-compose.test.yml down -v
```

### Running Specific Tests

```bash
# Run only favorites integration tests
docker compose -f docker-compose.test.yml run --rm frontend-integration-tests \
  sh -c "npm test -- --testPathPattern=favorites-integration --watchAll=false"

# Run with verbose output
docker compose -f docker-compose.test.yml run --rm frontend-integration-tests \
  sh -c "npm test -- --testPathPattern=integration --watchAll=false --verbose"
```

## Test Structure

### favorites-integration.test.ts

Tests the complete favorites API workflow:

**Setup (beforeAll):**
- Logs in as a student user
- Gets authentication token
- Retrieves a tutor profile ID for testing

**Test Suites:**

1. **GET /api/favorites**
   - Returns empty array when no favorites
   - Returns list of saved tutors
   - Requires authentication

2. **POST /api/favorites**
   - Successfully adds tutor to favorites
   - Validates required fields
   - Handles non-existent tutors
   - Prevents duplicate favorites

3. **DELETE /api/favorites/:id**
   - Removes tutor from favorites
   - Returns 404 for non-existent favorites

4. **GET /api/favorites/:id**
   - Checks if tutor is saved
   - Returns 404 when not favorited

5. **Authorization and Permissions**
   - Only students can access favorites
   - Users can't access other users' favorites

6. **Data Integrity**
   - Maintains referential integrity
   - Includes proper timestamps

**Cleanup (afterEach):**
- Removes all test favorites to ensure clean state

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://test-backend:8000` | Backend API URL |
| `NODE_ENV` | `test` | Node environment |

## Test Users

Integration tests use default test users created by the backend:

| Role | Email | Password |
|------|-------|----------|
| Student | student@example.com | student123 |
| Tutor | tutor@example.com | tutor123 |
| Admin | admin@example.com | admin123 |

## Debugging Failed Tests

### Check Backend Logs

```bash
docker compose -f docker-compose.test.yml logs test-backend
```

### Check Database State

```bash
# Connect to test database
docker compose -f docker-compose.test.yml exec test-db psql -U postgres -d authapp_test

# Check favorites table
SELECT * FROM favorite_tutors;

# Check tutor profiles
SELECT id, user_id, title FROM tutor_profiles;
```

### Verify Backend Health

```bash
curl http://localhost:8001/health
```

### Run Tests with Debug Output

```bash
docker compose -f docker-compose.test.yml run --rm frontend-integration-tests \
  sh -c "npm test -- --testPathPattern=integration --watchAll=false --verbose --detectOpenHandles"
```

## Common Issues

### "Cannot connect to backend"

**Solution:** Ensure the backend is running and healthy:
```bash
docker compose -f docker-compose.test.yml up test-backend -d
docker compose -f docker-compose.test.yml ps
```

### "401 Unauthorized"

**Cause:** Token authentication failed

**Solution:** Check that default users exist in the database:
```bash
docker compose -f docker-compose.test.yml exec test-db \
  psql -U postgres -d authapp_test -c "SELECT id, email, role FROM users;"
```

### "404 Tutor not found"

**Cause:** No tutor profile exists for testing

**Solution:** Ensure the tutor user has a profile:
```bash
docker compose -f docker-compose.test.yml exec test-db \
  psql -U postgres -d authapp_test -c "SELECT * FROM tutor_profiles;"
```

If no profiles exist, log in as tutor and create one via the API.

### Tests timeout

**Solution:** Increase the timeout in jest.setup.integration.js:
```javascript
jest.setTimeout(60000) // 60 seconds
```

## Best Practices

1. **Test Isolation**: Each test cleans up after itself
2. **Use Real Data**: Don't mock API responses
3. **Test Happy and Sad Paths**: Include error scenarios
4. **Check Status Codes**: Verify HTTP responses
5. **Verify Data Integrity**: Check database state when needed

## Adding New Integration Tests

1. Create test file in `__tests__/integration/`
2. Use `axios` to make real HTTP requests
3. Include `beforeAll` for authentication
4. Include `afterEach` for cleanup
5. Test both success and error cases

Example:

```typescript
import axios, { AxiosInstance } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://test-backend:8000'

describe('My Feature Integration Tests', () => {
  let api: AxiosInstance
  let authToken: string

  beforeAll(async () => {
    api = axios.create({ baseURL: API_URL })
    
    const loginResponse = await api.post('/login', {
      username: 'student@example.com',
      password: 'student123',
    })
    
    authToken = loginResponse.data.access_token
  })

  it('should do something', async () => {
    const response = await api.get('/api/my-endpoint', {
      headers: { Authorization: `Bearer ${authToken}` },
    })

    expect(response.status).toBe(200)
    expect(response.data).toHaveProperty('expected_field')
  })
})
```

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run Integration Tests
  run: |
    docker compose -f docker-compose.test.yml up frontend-integration-tests --abort-on-container-exit
    docker compose -f docker-compose.test.yml down -v
```

## Performance

Integration tests are slower than unit tests because they:
- Make real HTTP requests
- Wait for database operations
- Authenticate users
- Clean up data

**Typical test times:**
- Unit tests: 2-5 seconds
- Integration tests: 15-30 seconds

Run them separately:
```bash
npm run test:unit           # Fast
npm run test:integration    # Slower but thorough
```
