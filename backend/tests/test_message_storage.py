"""
Comprehensive tests for the Message Attachment Storage module.

Tests cover:
- S3 client initialization (lazy loading)
- Bucket creation and existence checking
- File type validation and categorization
- File size validation
- Image dimension extraction
- Secure key generation
- File upload functionality
- Presigned URL generation
- File deletion
- File existence checking
- Error handling and edge cases
"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from PIL import Image

from core.message_storage import (
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    MAX_IMAGE_SIZE,
    PRESIGNED_URL_EXPIRY,
    _categorize_file,
    _ensure_bucket_exists,
    _extract_image_dimensions,
    _generate_secure_key,
    _s3_client,
    check_file_exists,
    delete_message_attachment,
    generate_presigned_url,
    store_message_attachment,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_settings():
    """Mock settings for message storage."""
    with patch("core.message_storage.settings") as mock:
        mock.MESSAGE_ATTACHMENT_STORAGE_ENDPOINT = "http://minio:9000"
        mock.MESSAGE_ATTACHMENT_STORAGE_ACCESS_KEY = "minioadmin"
        mock.MESSAGE_ATTACHMENT_STORAGE_SECRET_KEY = "minioadmin123"
        mock.MESSAGE_ATTACHMENT_STORAGE_BUCKET = "message-attachments"
        mock.MESSAGE_ATTACHMENT_STORAGE_REGION = "us-east-1"
        mock.MESSAGE_ATTACHMENT_STORAGE_USE_SSL = False
        mock.MESSAGE_ATTACHMENT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        mock.MESSAGE_ATTACHMENT_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
        mock.MESSAGE_ATTACHMENT_URL_TTL_SECONDS = 3600
        yield mock


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    with patch("core.message_storage._s3_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_boto3():
    """Mock boto3 session and client."""
    with patch("core.message_storage.boto3.session.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        yield mock_session, mock_client


def create_test_image(width: int = 100, height: int = 100, format: str = "PNG") -> bytes:
    """Helper to create test image bytes."""
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 0, 0)).save(buffer, format=format)
    return buffer.getvalue()


def create_upload_file(
    content: bytes,
    filename: str = "test.txt",
    content_type: str = "text/plain",
) -> UploadFile:
    """Helper to create mock UploadFile."""
    BytesIO(content)
    upload = MagicMock(spec=UploadFile)
    upload.filename = filename
    upload.content_type = content_type
    upload.read = AsyncMock(return_value=content)
    return upload


# =============================================================================
# Test Constants and Configuration
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_allowed_image_types(self):
        """Test allowed image MIME types."""
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES
        assert "image/png" in ALLOWED_IMAGE_TYPES
        assert "image/gif" in ALLOWED_IMAGE_TYPES
        assert "image/webp" in ALLOWED_IMAGE_TYPES

    def test_allowed_document_types(self):
        """Test allowed document MIME types."""
        assert "application/pdf" in ALLOWED_DOCUMENT_TYPES
        assert "application/msword" in ALLOWED_DOCUMENT_TYPES
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ALLOWED_DOCUMENT_TYPES
        assert "text/plain" in ALLOWED_DOCUMENT_TYPES

    def test_allowed_mime_types_union(self):
        """Test that ALLOWED_MIME_TYPES is union of image and document types."""
        assert ALLOWED_MIME_TYPES == ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

    def test_max_file_size_is_reasonable(self):
        """Test that max file size is within expected range."""
        assert MAX_FILE_SIZE > 0
        assert MAX_FILE_SIZE <= 50 * 1024 * 1024  # Should not exceed 50 MB

    def test_max_image_size_less_than_file_size(self):
        """Test that max image size is less than or equal to max file size."""
        assert MAX_IMAGE_SIZE <= MAX_FILE_SIZE

    def test_presigned_url_expiry_is_reasonable(self):
        """Test that presigned URL expiry is within expected range."""
        assert PRESIGNED_URL_EXPIRY > 0
        assert PRESIGNED_URL_EXPIRY <= 86400  # Should not exceed 24 hours


# =============================================================================
# Test File Categorization
# =============================================================================


class TestCategorizeFile:
    """Tests for file categorization."""

    def test_categorize_jpeg_as_image(self):
        """Test JPEG is categorized as image."""
        assert _categorize_file("image/jpeg") == "image"

    def test_categorize_png_as_image(self):
        """Test PNG is categorized as image."""
        assert _categorize_file("image/png") == "image"

    def test_categorize_gif_as_image(self):
        """Test GIF is categorized as image."""
        assert _categorize_file("image/gif") == "image"

    def test_categorize_webp_as_image(self):
        """Test WebP is categorized as image."""
        assert _categorize_file("image/webp") == "image"

    def test_categorize_pdf_as_document(self):
        """Test PDF is categorized as document."""
        assert _categorize_file("application/pdf") == "document"

    def test_categorize_word_doc_as_document(self):
        """Test Word doc is categorized as document."""
        assert _categorize_file("application/msword") == "document"

    def test_categorize_docx_as_document(self):
        """Test DOCX is categorized as document."""
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert _categorize_file(mime_type) == "document"

    def test_categorize_text_as_document(self):
        """Test plain text is categorized as document."""
        assert _categorize_file("text/plain") == "document"

    def test_categorize_unknown_as_other(self):
        """Test unknown MIME type is categorized as other."""
        assert _categorize_file("application/octet-stream") == "other"

    def test_categorize_video_as_other(self):
        """Test video is categorized as other."""
        assert _categorize_file("video/mp4") == "other"

    def test_categorize_audio_as_other(self):
        """Test audio is categorized as other."""
        assert _categorize_file("audio/mpeg") == "other"


# =============================================================================
# Test Image Dimension Extraction
# =============================================================================


class TestExtractImageDimensions:
    """Tests for image dimension extraction."""

    def test_extract_png_dimensions(self):
        """Test extracting dimensions from PNG image."""
        image_bytes = create_test_image(200, 150, "PNG")
        width, height = _extract_image_dimensions(image_bytes)

        assert width == 200
        assert height == 150

    def test_extract_jpeg_dimensions(self):
        """Test extracting dimensions from JPEG image."""
        image_bytes = create_test_image(800, 600, "JPEG")
        width, height = _extract_image_dimensions(image_bytes)

        assert width == 800
        assert height == 600

    def test_extract_gif_dimensions(self):
        """Test extracting dimensions from GIF image."""
        image_bytes = create_test_image(320, 240, "GIF")
        width, height = _extract_image_dimensions(image_bytes)

        assert width == 320
        assert height == 240

    def test_extract_dimensions_from_invalid_data(self):
        """Test extracting dimensions from non-image data."""
        invalid_data = b"This is not an image"
        width, height = _extract_image_dimensions(invalid_data)

        assert width is None
        assert height is None

    def test_extract_dimensions_from_corrupted_image(self):
        """Test extracting dimensions from corrupted image."""
        # Create partial/corrupted image data
        corrupted_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        width, height = _extract_image_dimensions(corrupted_data)

        assert width is None
        assert height is None

    def test_extract_dimensions_from_empty_bytes(self):
        """Test extracting dimensions from empty bytes."""
        width, height = _extract_image_dimensions(b"")

        assert width is None
        assert height is None


# =============================================================================
# Test Secure Key Generation
# =============================================================================


class TestGenerateSecureKey:
    """Tests for secure storage key generation."""

    def test_key_format(self):
        """Test generated key follows expected format."""
        key = _generate_secure_key(123, 456, "test.pdf")

        assert key.startswith("messages/123/456/")
        assert key.endswith(".pdf")

    def test_key_contains_random_component(self):
        """Test that key contains random hex string."""
        key1 = _generate_secure_key(1, 1, "file.txt")
        key2 = _generate_secure_key(1, 1, "file.txt")

        # Keys should be different due to random component
        assert key1 != key2

    def test_key_sanitizes_filename(self):
        """Test that unsafe characters are removed from filename."""
        key = _generate_secure_key(1, 1, "../../../etc/passwd")

        assert ".." not in key
        assert "etc" not in key
        assert "passwd" not in key

    def test_key_handles_special_characters(self):
        """Test handling of special characters in filename."""
        key = _generate_secure_key(1, 1, "file with spaces & symbols!.pdf")

        # Key should be safe (alphanumeric, dash, underscore, dot only)
        assert " " not in key
        assert "&" not in key
        assert "!" not in key

    def test_key_handles_empty_filename(self):
        """Test handling of empty filename."""
        key = _generate_secure_key(1, 1, "")

        assert "messages/1/1/" in key
        # Should still have random hex component

    def test_key_handles_none_filename(self):
        """Test handling of None-like filename."""
        with patch("core.message_storage.sanitize_filename") as mock_sanitize:
            mock_sanitize.return_value = None
            key = _generate_secure_key(1, 1, None)

            assert "messages/1/1/" in key

    def test_key_normalizes_extension(self):
        """Test that extension is normalized to lowercase."""
        key = _generate_secure_key(1, 1, "file.PDF")

        assert key.endswith(".pdf")

    def test_key_handles_no_extension(self):
        """Test handling of filename without extension."""
        key = _generate_secure_key(1, 1, "filenoext")

        assert "messages/1/1/" in key
        # Should have no extension or just hex

    def test_key_limits_extension_length(self):
        """Test that long extensions are handled."""
        key = _generate_secure_key(1, 1, "file.verylongextension")

        # Extension should be replaced with 'bin' if too long or not alphanumeric
        assert "verylongextension" not in key or ".bin" in key


# =============================================================================
# Test Bucket Management
# =============================================================================


class TestEnsureBucketExists:
    """Tests for bucket existence checking and creation."""

    def test_bucket_exists(self, mock_s3_client, mock_settings):
        """Test when bucket already exists."""
        mock_s3_client.head_bucket.return_value = {}

        # Should not raise
        _ensure_bucket_exists()

        mock_s3_client.head_bucket.assert_called_once()

    def test_bucket_created_when_not_exists(self, mock_s3_client, mock_settings):
        """Test bucket creation when it doesn't exist."""
        # Simulate bucket not found
        error_response = {"Error": {"Code": "404"}}
        mock_s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        _ensure_bucket_exists()

        mock_s3_client.create_bucket.assert_called_once()

    def test_bucket_creation_with_region(self, mock_settings):
        """Test bucket creation with non-us-east-1 region."""
        mock_settings.MESSAGE_ATTACHMENT_STORAGE_REGION = "eu-west-1"

        with patch("core.message_storage._s3_client") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client

            error_response = {"Error": {"Code": "404"}}
            mock_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

            _ensure_bucket_exists()

            create_call = mock_client.create_bucket.call_args
            assert "CreateBucketConfiguration" in create_call[1]

    def test_bucket_already_owned_not_error(self, mock_s3_client, mock_settings):
        """Test that BucketAlreadyOwnedByYou is handled."""
        # First head_bucket fails with 404
        error_404 = {"Error": {"Code": "404"}}
        mock_s3_client.head_bucket.side_effect = ClientError(error_404, "HeadBucket")

        # create_bucket returns BucketAlreadyOwnedByYou
        error_owned = {"Error": {"Code": "BucketAlreadyOwnedByYou"}}
        mock_s3_client.create_bucket.side_effect = ClientError(error_owned, "CreateBucket")

        # Should not raise
        _ensure_bucket_exists()

    def test_bucket_check_error_raises_http_exception(self, mock_s3_client, mock_settings):
        """Test that other errors raise HTTPException."""
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        mock_s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        with pytest.raises(HTTPException) as exc_info:
            _ensure_bucket_exists()

        assert exc_info.value.status_code == 500

    def test_bucket_creation_error_raises_http_exception(self, mock_s3_client, mock_settings):
        """Test that bucket creation failure raises HTTPException."""
        # head_bucket fails with 404
        error_404 = {"Error": {"Code": "404"}}
        mock_s3_client.head_bucket.side_effect = ClientError(error_404, "HeadBucket")

        # create_bucket fails with unexpected error
        error_other = {"Error": {"Code": "InternalError"}}
        mock_s3_client.create_bucket.side_effect = ClientError(error_other, "CreateBucket")

        with pytest.raises(HTTPException) as exc_info:
            _ensure_bucket_exists()

        assert exc_info.value.status_code == 500


# =============================================================================
# Test File Upload
# =============================================================================


class TestStoreMessageAttachment:
    """Tests for storing message attachments."""

    @pytest.mark.asyncio
    async def test_upload_pdf_success(self, mock_s3_client, mock_settings):
        """Test successful PDF upload."""
        mock_s3_client.head_bucket.return_value = {}

        pdf_content = b"%PDF-1.4 test content"
        upload = create_upload_file(pdf_content, "document.pdf", "application/pdf")

        result = await store_message_attachment(
            user_id=1,
            message_id=100,
            upload=upload,
        )

        assert result["original_filename"] == "document.pdf"
        assert result["mime_type"] == "application/pdf"
        assert result["file_category"] == "document"
        assert result["file_size"] == len(pdf_content)
        assert "file_key" in result
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_image_with_dimensions(self, mock_s3_client, mock_settings):
        """Test image upload extracts dimensions."""
        mock_s3_client.head_bucket.return_value = {}

        image_content = create_test_image(400, 300, "PNG")
        upload = create_upload_file(image_content, "photo.png", "image/png")

        result = await store_message_attachment(
            user_id=2,
            message_id=200,
            upload=upload,
        )

        assert result["mime_type"] == "image/png"
        assert result["file_category"] == "image"
        assert result["width"] == 400
        assert result["height"] == 300

    @pytest.mark.asyncio
    async def test_upload_jpeg_image(self, mock_s3_client, mock_settings):
        """Test JPEG image upload."""
        mock_s3_client.head_bucket.return_value = {}

        image_content = create_test_image(800, 600, "JPEG")
        upload = create_upload_file(image_content, "photo.jpg", "image/jpeg")

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        assert result["mime_type"] == "image/jpeg"
        assert result["file_category"] == "image"

    @pytest.mark.asyncio
    async def test_upload_text_file(self, mock_s3_client, mock_settings):
        """Test plain text file upload."""
        mock_s3_client.head_bucket.return_value = {}

        text_content = b"Hello, this is a test text file."
        upload = create_upload_file(text_content, "notes.txt", "text/plain")

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        assert result["mime_type"] == "text/plain"
        assert result["file_category"] == "document"

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_type(self, mock_settings):
        """Test that unsupported file types are rejected."""
        content = b"video content"
        upload = create_upload_file(content, "video.mp4", "video/mp4")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(
                user_id=1,
                message_id=1,
                upload=upload,
            )

        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_rejects_empty_file(self, mock_settings):
        """Test that empty files are rejected."""
        upload = create_upload_file(b"", "empty.txt", "text/plain")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(
                user_id=1,
                message_id=1,
                upload=upload,
            )

        assert exc_info.value.status_code == 400
        assert "Empty file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_rejects_oversized_file(self, mock_settings):
        """Test that oversized files are rejected."""
        mock_settings.MESSAGE_ATTACHMENT_MAX_FILE_SIZE = 100  # 100 bytes

        large_content = b"x" * 200  # 200 bytes
        upload = create_upload_file(large_content, "large.txt", "text/plain")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(
                user_id=1,
                message_id=1,
                upload=upload,
            )

        assert exc_info.value.status_code == 400
        assert "File too large" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_rejects_oversized_image(self, mock_settings):
        """Test that oversized images are rejected."""
        mock_settings.MESSAGE_ATTACHMENT_MAX_FILE_SIZE = 10 * 1024 * 1024
        mock_settings.MESSAGE_ATTACHMENT_MAX_IMAGE_SIZE = 100  # 100 bytes

        # Create image larger than limit
        image_content = create_test_image(1000, 1000, "PNG")  # Will be > 100 bytes
        upload = create_upload_file(image_content, "large.png", "image/png")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(
                user_id=1,
                message_id=1,
                upload=upload,
            )

        assert exc_info.value.status_code == 400
        assert "Image too large" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_handles_s3_error(self, mock_s3_client, mock_settings):
        """Test that S3 upload errors are handled."""
        mock_s3_client.head_bucket.return_value = {}

        error_response = {"Error": {"Code": "InternalError", "Message": "S3 Error"}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, "PutObject")

        content = b"test content"
        upload = create_upload_file(content, "file.txt", "text/plain")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(
                user_id=1,
                message_id=1,
                upload=upload,
            )

        assert exc_info.value.status_code == 500
        assert "Failed to store file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_handles_missing_filename(self, mock_s3_client, mock_settings):
        """Test upload handles None filename."""
        mock_s3_client.head_bucket.return_value = {}

        content = b"test content"
        upload = create_upload_file(content, None, "text/plain")

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        # Should use default "file" name
        assert "file_key" in result

    @pytest.mark.asyncio
    async def test_upload_word_document(self, mock_s3_client, mock_settings):
        """Test Word document upload."""
        mock_s3_client.head_bucket.return_value = {}

        content = b"PK\x03\x04 docx content"  # DOCX magic bytes
        upload = create_upload_file(
            content,
            "document.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        assert result["file_category"] == "document"


# =============================================================================
# Test Presigned URL Generation
# =============================================================================


class TestGeneratePresignedUrl:
    """Tests for presigned URL generation."""

    def test_generate_presigned_url_success(self, mock_s3_client, mock_settings):
        """Test successful presigned URL generation."""
        expected_url = "https://minio:9000/bucket/key?signature=xxx"
        mock_s3_client.generate_presigned_url.return_value = expected_url

        url = generate_presigned_url("messages/1/100/abc123.pdf")

        assert url == expected_url
        mock_s3_client.generate_presigned_url.assert_called_once()

    def test_generate_presigned_url_with_custom_expiry(self, mock_s3_client, mock_settings):
        """Test presigned URL with custom expiry."""
        mock_s3_client.generate_presigned_url.return_value = "https://example.com/file"

        generate_presigned_url("file_key", expiry_seconds=7200)

        call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
        assert call_kwargs["ExpiresIn"] == 7200

    def test_generate_presigned_url_uses_default_expiry(self, mock_s3_client, mock_settings):
        """Test presigned URL uses default expiry."""
        mock_s3_client.generate_presigned_url.return_value = "https://example.com/file"

        generate_presigned_url("file_key")

        call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
        assert call_kwargs["ExpiresIn"] == PRESIGNED_URL_EXPIRY

    def test_generate_presigned_url_error(self, mock_s3_client, mock_settings):
        """Test presigned URL generation error handling."""
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            error_response, "GeneratePresignedUrl"
        )

        with pytest.raises(HTTPException) as exc_info:
            generate_presigned_url("nonexistent_key")

        assert exc_info.value.status_code == 500
        assert "Failed to generate file access URL" in str(exc_info.value.detail)


# =============================================================================
# Test File Deletion
# =============================================================================


class TestDeleteMessageAttachment:
    """Tests for deleting message attachments."""

    def test_delete_attachment_success(self, mock_s3_client, mock_settings):
        """Test successful attachment deletion."""
        mock_s3_client.delete_object.return_value = {}

        delete_message_attachment("messages/1/100/abc123.pdf")

        mock_s3_client.delete_object.assert_called_once()

    def test_delete_attachment_handles_error(self, mock_s3_client, mock_settings):
        """Test deletion handles error gracefully."""
        error_response = {"Error": {"Code": "InternalError"}}
        mock_s3_client.delete_object.side_effect = ClientError(
            error_response, "DeleteObject"
        )

        # Should not raise, just log warning
        delete_message_attachment("messages/1/100/abc123.pdf")

    def test_delete_empty_key_does_nothing(self, mock_s3_client, mock_settings):
        """Test deleting empty key does nothing."""
        delete_message_attachment("")

        mock_s3_client.delete_object.assert_not_called()

    def test_delete_none_key_does_nothing(self, mock_s3_client, mock_settings):
        """Test deleting None key does nothing."""
        delete_message_attachment(None)

        mock_s3_client.delete_object.assert_not_called()


# =============================================================================
# Test File Existence Check
# =============================================================================


class TestCheckFileExists:
    """Tests for checking file existence."""

    def test_file_exists_returns_true(self, mock_s3_client, mock_settings):
        """Test returns True when file exists."""
        mock_s3_client.head_object.return_value = {"ContentLength": 1000}

        result = check_file_exists("messages/1/100/abc123.pdf")

        assert result is True

    def test_file_not_exists_returns_false(self, mock_s3_client, mock_settings):
        """Test returns False when file doesn't exist."""
        error_response = {"Error": {"Code": "404"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        result = check_file_exists("nonexistent_key")

        assert result is False

    def test_file_check_error_returns_false(self, mock_s3_client, mock_settings):
        """Test returns False on any error."""
        error_response = {"Error": {"Code": "403"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        result = check_file_exists("forbidden_key")

        assert result is False


# =============================================================================
# Test S3 Client Initialization
# =============================================================================


class TestS3ClientInitialization:
    """Tests for S3 client lazy initialization."""

    def test_client_is_cached(self, mock_settings):
        """Test that S3 client is cached via lru_cache."""
        # Clear the cache first
        _s3_client.cache_clear()

        with patch("core.message_storage.boto3.session.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            client1 = _s3_client()
            client2 = _s3_client()

            # Should only create session once
            assert mock_session.call_count == 1
            assert client1 is client2

    def test_client_uses_correct_config(self, mock_settings):
        """Test that S3 client is created with correct configuration."""
        _s3_client.cache_clear()

        with patch("core.message_storage.boto3.session.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            _s3_client()

            call_kwargs = mock_session.return_value.client.call_args[1]
            assert call_kwargs["endpoint_url"] == "http://minio:9000"
            assert call_kwargs["aws_access_key_id"] == "minioadmin"
            assert call_kwargs["aws_secret_access_key"] == "minioadmin123"


# =============================================================================
# Test Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_categorize_file_with_uppercase_mime(self):
        """Test categorization handles case sensitivity."""
        # MIME types should be lowercase, but test defensive coding
        assert _categorize_file("IMAGE/PNG") == "other"
        assert _categorize_file("image/png") == "image"

    def test_extract_dimensions_from_small_image(self):
        """Test extracting dimensions from minimal image."""
        image_bytes = create_test_image(1, 1, "PNG")
        width, height = _extract_image_dimensions(image_bytes)

        assert width == 1
        assert height == 1

    def test_extract_dimensions_from_large_image(self):
        """Test extracting dimensions from large image."""
        image_bytes = create_test_image(4000, 3000, "PNG")
        width, height = _extract_image_dimensions(image_bytes)

        assert width == 4000
        assert height == 3000

    @pytest.mark.asyncio
    async def test_upload_gif_image(self, mock_s3_client, mock_settings):
        """Test GIF image upload."""
        mock_s3_client.head_bucket.return_value = {}

        image_content = create_test_image(100, 100, "GIF")
        upload = create_upload_file(image_content, "animation.gif", "image/gif")

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        assert result["mime_type"] == "image/gif"
        assert result["file_category"] == "image"

    @pytest.mark.asyncio
    async def test_upload_webp_image(self, mock_s3_client, mock_settings):
        """Test WebP image upload."""
        mock_s3_client.head_bucket.return_value = {}

        image_content = create_test_image(100, 100, "WebP")
        upload = create_upload_file(image_content, "image.webp", "image/webp")

        result = await store_message_attachment(
            user_id=1,
            message_id=1,
            upload=upload,
        )

        assert result["mime_type"] == "image/webp"
        assert result["file_category"] == "image"

    def test_generate_secure_key_with_path_traversal_attempt(self):
        """Test that path traversal attempts are sanitized."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "file\x00.txt",
            "./hidden/.file",
        ]

        for filename in dangerous_filenames:
            key = _generate_secure_key(1, 1, filename)
            assert ".." not in key
            assert "\x00" not in key
            assert key.startswith("messages/1/1/")

    def test_key_generation_preserves_valid_extensions(self):
        """Test that valid extensions are preserved."""
        valid_files = [
            ("document.pdf", "pdf"),
            ("image.jpg", "jpg"),
            ("file.docx", "docx"),
            ("notes.txt", "txt"),
        ]

        for filename, expected_ext in valid_files:
            key = _generate_secure_key(1, 1, filename)
            assert key.endswith(f".{expected_ext}")


# =============================================================================
# Test MIME Type Validation
# =============================================================================


class TestMimeTypeValidation:
    """Tests for MIME type validation."""

    @pytest.mark.asyncio
    async def test_rejects_executable(self, mock_settings):
        """Test that executable files are rejected."""
        upload = create_upload_file(b"MZ...", "program.exe", "application/x-msdownload")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_script(self, mock_settings):
        """Test that script files are rejected."""
        upload = create_upload_file(b"<script>", "script.js", "application/javascript")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_html(self, mock_settings):
        """Test that HTML files are rejected."""
        upload = create_upload_file(b"<html>", "page.html", "text/html")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_zip(self, mock_settings):
        """Test that archive files are rejected."""
        upload = create_upload_file(b"PK...", "archive.zip", "application/zip")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400
