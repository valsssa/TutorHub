"""Tests for avatar storage module (MinIO/S3 storage client)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException


class TestAvatarStorageClient:
    """Test AvatarStorageClient class."""

    @pytest.fixture
    def storage_client(self):
        """Create AvatarStorageClient instance for testing."""
        from core.avatar_storage import AvatarStorageClient

        return AvatarStorageClient(
            endpoint="http://localhost:9000",
            access_key="test-access-key",
            secret_key="test-secret-key",
            bucket="test-bucket",
            region="us-east-1",
            use_ssl=False,
            public_endpoint="http://public.localhost:9000",
            url_ttl_seconds=300,
        )

    @pytest.fixture
    def storage_client_no_region(self):
        """Create AvatarStorageClient instance without region."""
        from core.avatar_storage import AvatarStorageClient

        return AvatarStorageClient(
            endpoint="http://localhost:9000",
            access_key="test-access-key",
            secret_key="test-secret-key",
            bucket="test-bucket",
            region=None,
            use_ssl=True,
            public_endpoint=None,
            url_ttl_seconds=600,
        )

    def test_init_sets_attributes(self, storage_client):
        """Test that __init__ properly sets all attributes."""
        assert storage_client._endpoint == "http://localhost:9000"
        assert storage_client._access_key == "test-access-key"
        assert storage_client._secret_key == "test-secret-key"
        assert storage_client._bucket == "test-bucket"
        assert storage_client._region == "us-east-1"
        assert storage_client._use_ssl is False
        assert storage_client._public_endpoint == "http://public.localhost:9000"
        assert storage_client._url_ttl_seconds == 300
        assert storage_client._bucket_initialized is False

    def test_init_defaults_public_endpoint_to_endpoint(self, storage_client_no_region):
        """Test that public_endpoint defaults to endpoint when None."""
        assert storage_client_no_region._public_endpoint == "http://localhost:9000"

    def test_init_region_none_handling(self, storage_client_no_region):
        """Test that None region is properly handled."""
        assert storage_client_no_region._region is None

    def test_bucket_property(self, storage_client):
        """Test bucket() returns bucket name."""
        assert storage_client.bucket() == "test-bucket"

    def test_public_endpoint_property(self, storage_client):
        """Test public_endpoint() returns public endpoint."""
        assert storage_client.public_endpoint() == "http://public.localhost:9000"

    def test_url_ttl_property(self, storage_client):
        """Test url_ttl() returns TTL seconds."""
        assert storage_client.url_ttl() == 300

    @pytest.mark.asyncio
    async def test_ensure_bucket_already_initialized(self, storage_client):
        """Test ensure_bucket returns early if already initialized."""
        storage_client._bucket_initialized = True

        # Should return without doing anything
        await storage_client.ensure_bucket()
        assert storage_client._bucket_initialized is True

    @pytest.mark.asyncio
    async def test_ensure_bucket_exists(self, storage_client):
        """Test ensure_bucket when bucket already exists."""
        mock_client = AsyncMock()
        mock_client.head_bucket = AsyncMock(return_value={})

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            await storage_client.ensure_bucket()

        assert storage_client._bucket_initialized is True
        mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")

    @pytest.mark.asyncio
    async def test_ensure_bucket_creates_bucket_on_404(self, storage_client):
        """Test ensure_bucket creates bucket when it doesn't exist."""
        mock_client = AsyncMock()

        # First call raises 404, then create_bucket succeeds
        error_response = {"Error": {"Code": "404"}}
        mock_client.head_bucket = AsyncMock(
            side_effect=ClientError(error_response, "HeadBucket")
        )
        mock_client.create_bucket = AsyncMock(return_value={})
        mock_client.put_bucket_policy = AsyncMock(return_value={})

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            await storage_client.ensure_bucket()

        assert storage_client._bucket_initialized is True
        mock_client.create_bucket.assert_called()

    @pytest.mark.asyncio
    async def test_ensure_bucket_creates_with_location_constraint(self):
        """Test ensure_bucket adds location constraint for non-us-east-1 regions."""
        from core.avatar_storage import AvatarStorageClient

        storage_client = AvatarStorageClient(
            endpoint="http://localhost:9000",
            access_key="test-access-key",
            secret_key="test-secret-key",
            bucket="test-bucket",
            region="eu-west-1",
            use_ssl=False,
            public_endpoint="http://public.localhost:9000",
            url_ttl_seconds=300,
        )

        mock_client = AsyncMock()
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        mock_client.head_bucket = AsyncMock(
            side_effect=ClientError(error_response, "HeadBucket")
        )
        mock_client.create_bucket = AsyncMock(return_value={})
        mock_client.put_bucket_policy = AsyncMock(return_value={})

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            await storage_client.ensure_bucket()

        # Verify location constraint was added for eu-west-1
        call_args = mock_client.create_bucket.call_args
        assert "CreateBucketConfiguration" in call_args.kwargs
        assert call_args.kwargs["CreateBucketConfiguration"]["LocationConstraint"] == "eu-west-1"

    @pytest.mark.asyncio
    async def test_ensure_bucket_create_fails_raises_http_exception(self, storage_client):
        """Test ensure_bucket raises HTTPException when bucket creation fails."""
        mock_client = AsyncMock()
        error_response = {"Error": {"Code": "404"}}
        mock_client.head_bucket = AsyncMock(
            side_effect=ClientError(error_response, "HeadBucket")
        )

        create_error = {"Error": {"Code": "AccessDenied"}}
        mock_client.create_bucket = AsyncMock(
            side_effect=ClientError(create_error, "CreateBucket")
        )

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            with pytest.raises(HTTPException) as exc_info:
                await storage_client.ensure_bucket()

        assert exc_info.value.status_code == 500
        assert "Unable to prepare avatar storage" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_ensure_bucket_access_error_raises_http_exception(self, storage_client):
        """Test ensure_bucket raises HTTPException for non-404 errors."""
        mock_client = AsyncMock()
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_client.head_bucket = AsyncMock(
            side_effect=ClientError(error_response, "HeadBucket")
        )

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            with pytest.raises(HTTPException) as exc_info:
                await storage_client.ensure_bucket()

        assert exc_info.value.status_code == 500
        assert "Unable to access avatar storage" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_client):
        """Test upload_file successfully uploads a file."""
        storage_client._bucket_initialized = True

        mock_client = AsyncMock()
        mock_client.put_object = AsyncMock(return_value={})

        file_content = b"test image content"

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            with patch("aiofiles.open", return_value=self._create_async_file_context(file_content)):
                await storage_client.upload_file(
                    key="avatars/user1.jpg",
                    file_path="/tmp/test.jpg",
                    content_type="image/jpeg",
                )

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="avatars/user1.jpg",
            Body=file_content,
            ContentType="image/jpeg",
            ACL="private",
            CacheControl="max-age=31536000, immutable",
        )

    @pytest.mark.asyncio
    async def test_upload_file_client_error_raises_http_exception(self, storage_client):
        """Test upload_file raises HTTPException on ClientError."""
        storage_client._bucket_initialized = True

        mock_client = AsyncMock()
        error_response = {"Error": {"Code": "InternalError"}}
        mock_client.put_object = AsyncMock(
            side_effect=ClientError(error_response, "PutObject")
        )

        file_content = b"test image content"

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            with patch("aiofiles.open", return_value=self._create_async_file_context(file_content)):
                with pytest.raises(HTTPException) as exc_info:
                    await storage_client.upload_file(
                        key="avatars/user1.jpg",
                        file_path="/tmp/test.jpg",
                        content_type="image/jpeg",
                    )

        assert exc_info.value.status_code == 500
        assert "Unable to store avatar" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_client):
        """Test delete_file successfully deletes a file."""
        mock_client = AsyncMock()
        mock_client.delete_object = AsyncMock(return_value={})

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            await storage_client.delete_file(key="avatars/user1.jpg")

        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="avatars/user1.jpg"
        )

    @pytest.mark.asyncio
    async def test_delete_file_empty_key_returns_early(self, storage_client):
        """Test delete_file returns early for empty key."""
        mock_client = AsyncMock()

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            await storage_client.delete_file(key="")

        # Should not call delete_object
        mock_client.delete_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_file_client_error_logs_warning(self, storage_client):
        """Test delete_file logs warning on ClientError but doesn't raise."""
        mock_client = AsyncMock()
        error_response = {"Error": {"Code": "InternalError"}}
        mock_client.delete_object = AsyncMock(
            side_effect=ClientError(error_response, "DeleteObject")
        )

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            # Should not raise, just log warning
            await storage_client.delete_file(key="avatars/user1.jpg")

    @pytest.mark.asyncio
    async def test_generate_presigned_url_success(self, storage_client):
        """Test generate_presigned_url returns presigned URL from S3 client."""
        mock_client = AsyncMock()
        expected_url = "http://public.localhost:9000/test-bucket/avatars/user1.jpg?X-Amz-Signature=abc123"
        mock_client.generate_presigned_url = AsyncMock(return_value=expected_url)

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            url = await storage_client.generate_presigned_url(key="avatars/user1.jpg")

        assert url == expected_url
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "avatars/user1.jpg"},
            ExpiresIn=300,
        )

    @pytest.mark.asyncio
    async def test_generate_presigned_url_empty_key_raises(self, storage_client):
        """Test generate_presigned_url raises HTTPException for empty key."""
        with pytest.raises(HTTPException) as exc_info:
            await storage_client.generate_presigned_url(key="")

        assert exc_info.value.status_code == 404
        assert "Avatar not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_presigned_url_strips_trailing_slash(self, storage_client):
        """Test generate_presigned_url works with trailing slash in endpoint."""
        storage_client._public_endpoint = "http://public.localhost:9000/"

        mock_client = AsyncMock()
        expected_url = "http://public.localhost:9000/test-bucket/avatars/user1.jpg?X-Amz-Signature=abc123"
        mock_client.generate_presigned_url = AsyncMock(return_value=expected_url)

        with patch.object(
            storage_client, "_client", return_value=self._create_async_context(mock_client)
        ):
            url = await storage_client.generate_presigned_url(key="avatars/user1.jpg")

        # URL should be generated via S3 client, which handles endpoint formatting
        assert url == expected_url

    def _create_async_context(self, mock_client):
        """Create an async context manager that yields mock_client."""

        class AsyncContextManager:
            async def __aenter__(self):
                return mock_client

            async def __aexit__(self, *args):
                pass

        return AsyncContextManager()

    def _create_async_file_context(self, content: bytes):
        """Create an async file context manager."""

        class AsyncFileContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def read(self):
                return content

        return AsyncFileContextManager()


class TestGetAvatarStorage:
    """Test get_avatar_storage factory function."""

    def test_get_avatar_storage_returns_client(self):
        """Test get_avatar_storage returns AvatarStorageClient."""
        from core.avatar_storage import get_avatar_storage, AvatarStorageClient

        # Clear the cache to ensure fresh instance
        get_avatar_storage.cache_clear()

        with patch("core.avatar_storage.settings") as mock_settings:
            mock_settings.AVATAR_STORAGE_ENDPOINT = "http://minio:9000"
            mock_settings.AVATAR_STORAGE_ACCESS_KEY = "access"
            mock_settings.AVATAR_STORAGE_SECRET_KEY = "secret"
            mock_settings.AVATAR_STORAGE_BUCKET = "avatars"
            mock_settings.AVATAR_STORAGE_REGION = "us-east-1"
            mock_settings.AVATAR_STORAGE_USE_SSL = False
            mock_settings.AVATAR_STORAGE_PUBLIC_ENDPOINT = "http://public:9000"
            mock_settings.AVATAR_STORAGE_URL_TTL_SECONDS = 300

            client = get_avatar_storage()

        assert isinstance(client, AvatarStorageClient)

    def test_get_avatar_storage_cached(self):
        """Test get_avatar_storage returns cached instance."""
        from core.avatar_storage import get_avatar_storage

        # Clear cache and get fresh instance
        get_avatar_storage.cache_clear()

        with patch("core.avatar_storage.settings") as mock_settings:
            mock_settings.AVATAR_STORAGE_ENDPOINT = "http://minio:9000"
            mock_settings.AVATAR_STORAGE_ACCESS_KEY = "access"
            mock_settings.AVATAR_STORAGE_SECRET_KEY = "secret"
            mock_settings.AVATAR_STORAGE_BUCKET = "avatars"
            mock_settings.AVATAR_STORAGE_REGION = None
            mock_settings.AVATAR_STORAGE_USE_SSL = False
            mock_settings.AVATAR_STORAGE_PUBLIC_ENDPOINT = None
            mock_settings.AVATAR_STORAGE_URL_TTL_SECONDS = 300

            client1 = get_avatar_storage()
            client2 = get_avatar_storage()

        assert client1 is client2


class TestBuildAvatarUrl:
    """Test build_avatar_url function with presigned URL generation."""

    def test_build_avatar_url_none_key_returns_default(self):
        """Test build_avatar_url returns default for None key."""
        from core.avatar_storage import build_avatar_url

        result = build_avatar_url(None, default="https://example.com/default.png")
        assert result == "https://example.com/default.png"

    def test_build_avatar_url_empty_key_returns_default(self):
        """Test build_avatar_url returns default for empty key."""
        from core.avatar_storage import build_avatar_url

        result = build_avatar_url("", default="https://example.com/default.png")
        assert result == "https://example.com/default.png"

    def test_build_avatar_url_absolute_url_returned_unchanged(self):
        """Test build_avatar_url returns absolute URLs unchanged (OAuth avatars)."""
        from core.avatar_storage import build_avatar_url

        http_url = "http://example.com/avatar.jpg"
        https_url = "https://example.com/avatar.jpg"

        assert build_avatar_url(http_url) == http_url
        assert build_avatar_url(https_url) == https_url

    def test_build_avatar_url_generates_presigned_url(self):
        """Test build_avatar_url generates presigned URL for storage keys."""
        from core.avatar_storage import (
            _get_sync_s3_client,
            build_avatar_url,
        )

        # Clear caches
        _get_sync_s3_client.cache_clear()

        mock_presigned_url = "https://minio.example.com/avatars/users/123/avatar.jpg?X-Amz-Signature=abc123"

        with patch("core.avatar_storage._get_sync_s3_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = mock_presigned_url
            mock_get_client.return_value = mock_client

            result = build_avatar_url("users/123/avatar.jpg")

            assert result == mock_presigned_url
            mock_client.generate_presigned_url.assert_called_once()

    def test_build_avatar_url_absolute_not_allowed_generates_presigned(self):
        """Test build_avatar_url with allow_absolute=False generates presigned URL."""
        from core.avatar_storage import (
            _get_sync_s3_client,
            build_avatar_url,
        )

        _get_sync_s3_client.cache_clear()

        mock_presigned_url = "https://minio.example.com/avatars/key?X-Amz-Signature=xyz"

        with patch("core.avatar_storage._get_sync_s3_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = mock_presigned_url
            mock_get_client.return_value = mock_client

            # Even with a URL-like key, should generate presigned URL when allow_absolute=False
            result = build_avatar_url(
                "http://example.com/avatar.jpg",
                allow_absolute=False
            )

            assert result == mock_presigned_url

    def test_build_avatar_url_no_default_returns_none(self):
        """Test build_avatar_url returns None when no default and empty key."""
        from core.avatar_storage import build_avatar_url

        result = build_avatar_url(None)
        assert result is None

        result = build_avatar_url("")
        assert result is None

    def test_generate_presigned_url_sync_uses_configured_ttl(self):
        """Test presigned URL uses configured TTL."""
        from core.avatar_storage import (
            _get_sync_s3_client,
            generate_presigned_url_sync,
        )

        _get_sync_s3_client.cache_clear()

        with patch("core.avatar_storage._get_sync_s3_client") as mock_get_client:
            with patch("core.avatar_storage.settings") as mock_settings:
                mock_settings.AVATAR_STORAGE_URL_TTL_SECONDS = 600
                mock_settings.AVATAR_STORAGE_BUCKET = "avatars"

                mock_client = MagicMock()
                mock_client.generate_presigned_url.return_value = "https://signed-url"
                mock_get_client.return_value = mock_client

                generate_presigned_url_sync("test/key.jpg")

                # Verify TTL was passed correctly
                call_args = mock_client.generate_presigned_url.call_args
                assert call_args[1]["ExpiresIn"] == 600

    def test_generate_presigned_url_sync_custom_ttl(self):
        """Test presigned URL with custom TTL override."""
        from core.avatar_storage import (
            _get_sync_s3_client,
            generate_presigned_url_sync,
        )

        _get_sync_s3_client.cache_clear()

        with patch("core.avatar_storage._get_sync_s3_client") as mock_get_client:
            with patch("core.avatar_storage.settings") as mock_settings:
                mock_settings.AVATAR_STORAGE_URL_TTL_SECONDS = 300
                mock_settings.AVATAR_STORAGE_BUCKET = "avatars"

                mock_client = MagicMock()
                mock_client.generate_presigned_url.return_value = "https://signed-url"
                mock_get_client.return_value = mock_client

                # Pass custom TTL
                generate_presigned_url_sync("test/key.jpg", ttl_seconds=3600)

                call_args = mock_client.generate_presigned_url.call_args
                assert call_args[1]["ExpiresIn"] == 3600
