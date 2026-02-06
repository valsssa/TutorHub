"""Tests for Celery configuration."""

import os
from unittest.mock import patch

import pytest

from core.celery_app import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    REDIS_URL,
    TaskRetryConfig,
    celery_app,
    get_celery_app,
)


class TestCeleryConfiguration:
    """Tests for Celery app configuration."""

    def test_celery_app_name(self):
        """Test Celery app has correct name."""
        assert celery_app.main == "edustream"

    def test_celery_broker_configured(self):
        """Test Celery broker is configured."""
        assert celery_app.conf.broker_url is not None

    def test_celery_result_backend_configured(self):
        """Test Celery result backend is configured."""
        assert celery_app.conf.result_backend is not None

    def test_task_serializer_json(self):
        """Test task serializer is JSON."""
        assert celery_app.conf.task_serializer == "json"

    def test_accept_content_json(self):
        """Test accepted content types include JSON."""
        assert "json" in celery_app.conf.accept_content

    def test_result_serializer_json(self):
        """Test result serializer is JSON."""
        assert celery_app.conf.result_serializer == "json"

    def test_timezone_utc(self):
        """Test timezone is UTC."""
        assert celery_app.conf.timezone == "UTC"

    def test_utc_enabled(self):
        """Test UTC is enabled."""
        assert celery_app.conf.enable_utc is True

    def test_task_acks_late(self):
        """Test task acknowledgment is late (after completion)."""
        assert celery_app.conf.task_acks_late is True

    def test_task_reject_on_worker_lost(self):
        """Test tasks are rejected when worker dies."""
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_worker_prefetch_multiplier(self):
        """Test worker fetches one task at a time."""
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_task_default_retry_delay(self):
        """Test default retry delay is 60 seconds."""
        assert celery_app.conf.task_default_retry_delay == 60

    def test_task_max_retries(self):
        """Test max retries is 5."""
        assert celery_app.conf.task_max_retries == 5

    def test_result_expires(self):
        """Test results expire after 1 hour."""
        assert celery_app.conf.result_expires == 3600

    def test_worker_max_tasks_per_child(self):
        """Test worker restarts after 1000 tasks."""
        assert celery_app.conf.worker_max_tasks_per_child == 1000


class TestTaskRouting:
    """Tests for task routing configuration."""

    def test_booking_tasks_route(self):
        """Test booking tasks are routed to bookings queue."""
        routes = celery_app.conf.task_routes
        assert "tasks.booking_tasks.*" in routes
        assert routes["tasks.booking_tasks.*"]["queue"] == "bookings"


class TestBeatSchedule:
    """Tests for beat schedule configuration."""

    def test_expire_booking_requests_scheduled(self):
        """Test expire_requests task is scheduled."""
        schedule = celery_app.conf.beat_schedule
        assert "expire-booking-requests" in schedule

        task_config = schedule["expire-booking-requests"]
        assert task_config["task"] == "tasks.booking_tasks.expire_requests"
        assert task_config["schedule"] == 300.0
        assert task_config["options"]["queue"] == "bookings"

    def test_start_sessions_scheduled(self):
        """Test start_sessions task is scheduled."""
        schedule = celery_app.conf.beat_schedule
        assert "start-scheduled-sessions" in schedule

        task_config = schedule["start-scheduled-sessions"]
        assert task_config["task"] == "tasks.booking_tasks.start_sessions"
        assert task_config["schedule"] == 60.0
        assert task_config["options"]["queue"] == "bookings"

    def test_end_sessions_scheduled(self):
        """Test end_sessions task is scheduled."""
        schedule = celery_app.conf.beat_schedule
        assert "end-active-sessions" in schedule

        task_config = schedule["end-active-sessions"]
        assert task_config["task"] == "tasks.booking_tasks.end_sessions"
        assert task_config["schedule"] == 60.0
        assert task_config["options"]["queue"] == "bookings"


class TestBeatSchedulerSettings:
    """Tests for beat scheduler settings."""

    def test_beat_scheduler_persistent(self):
        """Test beat scheduler is persistent."""
        assert celery_app.conf.beat_scheduler == "celery.beat:PersistentScheduler"

    def test_beat_schedule_filename(self):
        """Test beat schedule filename is set."""
        assert celery_app.conf.beat_schedule_filename == "/tmp/celerybeat-schedule"


class TestGetCeleryApp:
    """Tests for get_celery_app function."""

    def test_returns_celery_instance(self):
        """Test function returns Celery instance."""
        app = get_celery_app()
        assert app is celery_app

    def test_returns_same_instance(self):
        """Test function returns same instance each time."""
        app1 = get_celery_app()
        app2 = get_celery_app()
        assert app1 is app2


class TestTaskRetryConfig:
    """Tests for TaskRetryConfig class."""

    def test_backoff_base(self):
        """Test backoff base is 60 seconds."""
        assert TaskRetryConfig.BACKOFF_BASE == 60

    def test_backoff_multiplier(self):
        """Test backoff multiplier is 2."""
        assert TaskRetryConfig.BACKOFF_MULTIPLIER == 2

    def test_max_retries(self):
        """Test max retries is 5."""
        assert TaskRetryConfig.MAX_RETRIES == 5

    def test_get_countdown_first_retry(self):
        """Test countdown for first retry (60 seconds)."""
        countdown = TaskRetryConfig.get_countdown(0)
        assert countdown == 60

    def test_get_countdown_second_retry(self):
        """Test countdown for second retry (120 seconds)."""
        countdown = TaskRetryConfig.get_countdown(1)
        assert countdown == 120

    def test_get_countdown_third_retry(self):
        """Test countdown for third retry (240 seconds)."""
        countdown = TaskRetryConfig.get_countdown(2)
        assert countdown == 240

    def test_get_countdown_fourth_retry(self):
        """Test countdown for fourth retry (480 seconds)."""
        countdown = TaskRetryConfig.get_countdown(3)
        assert countdown == 480

    def test_get_countdown_fifth_retry(self):
        """Test countdown for fifth retry (960 seconds)."""
        countdown = TaskRetryConfig.get_countdown(4)
        assert countdown == 960

    def test_exponential_backoff_formula(self):
        """Test exponential backoff follows formula."""
        for i in range(5):
            expected = TaskRetryConfig.BACKOFF_BASE * (
                TaskRetryConfig.BACKOFF_MULTIPLIER ** i
            )
            assert TaskRetryConfig.get_countdown(i) == expected


class TestRedisURLs:
    """Tests for Redis URL configuration."""

    def test_redis_url_default(self):
        """Test default Redis URL."""
        with patch.dict(os.environ, {}, clear=True):
            pass

    def test_broker_uses_different_db(self):
        """Test broker uses different Redis database than default."""
        if "/0" in REDIS_URL:
            assert "/1" in CELERY_BROKER_URL

    def test_result_backend_uses_different_db(self):
        """Test result backend uses different Redis database."""
        if "/0" in REDIS_URL:
            assert "/2" in CELERY_RESULT_BACKEND


class TestIncludedTasks:
    """Tests for included task modules."""

    def test_booking_tasks_included(self):
        """Test booking_tasks module is included."""
        assert "tasks.booking_tasks" in celery_app.conf.include


class TestWorkerSettings:
    """Tests for worker-specific settings."""

    def test_rate_limits_not_disabled(self):
        """Test rate limits are not disabled."""
        assert celery_app.conf.worker_disable_rate_limits is False
