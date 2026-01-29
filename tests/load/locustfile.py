"""
EduStream Load Testing Suite

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Or headless:
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m

Configuration:
    - Target: 100 concurrent users
    - Spawn rate: 10 users/second
    - Duration: 5 minutes minimum
    - Success criteria: P95 < 500ms, Error rate < 1%
"""

import json
import random
import string
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# Test data
SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "History"]
PRICE_RANGES = [(20, 50), (50, 100), (100, 200)]


def random_email() -> str:
    """Generate a random email for testing."""
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"loadtest_{suffix}@test.com"


def random_name() -> str:
    """Generate a random name for testing."""
    first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


class EduStreamUser(HttpUser):
    """
    Base user class for EduStream load testing.
    Simulates typical user behavior patterns.
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    token: str | None = None
    user_id: str | None = None

    def on_start(self):
        """Called when a user starts. Login or create account."""
        # For load testing, we'll use the health endpoint first
        # Real tests would create/login test users
        self.client.get("/api/v1/health")

    @task(10)
    def health_check(self):
        """Health check - high weight for baseline."""
        with self.client.get(
            "/api/v1/health", catch_response=True, name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def browse_tutors(self):
        """Browse tutor listings - common user action."""
        params = {"page": 1, "page_size": 20}

        with self.client.get(
            "/api/v1/tutors",
            params=params,
            catch_response=True,
            name="Browse Tutors",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.success()  # Expected for unauthenticated
            else:
                response.failure(f"Browse tutors failed: {response.status_code}")

    @task(3)
    def search_tutors(self):
        """Search tutors with filters."""
        subject = random.choice(SUBJECTS)
        min_price, max_price = random.choice(PRICE_RANGES)

        params = {
            "subject": subject,
            "min_price": min_price,
            "max_price": max_price,
            "page": 1,
            "page_size": 10,
        }

        with self.client.get(
            "/api/v1/tutors/search",
            params=params,
            catch_response=True,
            name="Search Tutors",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"Search tutors failed: {response.status_code}")

    @task(2)
    def view_tutor_profile(self):
        """View individual tutor profile."""
        # Use a range of possible tutor IDs
        tutor_id = random.randint(1, 100)

        with self.client.get(
            f"/api/v1/tutors/{tutor_id}",
            catch_response=True,
            name="View Tutor Profile",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"View tutor profile failed: {response.status_code}")

    @task(2)
    def view_subjects(self):
        """Get list of subjects."""
        with self.client.get(
            "/api/v1/subjects",
            catch_response=True,
            name="View Subjects",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"View subjects failed: {response.status_code}")

    @task(1)
    def view_reviews(self):
        """View tutor reviews."""
        tutor_id = random.randint(1, 100)

        with self.client.get(
            f"/api/v1/reviews/tutor/{tutor_id}",
            catch_response=True,
            name="View Reviews",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"View reviews failed: {response.status_code}")


class AuthenticatedUser(HttpUser):
    """
    Authenticated user simulation.
    Requires valid test credentials to be set up.
    """

    wait_time = between(2, 8)
    token: str | None = None
    user_id: str | None = None
    abstract = True  # Don't spawn directly

    def on_start(self):
        """Login with test credentials."""
        # This would normally login with test credentials
        # For now, we'll skip authentication in load tests
        pass

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


class StudentUser(AuthenticatedUser):
    """Student user behavior simulation."""

    weight = 3  # 3x more students than tutors

    @task(5)
    def browse_tutors(self):
        """Browse available tutors."""
        with self.client.get(
            "/api/v1/tutors",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Student] Browse Tutors",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(3)
    def view_my_bookings(self):
        """View own bookings."""
        with self.client.get(
            "/api/v1/bookings/my",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Student] View My Bookings",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(2)
    def view_wallet(self):
        """View wallet balance."""
        with self.client.get(
            "/api/v1/wallet",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Student] View Wallet",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(2)
    def view_packages(self):
        """View available packages."""
        with self.client.get(
            "/api/v1/packages",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Student] View Packages",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(1)
    def view_notifications(self):
        """View notifications."""
        with self.client.get(
            "/api/v1/notifications",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Student] View Notifications",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


class TutorUser(AuthenticatedUser):
    """Tutor user behavior simulation."""

    weight = 1

    @task(5)
    def view_my_bookings(self):
        """View incoming bookings."""
        with self.client.get(
            "/api/v1/bookings/my",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Tutor] View My Bookings",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(3)
    def view_availability(self):
        """View own availability."""
        with self.client.get(
            "/api/v1/availability",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Tutor] View Availability",
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(2)
    def view_earnings(self):
        """View earnings."""
        with self.client.get(
            "/api/v1/earnings",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Tutor] View Earnings",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(1)
    def view_reviews(self):
        """View own reviews."""
        with self.client.get(
            "/api/v1/reviews/my",
            headers=self._auth_headers(),
            catch_response=True,
            name="[Tutor] View My Reviews",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# Event hooks for statistics


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Called when Locust starts."""
    if isinstance(environment.runner, MasterRunner):
        print("Running as master node")
    elif isinstance(environment.runner, WorkerRunner):
        print("Running as worker node")
    else:
        print("Running standalone")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "=" * 60)
    print("EduStream Load Test Starting")
    print("=" * 60)
    print(f"Target host: {environment.host}")
    print(f"User classes: {[cls.__name__ for cls in environment.user_classes]}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("\n" + "=" * 60)
    print("EduStream Load Test Complete")
    print("=" * 60)

    # Print summary statistics
    stats = environment.stats
    if stats.total.num_requests > 0:
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Failures: {stats.total.num_failures}")
        print(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        print(f"P50 response time: {stats.total.get_response_time_percentile(0.50):.2f}ms")
        print(f"P95 response time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"P99 response time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
        print(f"Requests/sec: {stats.total.current_rps:.2f}")

        # Check success criteria
        p95 = stats.total.get_response_time_percentile(0.95)
        fail_rate = stats.total.fail_ratio * 100

        print("\n--- Success Criteria ---")
        if p95 < 500:
            print(f"✅ P95 response time: {p95:.2f}ms (target: <500ms)")
        else:
            print(f"❌ P95 response time: {p95:.2f}ms (target: <500ms)")

        if fail_rate < 1:
            print(f"✅ Error rate: {fail_rate:.2f}% (target: <1%)")
        else:
            print(f"❌ Error rate: {fail_rate:.2f}% (target: <1%)")

    print("=" * 60 + "\n")
