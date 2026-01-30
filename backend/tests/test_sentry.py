"""Tests for Sentry error monitoring configuration."""

from unittest.mock import MagicMock, patch

import pytest


class TestInitSentry:
    """Test init_sentry function."""

    def test_init_sentry_no_dsn_returns_false(self):
        """Test init_sentry returns False when no DSN configured."""
        from core.sentry import init_sentry

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            result = init_sentry()

        assert result is False

    def test_init_sentry_empty_dsn_returns_false(self):
        """Test init_sentry returns False for empty DSN."""
        from core.sentry import init_sentry

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = ""

            result = init_sentry()

        assert result is False

    def test_init_sentry_with_dsn_initializes_sentry(self):
        """Test init_sentry initializes Sentry SDK when DSN provided."""
        from core.sentry import init_sentry

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
            mock_settings.SENTRY_TRACES_SAMPLE_RATE = 0.1
            mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 0.1
            mock_settings.ENVIRONMENT = "testing"
            mock_settings.APP_VERSION = "1.0.0"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                result = init_sentry()

        assert result is True
        mock_sentry.init.assert_called_once()

    def test_init_sentry_uses_correct_config(self):
        """Test init_sentry passes correct configuration to sentry_sdk.init."""
        from core.sentry import init_sentry

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
            mock_settings.SENTRY_TRACES_SAMPLE_RATE = 0.25
            mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 0.15
            mock_settings.ENVIRONMENT = "production"
            mock_settings.APP_VERSION = "2.0.0"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                init_sentry()

        call_kwargs = mock_sentry.init.call_args.kwargs
        assert call_kwargs["dsn"] == "https://test@sentry.io/123"
        assert call_kwargs["traces_sample_rate"] == 0.25
        assert call_kwargs["profiles_sample_rate"] == 0.15
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["release"] == "edustream-backend@2.0.0"
        assert call_kwargs["send_default_pii"] is False
        assert call_kwargs["attach_stacktrace"] is True


class TestBeforeSend:
    """Test _before_send filter function."""

    def test_before_send_filters_401_http_exception(self):
        """Test _before_send filters out 401 HTTP exceptions."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        mock_exception = MagicMock()
        mock_exception.status_code = 401
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        assert result is None

    def test_before_send_filters_403_http_exception(self):
        """Test _before_send filters out 403 HTTP exceptions."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        mock_exception = MagicMock()
        mock_exception.status_code = 403
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        assert result is None

    def test_before_send_filters_404_http_exception(self):
        """Test _before_send filters out 404 HTTP exceptions."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        mock_exception = MagicMock()
        mock_exception.status_code = 404
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        assert result is None

    def test_before_send_filters_422_http_exception(self):
        """Test _before_send filters out 422 HTTP exceptions."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        mock_exception = MagicMock()
        mock_exception.status_code = 422
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        assert result is None

    def test_before_send_allows_500_http_exception(self):
        """Test _before_send allows 500 HTTP exceptions."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        mock_exception = MagicMock()
        mock_exception.status_code = 500
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        assert result == event

    def test_before_send_filters_sensitive_headers(self):
        """Test _before_send filters sensitive headers."""
        from core.sentry import _before_send

        event = {
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "cookie": "session=abc123",
                    "x-api-key": "my-api-key",
                    "content-type": "application/json",
                }
            }
        }

        result = _before_send(event, {})

        assert result["request"]["headers"]["authorization"] == "[Filtered]"
        assert result["request"]["headers"]["cookie"] == "[Filtered]"
        assert result["request"]["headers"]["x-api-key"] == "[Filtered]"
        assert result["request"]["headers"]["content-type"] == "application/json"

    def test_before_send_filters_sensitive_body_fields(self):
        """Test _before_send filters sensitive body fields."""
        from core.sentry import _before_send

        event = {
            "request": {
                "data": {
                    "password": "secret123",
                    "token": "jwt-token",
                    "secret": "my-secret",
                    "api_key": "api-key-value",
                    "credit_card": "1234-5678-9012-3456",
                    "username": "testuser",
                }
            }
        }

        result = _before_send(event, {})

        assert result["request"]["data"]["password"] == "[Filtered]"
        assert result["request"]["data"]["token"] == "[Filtered]"
        assert result["request"]["data"]["secret"] == "[Filtered]"
        assert result["request"]["data"]["api_key"] == "[Filtered]"
        assert result["request"]["data"]["credit_card"] == "[Filtered]"
        assert result["request"]["data"]["username"] == "testuser"

    def test_before_send_handles_non_dict_body(self):
        """Test _before_send handles non-dict request body gracefully."""
        from core.sentry import _before_send

        event = {
            "request": {
                "data": "string body content"
            }
        }

        result = _before_send(event, {})

        assert result["request"]["data"] == "string body content"

    def test_before_send_handles_missing_request(self):
        """Test _before_send handles missing request key."""
        from core.sentry import _before_send

        event = {"message": "test event"}

        result = _before_send(event, {})

        assert result == event

    def test_before_send_handles_exception_without_status_code(self):
        """Test _before_send handles exception without status_code attribute."""
        from core.sentry import _before_send

        event = {
            "exception": {
                "values": [{"type": "HTTPException"}]
            }
        }

        # Exception without status_code attribute
        mock_exception = object()
        hint = {"exc_info": [None, mock_exception, None]}

        result = _before_send(event, hint)

        # Should return event since we can't check status_code
        assert result == event


class TestBeforeSendTransaction:
    """Test _before_send_transaction filter function."""

    def test_before_send_transaction_filters_health_endpoint(self):
        """Test _before_send_transaction filters /health endpoint."""
        from core.sentry import _before_send_transaction

        event = {"transaction": "/health"}

        result = _before_send_transaction(event, {})

        assert result is None

    def test_before_send_transaction_filters_integrity_health(self):
        """Test _before_send_transaction filters /api/health/integrity endpoint."""
        from core.sentry import _before_send_transaction

        event = {"transaction": "/api/health/integrity"}

        result = _before_send_transaction(event, {})

        assert result is None

    def test_before_send_transaction_filters_static_files(self):
        """Test _before_send_transaction filters static file requests."""
        from core.sentry import _before_send_transaction

        static_transactions = [
            "/static/css/main.css",
            "/static/js/app.js",
            "/static/images/logo.png",
        ]

        for transaction_name in static_transactions:
            event = {"transaction": transaction_name}
            result = _before_send_transaction(event, {})
            assert result is None, f"Expected {transaction_name} to be filtered"

    def test_before_send_transaction_filters_next_files(self):
        """Test _before_send_transaction filters /_next/ requests."""
        from core.sentry import _before_send_transaction

        next_transactions = [
            "/_next/static/chunks/main.js",
            "/_next/data/build/page.json",
            "/_next/image?url=test",
        ]

        for transaction_name in next_transactions:
            event = {"transaction": transaction_name}
            result = _before_send_transaction(event, {})
            assert result is None, f"Expected {transaction_name} to be filtered"

    def test_before_send_transaction_allows_api_endpoints(self):
        """Test _before_send_transaction allows API endpoints."""
        from core.sentry import _before_send_transaction

        api_transactions = [
            "/api/v1/auth/login",
            "/api/v1/users/me",
            "/api/v1/bookings",
            "/api/v1/tutors/search",
        ]

        for transaction_name in api_transactions:
            event = {"transaction": transaction_name}
            result = _before_send_transaction(event, {})
            assert result == event, f"Expected {transaction_name} to be allowed"

    def test_before_send_transaction_handles_empty_transaction(self):
        """Test _before_send_transaction handles empty transaction name."""
        from core.sentry import _before_send_transaction

        event = {"transaction": ""}

        result = _before_send_transaction(event, {})

        assert result == event


class TestCaptureException:
    """Test capture_exception function."""

    def test_capture_exception_no_dsn_returns_none(self):
        """Test capture_exception returns None when no DSN configured."""
        from core.sentry import capture_exception

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            result = capture_exception(Exception("test error"))

        assert result is None

    def test_capture_exception_with_dsn_captures_exception(self):
        """Test capture_exception captures exception when DSN configured."""
        from core.sentry import capture_exception

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.push_scope.return_value.__enter__ = MagicMock()
                mock_sentry.push_scope.return_value.__exit__ = MagicMock()
                mock_sentry.capture_exception.return_value = "event-id-123"

                error = Exception("test error")
                result = capture_exception(error, user_id=123)

        mock_sentry.capture_exception.assert_called_once_with(error)

    def test_capture_exception_sets_extra_context(self):
        """Test capture_exception sets extra context on scope."""
        from core.sentry import capture_exception

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            mock_scope = MagicMock()

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
                mock_sentry.push_scope.return_value.__exit__ = MagicMock()

                capture_exception(
                    Exception("test"),
                    user_id=123,
                    booking_id=456,
                )

        mock_scope.set_extra.assert_any_call("user_id", 123)
        mock_scope.set_extra.assert_any_call("booking_id", 456)


class TestCaptureMessage:
    """Test capture_message function."""

    def test_capture_message_no_dsn_returns_none(self):
        """Test capture_message returns None when no DSN configured."""
        from core.sentry import capture_message

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            result = capture_message("test message")

        assert result is None

    def test_capture_message_with_dsn_captures_message(self):
        """Test capture_message captures message when DSN configured."""
        from core.sentry import capture_message

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.push_scope.return_value.__enter__ = MagicMock()
                mock_sentry.push_scope.return_value.__exit__ = MagicMock()
                mock_sentry.capture_message.return_value = "event-id-456"

                result = capture_message("important event", level="warning")

        mock_sentry.capture_message.assert_called_once_with(
            "important event", level="warning"
        )

    def test_capture_message_default_level_is_info(self):
        """Test capture_message uses 'info' as default level."""
        from core.sentry import capture_message

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.push_scope.return_value.__enter__ = MagicMock()
                mock_sentry.push_scope.return_value.__exit__ = MagicMock()

                capture_message("test message")

        mock_sentry.capture_message.assert_called_once_with(
            "test message", level="info"
        )

    def test_capture_message_sets_extra_context(self):
        """Test capture_message sets extra context on scope."""
        from core.sentry import capture_message

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            mock_scope = MagicMock()

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
                mock_sentry.push_scope.return_value.__exit__ = MagicMock()

                capture_message(
                    "payment processed",
                    amount=100.00,
                    currency="USD",
                )

        mock_scope.set_extra.assert_any_call("amount", 100.00)
        mock_scope.set_extra.assert_any_call("currency", "USD")


class TestSetUserContext:
    """Test set_user_context function."""

    def test_set_user_context_no_dsn_returns_early(self):
        """Test set_user_context returns early when no DSN configured."""
        from core.sentry import set_user_context

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                set_user_context(user_id=123)

        mock_sentry.set_user.assert_not_called()

    def test_set_user_context_with_dsn_sets_user(self):
        """Test set_user_context sets user when DSN configured."""
        from core.sentry import set_user_context

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                set_user_context(user_id=123, email="test@example.com", role="admin")

        mock_sentry.set_user.assert_called_once_with({
            "id": "123",
            "email": "test@example.com",
            "role": "admin",
        })

    def test_set_user_context_without_optional_fields(self):
        """Test set_user_context works without optional email and role."""
        from core.sentry import set_user_context

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                set_user_context(user_id=456)

        mock_sentry.set_user.assert_called_once_with({
            "id": "456",
            "email": None,
            "role": None,
        })


class TestClearUserContext:
    """Test clear_user_context function."""

    def test_clear_user_context_no_dsn_returns_early(self):
        """Test clear_user_context returns early when no DSN configured."""
        from core.sentry import clear_user_context

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = None

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                clear_user_context()

        mock_sentry.set_user.assert_not_called()

    def test_clear_user_context_with_dsn_clears_user(self):
        """Test clear_user_context clears user when DSN configured."""
        from core.sentry import clear_user_context

        with patch("core.sentry.settings") as mock_settings:
            mock_settings.SENTRY_DSN = "https://test@sentry.io/123"

            with patch("core.sentry.sentry_sdk") as mock_sentry:
                clear_user_context()

        mock_sentry.set_user.assert_called_once_with(None)
