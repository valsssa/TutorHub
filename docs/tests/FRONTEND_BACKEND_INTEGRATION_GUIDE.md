# Frontend-Backend Integration Testing Guide

**Version:** 1.0
**Date:** 2026-01-21
**Purpose:** Comprehensive guide for testing full-stack integration between frontend and backend

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Basic Connectivity Testing](#basic-connectivity-testing)
5. [API Integration Verification](#api-integration-verification)
6. [Authentication Flow Testing](#authentication-flow-testing)
7. [Data Flow Testing](#data-flow-testing)
8. [End-to-End User Journeys](#end-to-end-user-journeys)
9. [Database State Verification](#database-state-verification)
10. [Error Handling Testing](#error-handling-testing)
11. [Performance Integration Testing](#performance-integration-testing)
12. [Monitoring and Debugging](#monitoring-and-debugging)
13. [CI/CD Integration Testing](#cicd-integration-testing)

---

## Overview

This guide provides comprehensive testing procedures to verify that frontend and backend components work together seamlessly. Integration testing ensures:

- ✅ API communication works correctly
- ✅ Data flows properly between components
- ✅ Authentication and authorization are synchronized
- ✅ Business logic is consistent across layers
- ✅ Error handling is unified
- ✅ Performance meets requirements

### Test Categories

| Test Type | Scope | Tools |
|-----------|--------|--------|
| **Connectivity Tests** | Network communication | curl, Postman, browser dev tools |
| **API Integration Tests** | Endpoint functionality | Jest + MSW, Cypress API testing |
| **Authentication Flow Tests** | Login/session management | Playwright, Cypress |
| **Data Flow Tests** | CRUD operations | Database queries, API assertions |
| **E2E Journey Tests** | Complete user workflows | Playwright, Cypress |
| **Performance Tests** | Response times, load | Lighthouse, k6 |

---

## Prerequisites

### Required Tools

```bash
# Core testing tools
npm install -g @playwright/test cypress lighthouse
pip install requests pytest-playwright

# API testing tools
npm install -g newman # Postman collection runner
go install github.com/rakyll/hey@latest # Load testing

# Database tools
pip install pgcli mycli # Database clients
```

### Environment Requirements

- ✅ Docker and Docker Compose installed
- ✅ Node.js 18+ and Python 3.12+
- ✅ PostgreSQL client tools
- ✅ Network access to all services
- ✅ Test data seeded in database

---

## Environment Setup

### 1. Start Full Stack Environment

```bash
# Clone and setup project
git clone <repository-url>
cd project-directory

# Start all services with test configuration
docker compose -f docker-compose.test.yml up -d

# Wait for services to be ready
./scripts/wait-for-services.sh

# Verify services are running
docker compose -f docker-compose.test.yml ps
```

Expected output:
```
NAME                          STATUS              PORTS
project1-splitversion-backend-tests   Up      0.0.0.0:8000->8000/tcp
project1-splitversion-frontend-tests  Up      0.0.0.0:3000->3000/tcp
project1-splitversion-db-tests        Up      0.0.0.0:5432->5432/tcp
```

### 2. Seed Test Data

```bash
# Seed database with test fixtures
docker compose -f docker-compose.test.yml exec backend python -m pytest --fixtures-only

# Or run seed script directly
docker compose -f docker-compose.test.yml exec backend python backend/seed_data.py

# Verify test users exist
docker compose -f docker-compose.test.yml exec db psql -U postgres -d authapp -c "
SELECT email, role FROM users WHERE email LIKE '%test%';
"
```

### 3. Verify Service Health

```bash
# Backend health check
curl -f http://localhost:8000/health

# Frontend availability
curl -f http://localhost:3000

# Database connectivity
docker compose -f docker-compose.test.yml exec db pg_isready -U postgres -d authapp
```

---

## Basic Connectivity Testing

### 1. Network Connectivity Tests

```bash
# Test all service ports
#!/bin/bash
services=("backend:8000" "frontend:3000" "db:5432")

for service in "${services[@]}"; do
  name=$(echo $service | cut -d: -f1)
  port=$(echo $service | cut -d: -f2)

  if nc -z localhost $port 2>/dev/null; then
    echo "✅ $name is accessible on port $port"
  else
    echo "❌ $name is NOT accessible on port $port"
    exit 1
  fi
done
```

### 2. CORS Configuration Test

```bash
# Test CORS headers from frontend to backend
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     -v http://localhost:8000/api/users/me 2>&1 | grep -E "(Access-Control|allow-origin)"
```

Expected headers:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
access-control-allow-headers: content-type, authorization
```

### 3. SSL/TLS Verification (Production)

```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null

# Verify certificate chain
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## API Integration Verification

### 1. API Endpoint Mapping Verification

Create a test script to verify all endpoints are accessible:

```python
#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_endpoint(endpoint, method='GET', data=None, headers=None, expected_status=200):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)

        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - {response.status_code}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

# Test critical endpoints
endpoints = [
    ("/health", "GET", None, None, 200),
    ("/api/auth/login", "POST", {"email": "invalid", "password": "invalid"}, None, 401),
    ("/api/subjects", "GET", None, None, 200),
    ("/api/tutors", "GET", None, None, 200),
]

print("Testing API Endpoints...")
all_passed = True
for endpoint, method, data, headers, expected in endpoints:
    if not test_endpoint(endpoint, method, data, headers, expected):
        all_passed = False

if all_passed:
    print("\n✅ All API endpoints are accessible!")
else:
    print("\n❌ Some API endpoints failed!")
    exit(1)
```

### 2. Request/Response Schema Validation

```python
import jsonschema
import requests

# Define expected schemas
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "role": {"type": "string", "enum": ["student", "tutor", "admin"]},
        "is_active": {"type": "boolean"}
    },
    "required": ["id", "email", "role"]
}

def validate_response_schema(url, expected_schema):
    """Validate API response against JSON schema"""
    response = requests.get(url)
    response.raise_for_status()

    try:
        data = response.json()
        jsonschema.validate(instance=data, schema=expected_schema)
        print(f"✅ {url} response matches schema")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ {url} schema validation failed: {e}")
        return False

# Test schema compliance
validate_response_schema("http://localhost:8000/api/users/me", USER_SCHEMA)
```

### 3. API Rate Limiting Verification

```bash
# Test rate limiting on authentication endpoints
echo "Testing rate limiting..."

# Make multiple rapid requests
for i in {1..15}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}')

  if [ "$status" = "429" ]; then
    echo "✅ Rate limiting working (attempt $i)"
    break
  fi

  if [ $i -eq 15 ]; then
    echo "❌ Rate limiting not triggered after 15 attempts"
    exit 1
  fi

  sleep 0.1
done
```

---

## Authentication Flow Testing

### 1. Complete Login Flow Test

```python
#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_complete_auth_flow():
    """Test complete authentication flow between frontend and backend"""

    print("Testing Complete Authentication Flow...")

    # Step 1: Login via API
    login_data = {
        "email": "student@example.com",
        "password": "student123"
    }

    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=login_data
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    login_data = login_response.json()
    token = login_data.get("access_token")

    if not token:
        print("❌ No access token received")
        return False

    print("✅ Login successful, received token")

    # Step 2: Test token with protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers=headers
    )

    if user_response.status_code != 200:
        print(f"❌ Protected endpoint failed: {user_response.status_code}")
        return False

    user_data = user_response.json()
    if user_data.get("email") != "student@example.com":
        print("❌ Wrong user data returned")
        return False

    print("✅ Protected endpoint accessible with token")

    # Step 3: Test token expiration (if applicable)
    # This would require waiting or using an expired token

    # Step 4: Test logout (if implemented)
    # logout_response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)

    print("✅ Authentication flow test completed successfully")
    return True

if __name__ == "__main__":
    test_complete_auth_flow()
```

### 2. Token Synchronization Test

```javascript
// frontend_token_test.js - Run in browser console or with Puppeteer
async function testTokenSync() {
  // Simulate login
  const loginResponse = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'student@example.com',
      password: 'student123'
    })
  });

  const loginData = await loginResponse.json();
  const token = loginData.access_token;

  // Store token (simulate frontend behavior)
  localStorage.setItem('token', token);

  // Test API call with token
  const userResponse = await fetch('/api/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (userResponse.ok) {
    const userData = await userResponse.json();
    console.log('✅ Token works for API calls');
    console.log('User data:', userData);
  } else {
    console.error('❌ Token authentication failed');
  }
}

testTokenSync();
```

### 3. Session Management Test

```python
def test_session_persistence():
    """Test that sessions persist across requests"""

    # Login once
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "student@example.com",
        "password": "student123"
    })
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Make multiple requests with same token
    for i in range(5):
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "student@example.com"

    print("✅ Session persistence verified across multiple requests")
```

---

## Data Flow Testing

### 1. CRUD Operations Integration Test

```python
def test_crud_operations_flow():
    """Test complete CRUD flow between frontend and backend"""

    print("Testing CRUD Operations Flow...")

    # Step 1: Create (POST)
    booking_data = {
        "tutor_profile_id": 1,
        "subject_id": 1,
        "start_time": "2025-02-01T10:00:00Z",
        "duration_minutes": 60,
        "notes_student": "Test booking"
    }

    create_response = requests.post(
        f"{BASE_URL}/api/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    if create_response.status_code != 201:
        print(f"❌ Create failed: {create_response.status_code}")
        return False

    booking = create_response.json()
    booking_id = booking["id"]
    print(f"✅ Booking created with ID: {booking_id}")

    # Step 2: Read (GET)
    read_response = requests.get(
        f"{BASE_URL}/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if read_response.status_code != 200:
        print(f"❌ Read failed: {read_response.status_code}")
        return False

    retrieved_booking = read_response.json()
    assert retrieved_booking["id"] == booking_id
    assert retrieved_booking["notes_student"] == "Test booking"
    print("✅ Booking read successfully")

    # Step 3: Update (PUT)
    update_data = {"notes_student": "Updated test booking"}
    update_response = requests.put(
        f"{BASE_URL}/api/bookings/{booking_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    if update_response.status_code != 200:
        print(f"❌ Update failed: {update_response.status_code}")
        return False

    print("✅ Booking updated successfully")

    # Step 4: Delete (DELETE)
    delete_response = requests.delete(
        f"{BASE_URL}/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if delete_response.status_code not in [200, 204]:
        print(f"❌ Delete failed: {delete_response.status_code}")
        return False

    print("✅ Booking deleted successfully")

    # Step 5: Verify deletion (GET should fail)
    verify_response = requests.get(
        f"{BASE_URL}/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if verify_response.status_code != 404:
        print(f"❌ Booking still exists after deletion: {verify_response.status_code}")
        return False

    print("✅ CRUD operations flow completed successfully")
    return True
```

### 2. Database State Verification

```sql
-- Run these queries to verify data consistency

-- Check user creation
SELECT id, email, role, created_at FROM users WHERE email LIKE '%test%' ORDER BY created_at DESC;

-- Verify booking creation and relationships
SELECT
    b.id,
    b.status,
    b.total_amount,
    u.email as student_email,
    tp.title as tutor_title
FROM bookings b
JOIN users u ON b.student_id = u.id
JOIN tutor_profiles tp ON b.tutor_profile_id = tp.id
ORDER BY b.created_at DESC
LIMIT 5;

-- Check payment records
SELECT
    p.id,
    p.amount,
    p.status,
    b.id as booking_id
FROM payments p
LEFT JOIN bookings b ON p.booking_id = b.id
ORDER BY p.created_at DESC
LIMIT 5;

-- Verify review relationships
SELECT
    r.id,
    r.rating,
    r.comment,
    u.email as reviewer_email,
    tp.title as tutor_title
FROM reviews r
JOIN users u ON r.student_id = u.id
JOIN tutor_profiles tp ON r.tutor_profile_id = tp.id
ORDER BY r.created_at DESC
LIMIT 5;
```

### 3. Data Synchronization Test

```python
def test_data_synchronization():
    """Test that data changes are synchronized across components"""

    # Create a booking
    booking_response = requests.post(f"{BASE_URL}/api/bookings", json={
        "tutor_profile_id": 1,
        "subject_id": 1,
        "start_time": "2025-02-01T10:00:00Z",
        "duration_minutes": 60
    }, headers={"Authorization": f"Bearer {token}"})

    booking_id = booking_response.json()["id"]

    # Check database directly
    db_check = run_query(f"SELECT status FROM bookings WHERE id = {booking_id}")
    assert db_check[0]["status"] == "pending"

    # Update via API
    requests.put(f"{BASE_URL}/api/bookings/{booking_id}", json={
        "status": "confirmed"
    }, headers={"Authorization": f"Bearer {token}"})

    # Verify database was updated
    db_check = run_query(f"SELECT status FROM bookings WHERE id = {booking_id}")
    assert db_check[0]["status"] == "confirmed"

    # Verify API returns updated data
    api_check = requests.get(f"{BASE_URL}/api/bookings/{booking_id}",
                           headers={"Authorization": f"Bearer {token}"})
    assert api_check.json()["status"] == "confirmed"

    print("✅ Data synchronization verified")
```

---

## End-to-End User Journeys

### 1. Student Booking Journey E2E Test

```python
# tests/e2e/test_complete_student_journey.py
import pytest
from playwright.sync_api import Page, expect

class TestCompleteStudentJourney:
    """Complete E2E test for student booking journey"""

    def test_student_complete_workflow(self, page: Page):
        """Test complete student workflow from registration to review"""

        # Step 1: Registration
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'e2e-student@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Student')
        page.click('button:has-text("Sign Up")')

        expect(page).to_have_url('http://localhost:3000/login')

        # Step 2: Login
        page.fill('input[name="email"]', 'e2e-student@test.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button:has-text("Sign In")')

        expect(page).to_have_url('http://localhost:3000/dashboard')

        # Step 3: Search and book tutor
        page.click('a:has-text("Find Tutors")')
        expect(page).to_have_url('http://localhost:3000/tutors')

        # Click on first tutor
        page.click('.tutor-card:first-child button:has-text("Book")')

        # Fill booking modal
        modal = page.locator('[role="dialog"]')
        expect(modal).to_be_visible()

        modal.select_option('select[name="subject"]', '1')
        modal.fill('input[name="date"]', '2025-02-15')
        modal.select_option('select[name="time"]', '10:00')
        modal.select_option('select[name="duration"]', '60')
        modal.click('button:has-text("Book Session")')

        # Verify booking created
        expect(page.locator('.toast-success')).to_contain_text('Booking created')
        expect(page).to_have_url('http://localhost:3000/bookings')

        # Step 4: Verify backend data
        # This would require API calls to verify database state
        booking_card = page.locator('.booking-card').first
        expect(booking_card).to_contain_text('Pending')

        print("✅ Complete student journey test passed")
```

### 2. Tutor Onboarding Journey Test

```python
class TestTutorOnboardingJourney:
    """Complete E2E test for tutor onboarding"""

    def test_tutor_onboarding_workflow(self, page: Page):
        """Test complete tutor onboarding workflow"""

        # Registration
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'e2e-tutor@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Tutor')
        page.click('button:has-text("Sign Up")')

        expect(page).to_have_url('http://localhost:3000/tutor/onboarding')

        # Complete onboarding wizard (8 steps)
        # ... implementation of all onboarding steps ...

        # Submit for approval
        page.click('button:has-text("Submit for Approval")')
        expect(page).to_have_url('http://localhost:3000/tutor/profile/submitted')

        # Admin approval (switch to admin context)
        admin_page = page.context.new_page()
        admin_page.goto('http://localhost:3000/login')
        admin_page.fill('input[name="email"]', 'admin@example.com')
        admin_page.fill('input[name="password"]', 'admin123')
        admin_page.click('button:has-text("Sign In")')

        # Approve tutor
        admin_page.click('button:has-text("Tutor Approvals"]')
        admin_page.click('.pending-tutor-card:first-child')
        admin_page.click('button:has-text("Approve")')

        # Verify tutor can now accept bookings
        # ... continue with booking acceptance flow ...

        admin_page.close()
        print("✅ Tutor onboarding journey test passed")
```

### 3. Real-Time Features Test

```python
class TestRealtimeFeatures:
    """Test real-time features integration"""

    def test_websocket_messaging(self, context):
        """Test WebSocket messaging between users"""

        # Open two browser pages
        student_page = context.new_page()
        tutor_page = context.new_page()

        # Login both users
        # ... login code ...

        # Navigate to messages
        student_page.goto('http://localhost:3000/messages')
        tutor_page.goto('http://localhost:3000/messages')

        # Verify WebSocket connection
        expect(student_page.locator('.connection-status')).to_contain_text('Connected')
        expect(tutor_page.locator('.connection-status')).to_contain_text('Connected')

        # Send message from student
        student_page.fill('textarea[placeholder="Type a message"]', 'Hello!')
        student_page.click('button[aria-label="Send message"]')

        # Verify real-time delivery to tutor
        expect(tutor_page.locator('.message-bubble.received').last).to_contain_text('Hello!')

        # Test typing indicators
        tutor_page.fill('textarea', 'Typing a response...')
        expect(student_page.locator('.typing-indicator')).to_contain_text('is typing')

        print("✅ Real-time messaging test passed")
```

---

## Database State Verification

### 1. Database Consistency Checks

```sql
-- Comprehensive database integrity check

-- Check foreign key relationships
SELECT 'bookings_students' as check_name,
       COUNT(*) as invalid_count
FROM bookings b
LEFT JOIN users u ON b.student_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'bookings_tutors',
       COUNT(*)
FROM bookings b
LEFT JOIN tutor_profiles tp ON b.tutor_profile_id = tp.id
WHERE tp.id IS NULL

UNION ALL

SELECT 'reviews_students',
       COUNT(*)
FROM reviews r
LEFT JOIN users u ON r.student_id = u.id
WHERE u.id IS NULL;

-- Check data type consistency
SELECT 'invalid_emails' as check_name,
       COUNT(*) as count
FROM users
WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- Check business rule compliance
SELECT 'negative_amounts' as check_name,
       COUNT(*) as count
FROM bookings
WHERE total_amount < 0;

-- Check temporal consistency
SELECT 'future_created_dates' as check_name,
       COUNT(*) as count
FROM users
WHERE created_at > NOW();
```

### 2. Data Migration Verification

```python
def test_data_migration_integrity():
    """Verify data integrity after migrations"""

    # Check that all required fields are populated
    required_fields_checks = [
        ("users", "email", "Users without email"),
        ("users", "role", "Users without role"),
        ("tutor_profiles", "title", "Tutor profiles without title"),
        ("bookings", "status", "Bookings without status"),
    ]

    for table, field, description in required_fields_checks:
        count = run_query(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL")[0]["count"]
        if count > 0:
            print(f"❌ {description}: {count} records")
            return False

    # Check enum value validity
    valid_roles = run_query("SELECT DISTINCT role FROM users")
    invalid_roles = [r for r in valid_roles if r["role"] not in ["student", "tutor", "admin"]]

    if invalid_roles:
        print(f"❌ Invalid user roles found: {invalid_roles}")
        return False

    print("✅ Data migration integrity verified")
    return True
```

---

## Error Handling Testing

### 1. Network Error Simulation

```bash
# Test frontend error handling with network failures

# Simulate backend down
docker compose -f docker-compose.test.yml stop backend

# Test frontend behavior
curl -s http://localhost:3000 > /dev/null
echo "Frontend should show error page when backend is down"

# Restart backend
docker compose -f docker-compose.test.yml start backend
```

### 2. API Error Response Testing

```python
def test_api_error_handling():
    """Test how frontend handles various API errors"""

    error_scenarios = [
        ("/api/bookings/99999", "GET", 404, "Not Found"),
        ("/api/bookings", "POST", 400, "Bad Request"),
        ("/api/users/me", "GET", 401, "Unauthorized"),
        ("/api/admin/users", "GET", 403, "Forbidden"),
        ("/api/bookings", "POST", 422, "Validation Error"),
        ("/health", "GET", 500, "Internal Server Error"),
    ]

    for endpoint, method, expected_status, description in error_scenarios:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={})

            if response.status_code == expected_status:
                print(f"✅ {description} ({expected_status}) handled correctly")

                # Check error response format
                error_data = response.json()
                if "detail" in error_data or "message" in error_data:
                    print("✅ Error response has proper format"                else:
                    print("⚠️ Error response missing detail/message field"
            else:
                print(f"❌ Expected {expected_status} for {description}, got {response.status_code}")

        except Exception as e:
            print(f"❌ Error testing {description}: {e}")

    print("✅ API error handling verification complete")
```

### 3. Frontend Error Boundary Testing

```javascript
// Test React error boundaries
function testErrorBoundaries() {
  // Simulate JavaScript error in component
  const errorButton = screen.getByText('Trigger Error');
  fireEvent.click(errorButton);

  // Verify error boundary catches the error
  expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  expect(screen.getByText('Try again')).toBeInTheDocument();
}

// Test 404 page handling
function test404Handling() {
  // Navigate to non-existent route
  window.history.pushState({}, '', '/non-existent-route');

  // Verify 404 page is shown
  expect(screen.getByText('Page Not Found')).toBeInTheDocument();
  expect(screen.getByText('Go Home')).toBeInTheDocument();
}
```

---

## Performance Integration Testing

### 1. API Response Time Testing

```bash
# Test API response times
echo "Testing API Response Times..."

# Test critical endpoints
endpoints=(
  "GET /health"
  "GET /api/subjects"
  "GET /api/tutors"
  "POST /api/auth/login"
)

for endpoint in "${endpoints[@]}"; do
  method=$(echo $endpoint | cut -d' ' -f1)
  path=$(echo $endpoint | cut -d' ' -f2)

  # Measure response time
  time_ms=$(curl -s -o /dev/null -w "%{time_total}" \
    -X $method \
    http://localhost:8000$path | awk '{printf "%.0f", $1 * 1000}')

  if [ "$time_ms" -gt 1000 ]; then
    echo "❌ $endpoint: ${time_ms}ms (too slow)"
  elif [ "$time_ms" -gt 500 ]; then
    echo "⚠️ $endpoint: ${time_ms}ms (slow)"
  else
    echo "✅ $endpoint: ${time_ms}ms"
  fi
done
```

### 2. Frontend Loading Performance

```bash
# Use Lighthouse for frontend performance testing
npx lighthouse http://localhost:3000 \
  --output=json \
  --output-path=./lighthouse-results.json \
  --chrome-flags="--headless --no-sandbox"

# Check key metrics
node -e "
const results = require('./lighthouse-results.json');
const score = results.categories.performance.score * 100;
console.log('Performance Score:', score);

if (score < 70) {
  console.log('❌ Performance score too low');
  process.exit(1);
} else if (score < 85) {
  console.log('⚠️ Performance score could be better');
} else {
  console.log('✅ Performance score good');
}
"
```

### 3. Database Query Performance

```sql
-- Identify slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 100  -- queries taking > 100ms on average
ORDER BY mean_time DESC
LIMIT 10;

-- Check table bloat
SELECT
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup::numeric / (n_live_tup + n_dead_tup) * 100, 2) as bloat_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY bloat_ratio DESC;
```

---

## Monitoring and Debugging

### 1. Integration Test Logging

```python
# Comprehensive logging setup for integration tests
import logging
import sys

def setup_integration_logging():
    """Setup detailed logging for integration testing"""

    # Create logger
    logger = logging.getLogger('integration_test')
    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create file handler
    file_handler = logging.FileHandler('integration_test.log')
    file_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Use throughout tests
logger = setup_integration_logging()

def log_api_call(method, endpoint, response):
    """Log API call details"""
    logger.info(f"{method} {endpoint} -> {response.status_code}")
    if response.status_code >= 400:
        logger.error(f"Response: {response.text}")
```

### 2. Browser DevTools Integration Testing

```javascript
// Automated browser testing with detailed logging
async function runIntegrationTestWithLogging(page) {
  console.log('🚀 Starting integration test...');

  try {
    // Enable console logging
    page.on('console', msg => {
      console.log('PAGE LOG:', msg.text());
    });

    // Enable network logging
    page.on('request', request => {
      console.log('NETWORK REQUEST:', request.method(), request.url());
    });

    page.on('response', response => {
      console.log('NETWORK RESPONSE:', response.status(), response.url());
    });

    // Run test steps with detailed logging
    console.log('📝 Step 1: Navigate to login page');
    await page.goto('http://localhost:3000/login');

    console.log('📝 Step 2: Fill login form');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');

    console.log('📝 Step 3: Submit login');
    await page.click('button[type="submit"]');

    console.log('📝 Step 4: Verify dashboard access');
    await page.waitForURL('**/dashboard');

    console.log('✅ Integration test completed successfully');

  } catch (error) {
    console.error('❌ Integration test failed:', error);

    // Take screenshot on failure
    await page.screenshot({ path: 'integration-test-failure.png' });

    throw error;
  }
}
```

### 3. API Request/Response Interception

```javascript
// Intercept and log all API calls
await page.route('**/api/**', route => {
  const request = route.request();
  console.log(`API ${request.method()} ${request.url()}`);

  if (request.postData()) {
    console.log('Request body:', request.postData());
  }

  route.continue();
});

// Intercept responses
page.on('response', response => {
  if (response.url().includes('/api/')) {
    console.log(`API Response ${response.status()} ${response.url()}`);
  }
});
```

---

## CI/CD Integration Testing

### 1. GitHub Actions Integration Test Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Start Services
        run: |
          docker compose -f docker-compose.test.yml up -d
          ./scripts/wait-for-services.sh

      - name: Run Health Checks
        run: |
          curl -f http://localhost:8000/health
          curl -f http://localhost:3000

      - name: Run API Integration Tests
        run: docker compose -f docker-compose.test.yml exec backend pytest tests/integration/ -v

      - name: Run E2E Tests
        run: docker compose -f docker-compose.test.yml exec e2e-tests npm run test:e2e

      - name: Run Performance Tests
        run: |
          npx lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json
          node -e "const score = require('./lighthouse-report.json').categories.performance.score * 100; process.exit(score < 70 ? 1 : 0)"

      - name: Upload Test Artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-artifacts
          path: |
            tests/e2e/screenshots/
            tests/e2e/videos/
            lighthouse-report.json
            backend/test-results.xml
            frontend/test-results.xml

      - name: Cleanup
        if: always()
        run: docker compose -f docker-compose.test.yml down -v
```

### 2. Automated Integration Test Script

```bash
#!/bin/bash
# comprehensive-integration-test.sh

set -e

echo "🚀 Starting Comprehensive Integration Test Suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Running: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
    fi
}

# Basic connectivity tests
run_test "Service Health Checks" "curl -f http://localhost:8000/health && curl -f http://localhost:3000"
run_test "Database Connectivity" "docker compose -f docker-compose.test.yml exec db pg_isready -U postgres -d authapp"

# API integration tests
run_test "API Endpoint Accessibility" "python scripts/test_api_endpoints.py"
run_test "Authentication Flow" "python scripts/test_auth_flow.py"
run_test "CRUD Operations" "python scripts/test_crud_operations.py"

# Frontend integration tests
run_test "Frontend API Integration" "docker compose -f docker-compose.test.yml exec frontend npm run test:integration"
run_test "Component Data Flow" "docker compose -f docker-compose.test.yml exec frontend npm run test:data-flow"

# E2E tests
run_test "Student Booking Journey" "docker compose -f docker-compose.test.yml exec e2e-tests npx playwright test tests/e2e/student-journey.spec.ts"
run_test "Tutor Onboarding Journey" "docker compose -f docker-compose.test.yml exec e2e-tests npx playwright test tests/e2e/tutor-onboarding.spec.ts"

# Database integrity
run_test "Database Consistency" "python scripts/check_db_integrity.py"
run_test "Data Synchronization" "python scripts/test_data_sync.py"

# Performance tests
run_test "API Response Times" "./scripts/check_response_times.sh"
run_test "Frontend Performance" "npx lighthouse http://localhost:3000 --output=json --quiet --chrome-flags='--headless' | jq -e '.categories.performance.score > 0.7'"

echo ""
echo "📊 Test Results Summary:"
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo "  📈 Success Rate: $((PASSED * 100 / (PASSED + FAILED)))%"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All integration tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 $FAILED integration tests failed!${NC}"
    echo "Check the logs above for details."
    exit 1
fi
```

### 3. Integration Test Dashboard

```python
#!/usr/bin/env python3
"""
Integration Test Dashboard
Generates HTML report of integration test results
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def generate_integration_report(results_file="integration-results.json"):
    """Generate HTML integration test report"""

    if not os.path.exists(results_file):
        print("No results file found")
        return

    with open(results_file, 'r') as f:
        results = json.load(f)

    # Group results by category
    categories = defaultdict(list)
    for result in results:
        category = result.get('category', 'uncategorized')
        categories[category].append(result)

    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Integration Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .summary {{ background: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
            .category {{ margin-bottom: 30px; }}
            .test {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
            .passed {{ border-left-color: #4CAF50; background: #f8fff8; }}
            .failed {{ border-left-color: #f44336; background: #fff8f8; }}
            .warning {{ border-left-color: #ff9800; background: #fffbf0; }}
        </style>
    </head>
    <body>
        <h1>Integration Test Report</h1>
        <div class="summary">
            <h2>Test Summary</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Tests:</strong> {len(results)}</p>
            <p><strong>Passed:</strong> {sum(1 for r in results if r['status'] == 'passed')}</p>
            <p><strong>Failed:</strong> {sum(1 for r in results if r['status'] == 'failed')}</p>
        </div>

        {"".join(f'''
        <div class="category">
            <h2>{category.title()}</h2>
            {"".join(f'''
            <div class="test {result['status']}">
                <h3>{result['name']}</h3>
                <p><strong>Status:</strong> {result['status'].upper()}</p>
                <p><strong>Duration:</strong> {result.get('duration', 'N/A')}s</p>
                {"".join(f"<p><strong>Error:</strong> {result['error']}</p>" for result in [result] if result.get('error'))}
            </div>
            ''' for result in category_results)}
        </div>
        ''' for category, category_results in categories.items())}
    </body>
    </html>
    """

    with open('integration-report.html', 'w') as f:
        f.write(html)

    print("Integration report generated: integration-report.html")

if __name__ == "__main__":
    generate_integration_report()
```

---

## Quick Reference

### Integration Test Checklist

- [ ] **Environment Setup**: Services running and accessible
- [ ] **Basic Connectivity**: Network communication working
- [ ] **API Integration**: All endpoints responding correctly
- [ ] **Authentication Flow**: Login/logout working end-to-end
- [ ] **Data Flow**: CRUD operations consistent across layers
- [ ] **Real-time Features**: WebSocket messaging functional
- [ ] **Database Integrity**: Foreign keys and constraints valid
- [ ] **Error Handling**: Proper error responses and UI handling
- [ ] **Performance**: Response times within acceptable limits
- [ ] **Security**: Authentication and authorization enforced

### Common Integration Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **CORS Errors** | Frontend API calls fail | Check CORS configuration in backend |
| **Token Mismatch** | Auth works in one part, fails in another | Verify token storage and transmission |
| **Data Inconsistency** | Frontend shows different data than API | Check caching, state management |
| **WebSocket Issues** | Real-time features don't work | Verify WebSocket server configuration |
| **Database Locks** | Tests fail with deadlocks | Use transactions, avoid long-running operations |
| **Race Conditions** | Intermittent test failures | Add proper waits, use deterministic data |

### Troubleshooting Commands

```bash
# Check service logs
docker compose -f docker-compose.test.yml logs backend
docker compose -f docker-compose.test.yml logs frontend

# Inspect network connectivity
docker compose -f docker-compose.test.yml exec backend curl -v http://frontend:3000

# Database debugging
docker compose -f docker-compose.test.yml exec db psql -U postgres -d authapp -c "SELECT * FROM users LIMIT 5;"

# Network debugging
docker compose -f docker-compose.test.yml exec backend nslookup frontend
docker compose -f docker-compose.test.yml exec frontend nslookup backend
```

---

**Next Steps:**
1. Run the integration test suite using the scripts provided
2. Address any failing tests identified
3. Set up automated integration testing in CI/CD
4. Monitor integration health with the provided monitoring tools

This guide provides a comprehensive framework for ensuring frontend-backend integration works seamlessly across all user journeys and system components.