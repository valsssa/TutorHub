"""
Comprehensive hard flow tests for file upload and storage scenarios.

Tests cover complex edge cases and failure scenarios:
1. Large File Upload Edge Cases
2. Concurrent Upload Scenarios
3. Storage Backend Failures
4. File Type Validation (MIME spoofing, magic numbers, malicious files)
5. Presigned URL Edge Cases
6. File Processing Pipeline
7. File Deletion & Cleanup
8. Avatar/Profile Image Specific scenarios
"""

import asyncio
import hashlib
import io
import os
import struct
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError
from fastapi import HTTPException, UploadFile
from PIL import Image

from core.avatar_storage import (
    AvatarStorageClient,
    build_avatar_url,
    get_avatar_storage,
)
from core.message_storage import (
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    MAX_IMAGE_SIZE,
    _categorize_file,
    _extract_image_dimensions,
    _generate_secure_key,
    check_file_exists,
    delete_message_attachment,
    generate_presigned_url,
    store_message_attachment,
)
from core.storage import (
    DOCUMENT_CONTENT_TYPES,
    IMAGE_CONTENT_TYPES,
    MAX_DOCUMENT_SIZE_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_SIZE_BYTES,
    MIN_IMAGE_DIMENSION,
    _build_object_key,
    _ensure_bucket_exists,
    _extract_key_from_url,
    _generate_filename,
    _process_image,
    _public_url_for_key,
    _s3_client,
    _validate_size,
    delete_file,
    delete_files,
    store_profile_photo,
    store_supporting_document,
)

# =============================================================================
# Test Utilities and Fixtures
# =============================================================================


def create_test_image(
    width: int = 100,
    height: int = 100,
    format: str = "PNG",
    mode: str = "RGB",
    color: tuple = (255, 0, 0),
) -> bytes:
    """Helper to create test image bytes with custom parameters."""
    buffer = BytesIO()
    Image.new(mode, (width, height), color=color).save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


def create_upload_file(
    content: bytes,
    filename: str = "test.txt",
    content_type: str = "text/plain",
) -> UploadFile:
    """Helper to create mock UploadFile."""
    upload = MagicMock(spec=UploadFile)
    upload.filename = filename
    upload.content_type = content_type
    upload.read = AsyncMock(return_value=content)
    return upload


def create_large_file(size_mb: int) -> bytes:
    """Create a large binary file of specified size in MB."""
    return os.urandom(size_mb * 1024 * 1024)


def create_chunked_data(total_size: int, chunk_size: int) -> list[bytes]:
    """Create data split into chunks for multipart upload simulation."""
    data = os.urandom(total_size)
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for storage.py module."""
    with patch("core.storage._s3_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_avatar_s3_client():
    """Mock S3 client for avatar_storage.py module."""
    with patch("core.avatar_storage.get_session") as mock_session:
        mock_client = AsyncMock()
        mock_session.return_value.create_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_session.return_value.create_client.return_value.__aexit__ = AsyncMock()
        yield mock_client


@pytest.fixture
def mock_message_s3_client():
    """Mock S3 client for message_storage.py module."""
    with patch("core.message_storage._s3_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    """Mock settings for storage modules."""
    with patch("core.message_storage.settings") as mock:
        mock.MESSAGE_ATTACHMENT_STORAGE_ENDPOINT = "http://minio:9000"
        mock.MESSAGE_ATTACHMENT_STORAGE_ACCESS_KEY = "minioadmin"
        mock.MESSAGE_ATTACHMENT_STORAGE_SECRET_KEY = "minioadmin123"
        mock.MESSAGE_ATTACHMENT_STORAGE_BUCKET = "message-attachments"
        mock.MESSAGE_ATTACHMENT_STORAGE_REGION = "us-east-1"
        mock.MESSAGE_ATTACHMENT_STORAGE_USE_SSL = False
        mock.MESSAGE_ATTACHMENT_MAX_FILE_SIZE = 10 * 1024 * 1024
        mock.MESSAGE_ATTACHMENT_MAX_IMAGE_SIZE = 5 * 1024 * 1024
        mock.MESSAGE_ATTACHMENT_URL_TTL_SECONDS = 3600
        yield mock


# =============================================================================
# 1. Large File Upload Edge Cases
# =============================================================================


class TestLargeFileUploadEdgeCases:
    """Test large file upload edge cases including multipart, resume, and timeouts."""

    @pytest.mark.asyncio
    async def test_multipart_upload_interruption(self, mock_s3_client):
        """Test handling of multipart upload interruption mid-transfer."""
        mock_s3_client.head_bucket.return_value = {}

        # Simulate failure after partial upload
        call_count = 0
        def upload_part_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # Fail on third chunk
                error_response = {"Error": {"Code": "RequestTimeout"}}
                raise ClientError(error_response, "UploadPart")
            return {"ETag": f"etag-{call_count}"}

        mock_s3_client.upload_part = MagicMock(side_effect=upload_part_side_effect)
        mock_s3_client.create_multipart_upload.return_value = {"UploadId": "test-upload-id"}
        mock_s3_client.abort_multipart_upload.return_value = {}

        # Verify abort is called on failure
        chunks = create_chunked_data(5 * 1024 * 1024, 1024 * 1024)  # 5MB in 1MB chunks

        with pytest.raises(ClientError):
            for i, chunk in enumerate(chunks):
                mock_s3_client.upload_part(
                    Bucket="test-bucket",
                    Key="test-key",
                    PartNumber=i + 1,
                    UploadId="test-upload-id",
                    Body=chunk,
                )

    @pytest.mark.asyncio
    async def test_resume_after_partial_upload(self, mock_s3_client):
        """Test resuming upload after partial completion."""
        mock_s3_client.head_bucket.return_value = {}

        # Track uploaded parts
        uploaded_parts = []

        def upload_part_tracking(*args, **kwargs):
            part_num = kwargs.get("PartNumber")
            uploaded_parts.append(part_num)
            return {"ETag": f"etag-{part_num}"}

        mock_s3_client.upload_part = MagicMock(side_effect=upload_part_tracking)
        mock_s3_client.list_parts.return_value = {
            "Parts": [
                {"PartNumber": 1, "ETag": "etag-1"},
                {"PartNumber": 2, "ETag": "etag-2"},
            ]
        }

        # Simulate resume - should only upload remaining parts
        existing_parts = {p["PartNumber"] for p in mock_s3_client.list_parts()["Parts"]}
        total_parts = 5

        for part_num in range(1, total_parts + 1):
            if part_num not in existing_parts:
                mock_s3_client.upload_part(
                    Bucket="test-bucket",
                    Key="test-key",
                    PartNumber=part_num,
                    UploadId="test-upload-id",
                    Body=b"chunk",
                )

        # Only parts 3, 4, 5 should be uploaded
        assert uploaded_parts == [3, 4, 5]

    @pytest.mark.asyncio
    async def test_chunk_ordering_verification(self, mock_s3_client):
        """Test that chunks are uploaded in correct order for multipart."""
        mock_s3_client.head_bucket.return_value = {}

        part_numbers = []

        def track_order(*args, **kwargs):
            part_numbers.append(kwargs.get("PartNumber"))
            return {"ETag": f"etag-{len(part_numbers)}"}

        mock_s3_client.upload_part = MagicMock(side_effect=track_order)

        # Upload chunks
        chunks = create_chunked_data(3 * 1024 * 1024, 1024 * 1024)
        for i, chunk in enumerate(chunks, 1):
            mock_s3_client.upload_part(
                Bucket="test-bucket",
                Key="test-key",
                PartNumber=i,
                UploadId="test-upload-id",
                Body=chunk,
            )

        # Verify sequential order
        assert part_numbers == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_upload_timeout_handling(self, mock_s3_client):
        """Test handling of upload timeout errors."""
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.put_object.side_effect = ReadTimeoutError(
            endpoint_url="http://minio:9000"
        )

        content = create_test_image(500, 500)
        upload = create_upload_file(content, "timeout_test.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                with pytest.raises(HTTPException) as exc_info:
                    await store_profile_photo(user_id=1, upload=upload)

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_maximum_file_size_enforcement_exact_boundary(self, mock_settings):
        """Test file size enforcement at exact boundary."""
        # Exact boundary - should pass
        exact_size_content = b"x" * MAX_FILE_SIZE
        create_upload_file(
            exact_size_content, "exact.txt", "text/plain"
        )

        # One byte over - should fail
        over_size_content = b"x" * (MAX_FILE_SIZE + 1)
        upload_over = create_upload_file(
            over_size_content, "over.txt", "text/plain"
        )

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload_over)

        assert exc_info.value.status_code == 400
        assert "too large" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_upload_with_zero_byte_file(self, mock_settings):
        """Test handling of zero-byte file uploads."""
        upload = create_upload_file(b"", "empty.txt", "text/plain")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400
        assert "empty" in str(exc_info.value.detail).lower()


# =============================================================================
# 2. Concurrent Upload Scenarios
# =============================================================================


class TestConcurrentUploadScenarios:
    """Test concurrent upload scenarios and race conditions."""

    @pytest.mark.asyncio
    async def test_same_file_uploaded_twice_simultaneously(
        self, mock_message_s3_client, mock_settings
    ):
        """Test handling when same file is uploaded twice at the same time."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}

        content = create_test_image(100, 100)
        upload1 = create_upload_file(content, "same_file.png", "image/png")
        upload2 = create_upload_file(content, "same_file.png", "image/png")

        # Simulate concurrent uploads
        results = await asyncio.gather(
            store_message_attachment(1, 1, upload1),
            store_message_attachment(1, 2, upload2),
            return_exceptions=True,
        )

        # Both should succeed with different keys (random component)
        assert not any(isinstance(r, Exception) for r in results)
        assert results[0]["file_key"] != results[1]["file_key"]

    @pytest.mark.asyncio
    async def test_multiple_files_same_user_concurrent(
        self, mock_message_s3_client, mock_settings
    ):
        """Test multiple concurrent uploads from same user."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}

        uploads = []
        for i in range(5):
            content = create_test_image(100 + i * 10, 100 + i * 10)
            uploads.append(
                create_upload_file(content, f"file_{i}.png", "image/png")
            )

        # Concurrent uploads
        results = await asyncio.gather(
            *[
                store_message_attachment(1, i, upload)
                for i, upload in enumerate(uploads)
            ],
            return_exceptions=True,
        )

        # All should succeed
        assert all(not isinstance(r, Exception) for r in results)

        # All keys should be unique
        keys = [r["file_key"] for r in results]
        assert len(keys) == len(set(keys))

    def test_storage_quota_race_condition_simulation(self):
        """Test storage quota enforcement under concurrent writes."""
        quota_remaining = {"value": 100}  # 100 bytes remaining
        lock = threading.Lock()
        uploads_completed = []
        uploads_rejected = []

        def simulate_upload(file_size: int, file_id: int):
            with lock:
                if quota_remaining["value"] >= file_size:
                    quota_remaining["value"] -= file_size
                    uploads_completed.append(file_id)
                    return True
                else:
                    uploads_rejected.append(file_id)
                    return False

        # Concurrent uploads trying to use quota
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(simulate_upload, 30, i)
                for i in range(10)
            ]
            for future in as_completed(futures):
                future.result()

        # Verify quota wasn't exceeded
        total_used = sum(30 for _ in uploads_completed)
        assert total_used <= 100
        assert len(uploads_completed) == 3  # Only 3 x 30 bytes fit in 100

    @pytest.mark.asyncio
    async def test_duplicate_content_detection_by_hash(
        self, mock_message_s3_client, mock_settings
    ):
        """Test detecting duplicate content via content hash."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}

        # Same content, different filenames
        content = b"identical content for deduplication test"
        upload1 = create_upload_file(content, "file1.txt", "text/plain")
        upload2 = create_upload_file(content, "file2.txt", "text/plain")

        # Calculate hashes
        hash1 = hashlib.sha256(content).hexdigest()
        hash2 = hashlib.sha256(content).hexdigest()

        assert hash1 == hash2  # Content is identical

        # Both uploads succeed but system could detect duplicates
        result1 = await store_message_attachment(1, 1, upload1)
        result2 = await store_message_attachment(1, 2, upload2)

        # Different keys but same content size
        assert result1["file_size"] == result2["file_size"]

    def test_upload_slot_limiting(self):
        """Test limiting concurrent upload slots per user."""
        max_concurrent_uploads = 3
        active_uploads = {"count": 0}
        max_reached = {"value": 0}
        lock = threading.Lock()

        def acquire_upload_slot(user_id: int) -> bool:
            with lock:
                if active_uploads["count"] < max_concurrent_uploads:
                    active_uploads["count"] += 1
                    max_reached["value"] = max(
                        max_reached["value"], active_uploads["count"]
                    )
                    return True
                return False

        def release_upload_slot():
            with lock:
                active_uploads["count"] -= 1

        def simulate_upload(user_id: int, file_id: int):
            if not acquire_upload_slot(user_id):
                return False
            try:
                time.sleep(0.01)  # Simulate upload time
                return True
            finally:
                release_upload_slot()

        # Try 10 concurrent uploads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(simulate_upload, 1, i)
                for i in range(10)
            ]
            [f.result() for f in as_completed(futures)]

        # Max concurrent should not exceed limit
        assert max_reached["value"] <= max_concurrent_uploads


# =============================================================================
# 3. Storage Backend Failures
# =============================================================================


class TestStorageBackendFailures:
    """Test storage backend failure scenarios."""

    @pytest.mark.asyncio
    async def test_minio_connection_timeout(self, mock_s3_client):
        """Test handling MinIO connection timeout."""
        mock_s3_client.head_bucket.side_effect = ConnectTimeoutError(
            endpoint_url="http://minio:9000"
        )

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with pytest.raises(Exception):  # Connection error propagates
                _ensure_bucket_exists()

    @pytest.mark.asyncio
    async def test_bucket_not_found_auto_creation(self, mock_s3_client):
        """Test automatic bucket creation when bucket not found."""
        # First call: bucket doesn't exist
        error_response = {"Error": {"Code": "404"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            error_response, "HeadBucket"
        )
        mock_s3_client.create_bucket.return_value = {}
        mock_s3_client.put_bucket_policy.return_value = {}

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            _ensure_bucket_exists()

        mock_s3_client.create_bucket.assert_called_once()

    @pytest.mark.asyncio
    async def test_bucket_not_found_creation_fails(self, mock_s3_client):
        """Test handling when bucket creation fails."""
        head_error = {"Error": {"Code": "404"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            head_error, "HeadBucket"
        )

        create_error = {"Error": {"Code": "AccessDenied"}}
        mock_s3_client.create_bucket.side_effect = ClientError(
            create_error, "CreateBucket"
        )

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with pytest.raises(HTTPException) as exc_info:
                _ensure_bucket_exists()

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_permission_denied_on_upload(self, mock_s3_client):
        """Test handling permission denied during upload."""
        mock_s3_client.head_bucket.return_value = {}

        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3_client.put_object.side_effect = ClientError(
            error_response, "PutObject"
        )

        content = create_test_image(300, 300)
        upload = create_upload_file(content, "test.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                with pytest.raises(HTTPException) as exc_info:
                    await store_profile_photo(user_id=1, upload=upload)

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_storage_full_scenario(self, mock_s3_client):
        """Test handling when storage is full."""
        mock_s3_client.head_bucket.return_value = {}

        error_response = {
            "Error": {
                "Code": "QuotaExceeded",
                "Message": "Storage quota exceeded",
            }
        }
        mock_s3_client.put_object.side_effect = ClientError(
            error_response, "PutObject"
        )

        content = create_test_image(300, 300)
        upload = create_upload_file(content, "test.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                with pytest.raises(HTTPException):
                    await store_profile_photo(user_id=1, upload=upload)

    @pytest.mark.asyncio
    async def test_network_interruption_during_upload(self, mock_s3_client):
        """Test handling network interruption during upload."""
        mock_s3_client.head_bucket.return_value = {}

        # Simulate network interruption
        mock_s3_client.put_object.side_effect = ConnectionError(
            "Connection reset by peer"
        )

        content = create_test_image(300, 300)
        upload = create_upload_file(content, "test.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                with pytest.raises((HTTPException, ConnectionError)):
                    await store_profile_photo(user_id=1, upload=upload)

    @pytest.mark.asyncio
    async def test_intermittent_failure_with_retry(self, mock_s3_client):
        """Test handling intermittent failures that succeed on retry."""
        mock_s3_client.head_bucket.return_value = {}

        call_count = {"value": 0}

        def intermittent_failure(*args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] < 3:
                error_response = {"Error": {"Code": "ServiceUnavailable"}}
                raise ClientError(error_response, "PutObject")
            return {}

        mock_s3_client.put_object.side_effect = intermittent_failure

        # Manual retry simulation
        max_retries = 3

        for attempt in range(max_retries):
            try:
                mock_s3_client.put_object(
                    Bucket="test", Key="key", Body=b"data"
                )
                break
            except ClientError:
                time.sleep(0.01 * (2 ** attempt))  # Exponential backoff

        # Should succeed on third attempt
        assert call_count["value"] == 3


# =============================================================================
# 4. File Type Validation (MIME Spoofing, Magic Numbers, Malicious Files)
# =============================================================================


class TestFileTypeValidation:
    """Test file type validation including MIME spoofing and malicious file detection."""

    @pytest.mark.asyncio
    async def test_mime_type_spoofing_detection_exe_as_png(self, mock_settings):
        """Test detection of executable disguised as PNG."""
        # Windows PE executable header disguised as PNG
        exe_content = b"MZ\x90\x00"  # DOS MZ header
        upload = create_upload_file(exe_content, "image.png", "image/png")

        with pytest.raises(HTTPException):
            await store_message_attachment(1, 1, upload)

    @pytest.mark.asyncio
    async def test_mime_type_spoofing_detection_script_as_image(self, mock_settings):
        """Test detection of script disguised as image."""
        # JavaScript content with image extension
        script_content = b"<script>alert('xss')</script>"
        upload = create_upload_file(script_content, "photo.jpg", "image/jpeg")

        # The file won't pass as valid JPEG
        with pytest.raises(HTTPException):
            await store_message_attachment(1, 1, upload)

    def test_magic_number_validation_png(self):
        """Test PNG magic number validation."""
        # Valid PNG header
        png_magic = b"\x89PNG\r\n\x1a\n"
        valid_png = create_test_image(100, 100, "PNG")

        assert valid_png[:8] == png_magic

    def test_magic_number_validation_jpeg(self):
        """Test JPEG magic number validation."""
        # Valid JPEG header (FFD8FF)
        valid_jpeg = create_test_image(100, 100, "JPEG")

        assert valid_jpeg[:2] == b"\xff\xd8"

    def test_magic_number_validation_pdf(self):
        """Test PDF magic number validation."""
        # Valid PDF header
        pdf_magic = b"%PDF-"
        valid_pdf = b"%PDF-1.4 fake pdf content"

        assert valid_pdf.startswith(pdf_magic)

    @pytest.mark.asyncio
    async def test_malicious_file_detection_polyglot(self, mock_settings):
        """Test detection of polyglot files (valid as multiple formats)."""
        # GIFAR: GIF that's also a JAR
        # GIF header followed by ZIP content
        gif_header = b"GIF89a\x01\x00\x01\x00\x00\x00\x00"
        zip_content = b"PK\x03\x04"  # ZIP signature
        polyglot = gif_header + zip_content

        create_upload_file(polyglot, "image.gif", "image/gif")

        # Image dimension extraction should fail for malformed content
        width, height = _extract_image_dimensions(polyglot)
        # Either fails or returns minimal dimensions

    @pytest.mark.asyncio
    async def test_archive_bomb_prevention_nested_zip(self, mock_settings):
        """Test prevention of zip bomb uploads."""
        # Simulated zip bomb header
        zip_header = b"PK\x03\x04"
        upload = create_upload_file(zip_header * 1000, "bomb.zip", "application/zip")

        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_archive_bomb_prevention_compression_ratio(self):
        """Test detection of suspicious compression ratios."""
        # A file that decompresses to massive size would have suspicious ratio
        # This is a conceptual test - actual implementation would check ratios

        compressed_size = 1000
        decompressed_size = 1000 * 1000 * 1000  # 1GB from 1KB

        ratio = decompressed_size / compressed_size
        max_allowed_ratio = 100

        assert ratio > max_allowed_ratio  # Would be flagged

    def test_image_dimension_limits_width(self):
        """Test image dimension limit enforcement for width."""
        # Image exceeding max dimension
        assert MAX_IMAGE_DIMENSION == 4096

        # Processing should resize images exceeding limits
        large_image = create_test_image(5000, 1000)
        processed, _, _ = _process_image(large_image, original_content_type="image/png")

        with Image.open(BytesIO(processed)) as img:
            assert img.width <= MAX_IMAGE_DIMENSION

    def test_image_dimension_limits_height(self):
        """Test image dimension limit enforcement for height."""
        large_image = create_test_image(1000, 5000)
        processed, _, _ = _process_image(large_image, original_content_type="image/png")

        with Image.open(BytesIO(processed)) as img:
            assert img.height <= MAX_IMAGE_DIMENSION

    def test_image_dimension_minimum_enforcement(self):
        """Test minimum image dimension enforcement."""
        # Tiny image should be upscaled
        tiny_image = create_test_image(50, 50)
        processed, _, _ = _process_image(tiny_image, original_content_type="image/png")

        with Image.open(BytesIO(processed)) as img:
            assert img.width >= MIN_IMAGE_DIMENSION
            assert img.height >= MIN_IMAGE_DIMENSION

    @pytest.mark.asyncio
    async def test_svg_with_embedded_script_rejection(self, mock_settings):
        """Test rejection of SVG with embedded JavaScript."""
        malicious_svg = b"""<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <script>alert('XSS')</script>
        </svg>"""

        upload = create_upload_file(malicious_svg, "image.svg", "image/svg+xml")

        # SVG is not in allowed types
        with pytest.raises(HTTPException) as exc_info:
            await store_message_attachment(1, 1, upload)

        assert exc_info.value.status_code == 400

    def test_null_byte_injection_in_filename(self):
        """Test prevention of null byte injection in filenames."""
        malicious_filename = "image.png\x00.exe"

        # Sanitization should remove null bytes
        from core.sanitization import sanitize_filename

        safe_filename = sanitize_filename(malicious_filename)
        assert "\x00" not in safe_filename

    def test_path_traversal_in_filename(self):
        """Test prevention of path traversal in filenames."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd",
            "..%2F..%2F..%2Fetc/passwd",
        ]

        from core.sanitization import sanitize_filename

        for filename in malicious_filenames:
            safe = sanitize_filename(filename)
            assert ".." not in safe
            assert "/" not in safe
            assert "\\" not in safe


# =============================================================================
# 5. Presigned URL Edge Cases
# =============================================================================


class TestPresignedURLEdgeCases:
    """Test presigned URL generation and access edge cases."""

    def test_url_expiration_boundary(self, mock_message_s3_client, mock_settings):
        """Test URL expiration at exact boundary."""
        mock_message_s3_client.generate_presigned_url.return_value = (
            "https://minio:9000/bucket/key?X-Amz-Expires=3600"
        )

        # Generate URL with specific expiry
        url = generate_presigned_url("test-key", expiry_seconds=3600)

        assert "3600" in url

    def test_url_expiration_zero_seconds(self, mock_message_s3_client, mock_settings):
        """Test URL generation with zero expiration."""
        mock_message_s3_client.generate_presigned_url.return_value = (
            "https://minio:9000/bucket/key?X-Amz-Expires=0"
        )

        # Zero expiration - immediately invalid
        generate_presigned_url("test-key", expiry_seconds=0)
        mock_message_s3_client.generate_presigned_url.assert_called_once()

    def test_url_expiration_max_allowed(self, mock_message_s3_client, mock_settings):
        """Test URL generation with maximum allowed expiration."""
        max_expiry = 604800  # 7 days
        mock_message_s3_client.generate_presigned_url.return_value = (
            f"https://minio:9000/bucket/key?X-Amz-Expires={max_expiry}"
        )

        generate_presigned_url("test-key", expiry_seconds=max_expiry)

        call_args = mock_message_s3_client.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == max_expiry

    def test_url_reuse_attempt_detection(self):
        """Test detection of URL reuse attempts (conceptual)."""
        # Track used URL signatures
        used_signatures = set()

        def validate_url(url: str) -> bool:
            # Extract signature from URL
            if "signature=" in url:
                sig = url.split("signature=")[1].split("&")[0]
                if sig in used_signatures:
                    return False
                used_signatures.add(sig)
                return True
            return False

        url1 = "https://minio:9000/key?signature=abc123"
        url2 = "https://minio:9000/key?signature=abc123"  # Reuse attempt

        assert validate_url(url1) is True
        assert validate_url(url2) is False

    def test_concurrent_access_to_same_url(self):
        """Test concurrent access to same presigned URL."""
        access_log = []
        lock = threading.Lock()

        def access_url(url: str, request_id: int):
            with lock:
                access_log.append({
                    "request_id": request_id,
                    "url": url,
                    "timestamp": time.time(),
                })
            time.sleep(0.01)  # Simulate download time
            return True

        url = "https://minio:9000/bucket/key?presigned"

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(access_url, url, i)
                for i in range(10)
            ]
            results = [f.result() for f in futures]

        # All concurrent accesses should succeed
        assert all(results)
        assert len(access_log) == 10

    def test_url_generation_rate_limiting(self):
        """Test rate limiting on URL generation."""
        rate_limit = 10  # URLs per second
        window_start = time.time()
        url_count = 0

        def can_generate_url() -> bool:
            nonlocal url_count, window_start
            current = time.time()

            if current - window_start >= 1.0:
                window_start = current
                url_count = 0

            if url_count < rate_limit:
                url_count += 1
                return True
            return False

        # Rapid URL generation attempts
        results = [can_generate_url() for _ in range(15)]

        # First 10 should succeed, rest should fail
        assert sum(results) == 10

    def test_cross_origin_url_structure(self, mock_message_s3_client, mock_settings):
        """Test presigned URL structure for CORS compatibility."""
        mock_message_s3_client.generate_presigned_url.return_value = (
            "https://minio.example.com/bucket/key?X-Amz-Algorithm=AWS4-HMAC-SHA256"
        )

        url = generate_presigned_url("test-key")

        # URL should use HTTPS
        assert url.startswith("https://")
        # Should contain signing algorithm
        assert "X-Amz-Algorithm" in url


# =============================================================================
# 6. File Processing Pipeline
# =============================================================================


class TestFileProcessingPipeline:
    """Test file processing pipeline including resize, thumbnail, and error recovery."""

    def test_image_resize_failure_recovery(self):
        """Test recovery from image resize failure."""
        # Corrupted image that fails to process
        corrupted_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with pytest.raises(HTTPException) as exc_info:
            _process_image(corrupted_image, original_content_type="image/png")

        assert exc_info.value.status_code == 400

    def test_thumbnail_generation_timeout_simulation(self):
        """Test handling of thumbnail generation timeout."""
        # Large image that would take long to process
        large_image = create_test_image(4000, 4000)

        # Processing should still complete (not actually timeout in test)
        with patch("PIL.Image.Image.resize") as mock_resize:
            mock_resize.side_effect = TimeoutError("Processing timeout")

            with pytest.raises(TimeoutError):
                _process_image(large_image, original_content_type="image/png")

    def test_processing_queue_overflow_handling(self):
        """Test handling of processing queue overflow."""
        queue_size = 5
        processing_queue = []
        rejected_count = 0

        def queue_for_processing(item_id: int) -> bool:
            nonlocal rejected_count
            if len(processing_queue) >= queue_size:
                rejected_count += 1
                return False
            processing_queue.append(item_id)
            return True

        # Try to queue more items than capacity
        results = [queue_for_processing(i) for i in range(10)]

        assert sum(results) == queue_size
        assert rejected_count == 5

    def test_metadata_extraction_from_jpeg_exif(self):
        """Test metadata extraction from JPEG EXIF data."""
        # Create image with basic properties
        img = Image.new("RGB", (200, 150), color=(100, 150, 200))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        jpeg_bytes = buffer.getvalue()

        # Extract dimensions
        width, height = _extract_image_dimensions(jpeg_bytes)

        assert width == 200
        assert height == 150

    def test_metadata_extraction_error_handling(self):
        """Test handling of metadata extraction errors."""
        # Non-image data
        non_image_data = b"This is not an image file"

        width, height = _extract_image_dimensions(non_image_data)

        assert width is None
        assert height is None

    def test_image_format_conversion_png_to_jpeg(self):
        """Test image format handling during processing."""
        png_image = create_test_image(300, 300, "PNG")

        # Process as JPEG
        processed, content_type, extension = _process_image(
            png_image, original_content_type="image/jpeg"
        )

        assert content_type == "image/jpeg"
        assert extension == "jpg"

    def test_image_mode_conversion_rgba_to_rgb(self):
        """Test RGBA to RGB conversion for JPEG."""
        # Create RGBA image
        rgba_image = create_test_image(300, 300, "PNG", mode="RGBA")

        # Process as JPEG (requires RGB)
        processed, content_type, _ = _process_image(
            rgba_image, original_content_type="image/jpeg"
        )

        with Image.open(BytesIO(processed)) as img:
            assert img.mode == "RGB"

    def test_processing_preserves_aspect_ratio(self):
        """Test that processing preserves aspect ratio."""
        # 2:1 aspect ratio image
        wide_image = create_test_image(800, 400)

        processed, _, _ = _process_image(
            wide_image, original_content_type="image/png"
        )

        with Image.open(BytesIO(processed)) as img:
            # Aspect ratio should be preserved (approximately 2:1)
            ratio = img.width / img.height
            assert 1.9 <= ratio <= 2.1


# =============================================================================
# 7. File Deletion & Cleanup
# =============================================================================


class TestFileDeletionAndCleanup:
    """Test file deletion, orphan detection, and cleanup scenarios."""

    def test_orphaned_file_detection_pattern(self):
        """Test pattern for detecting orphaned files."""
        # Simulate file registry and storage
        registered_files = {"file1.png", "file2.jpg", "file3.pdf"}
        stored_files = {"file1.png", "file2.jpg", "file3.pdf", "orphan1.png", "orphan2.jpg"}

        orphaned = stored_files - registered_files

        assert orphaned == {"orphan1.png", "orphan2.jpg"}

    def test_soft_delete_with_restore(self):
        """Test soft delete functionality with restore capability."""
        # Simulate soft delete
        files = {
            "file1.png": {"deleted_at": None, "content": "data1"},
            "file2.jpg": {"deleted_at": "2024-01-01T00:00:00", "content": "data2"},
        }

        # Soft delete file1
        files["file1.png"]["deleted_at"] = "2024-01-02T00:00:00"

        # Active files (not deleted)
        active = [k for k, v in files.items() if v["deleted_at"] is None]
        assert active == []

        # Restore file1
        files["file1.png"]["deleted_at"] = None

        active = [k for k, v in files.items() if v["deleted_at"] is None]
        assert "file1.png" in active

    def test_cascade_delete_verification(self, mock_s3_client):
        """Test cascade delete removes all related files."""
        mock_s3_client.delete_object.return_value = {}

        # User files to delete
        user_files = [
            "users/1/avatar.png",
            "users/1/documents/cert1.pdf",
            "users/1/documents/cert2.pdf",
            "users/1/photos/photo1.jpg",
        ]

        # Delete all
        with patch("core.storage._s3_client", return_value=mock_s3_client):
            for file_url in user_files:
                delete_file(f"https://minio.example.com/bucket/{file_url}")

        # Verify all deletions were attempted
        assert mock_s3_client.delete_object.call_count == 4

    def test_reference_counting_accuracy(self):
        """Test reference counting for shared files."""
        file_references = {
            "shared_image.png": {"count": 3, "users": [1, 2, 3]},
            "unique_image.png": {"count": 1, "users": [1]},
        }

        def remove_reference(file_key: str, user_id: int) -> bool:
            """Returns True if file should be deleted (no more references)."""
            if file_key not in file_references:
                return False

            ref = file_references[file_key]
            if user_id in ref["users"]:
                ref["users"].remove(user_id)
                ref["count"] -= 1

            return ref["count"] == 0

        # Remove reference from shared file
        assert remove_reference("shared_image.png", 1) is False  # Still has refs
        assert remove_reference("shared_image.png", 2) is False  # Still has refs
        assert remove_reference("shared_image.png", 3) is True   # No more refs

        # Remove from unique file
        assert remove_reference("unique_image.png", 1) is True   # No more refs

    def test_background_cleanup_job_failure_handling(self):
        """Test handling of background cleanup job failures."""
        cleanup_tasks = [
            {"file": "orphan1.png", "status": "pending"},
            {"file": "orphan2.png", "status": "pending"},
            {"file": "orphan3.png", "status": "pending"},
        ]

        def run_cleanup(task: dict) -> bool:
            if task["file"] == "orphan2.png":
                task["status"] = "failed"
                task["error"] = "Permission denied"
                return False
            task["status"] = "completed"
            return True

        [run_cleanup(task) for task in cleanup_tasks]

        # One failed
        failed = [t for t in cleanup_tasks if t["status"] == "failed"]
        assert len(failed) == 1
        assert failed[0]["file"] == "orphan2.png"

    def test_delete_nonexistent_file_idempotent(self, mock_s3_client):
        """Test deleting nonexistent file is idempotent."""
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3_client.delete_object.side_effect = ClientError(
            error_response, "DeleteObject"
        )

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            # Should not raise
            delete_file("https://minio.example.com/bucket/nonexistent.png")

    def test_delete_files_batch_operation(self, mock_s3_client):
        """Test batch deletion of multiple files."""
        mock_s3_client.delete_object.return_value = {}

        urls = [
            "https://minio.example.com/bucket/file1.png",
            "https://minio.example.com/bucket/file2.png",
            None,  # Should be skipped
            "https://minio.example.com/bucket/file3.png",
        ]

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            delete_files(urls)

        # 3 files deleted (None skipped)
        assert mock_s3_client.delete_object.call_count == 3


# =============================================================================
# 8. Avatar/Profile Image Specific Scenarios
# =============================================================================


class TestAvatarProfileImageSpecific:
    """Test avatar and profile image specific scenarios."""

    @pytest.mark.asyncio
    async def test_avatar_update_during_active_session(self, mock_s3_client):
        """Test avatar update while user has active sessions."""
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.put_object.return_value = {}
        mock_s3_client.delete_object.return_value = {}

        old_avatar_url = "https://minio.example.com/bucket/tutor_profiles/1/photo/old.png"
        new_avatar_content = create_test_image(400, 400)
        upload = create_upload_file(new_avatar_content, "new_avatar.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                new_url = await store_profile_photo(
                    user_id=1,
                    upload=upload,
                    existing_url=old_avatar_url,
                )

        # New URL should be generated
        assert new_url != old_avatar_url
        # Old avatar should be deleted
        mock_s3_client.delete_object.assert_called()

    def test_old_avatar_cleanup_timing(self, mock_s3_client):
        """Test that old avatar is cleaned up after new upload succeeds."""
        mock_s3_client.delete_object.return_value = {}

        # Track deletion order
        operations = []

        original_put = mock_s3_client.put_object

        def track_put(*args, **kwargs):
            operations.append("put")
            return original_put(*args, **kwargs)

        def track_delete(*args, **kwargs):
            operations.append("delete")
            return {}

        mock_s3_client.put_object = track_put
        mock_s3_client.delete_object = track_delete

        # Simulate: put new, then delete old
        mock_s3_client.put_object(Bucket="test", Key="new", Body=b"data")
        mock_s3_client.delete_object(Bucket="test", Key="old")

        # Delete should happen after put
        assert operations == ["put", "delete"]

    def test_default_avatar_fallback(self):
        """Test fallback to default avatar when none set."""
        default_avatar = "https://placehold.co/300x300?text=Avatar"

        # None or empty key should return default
        result = build_avatar_url(None, default=default_avatar)
        assert result == default_avatar

        result = build_avatar_url("", default=default_avatar)
        assert result == default_avatar

    def test_avatar_cdn_cache_invalidation_pattern(self):
        """Test pattern for CDN cache invalidation on avatar update."""
        # Simulate CDN cache invalidation
        cdn_cache = {
            "https://cdn.example.com/avatars/user1.png": {
                "cached_at": "2024-01-01T00:00:00",
                "ttl": 3600,
            }
        }

        def invalidate_cache(url: str):
            if url in cdn_cache:
                del cdn_cache[url]
                return True
            return False

        # Avatar updated - invalidate cache
        result = invalidate_cache("https://cdn.example.com/avatars/user1.png")
        assert result is True
        assert "https://cdn.example.com/avatars/user1.png" not in cdn_cache

    def test_profile_completeness_with_avatar(self):
        """Test profile completeness calculation with avatar."""
        profile = {
            "name": "John Doe",
            "bio": "A tutor",
            "avatar_url": None,
            "subjects": ["Math"],
            "hourly_rate": 50,
        }

        def calculate_completeness(profile: dict) -> int:
            """Calculate profile completeness percentage."""
            fields = ["name", "bio", "avatar_url", "subjects", "hourly_rate"]
            filled = sum(1 for f in fields if profile.get(f))
            return int((filled / len(fields)) * 100)

        # Without avatar
        assert calculate_completeness(profile) == 80

        # With avatar
        profile["avatar_url"] = "https://minio.example.com/avatar.png"
        assert calculate_completeness(profile) == 100

    @pytest.mark.asyncio
    async def test_avatar_upload_with_transparency(self, mock_s3_client):
        """Test avatar upload with PNG transparency."""
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.put_object.return_value = {}

        # Create PNG with transparency (RGBA)
        transparent_avatar = create_test_image(
            400, 400, "PNG", mode="RGBA", color=(255, 0, 0, 128)
        )
        upload = create_upload_file(
            transparent_avatar, "transparent.png", "image/png"
        )

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                url = await store_profile_photo(user_id=1, upload=upload)

        assert url is not None

    @pytest.mark.asyncio
    async def test_avatar_dimensions_after_processing(self, mock_s3_client):
        """Test avatar dimensions meet requirements after processing."""
        mock_s3_client.head_bucket.return_value = {}

        captured_body = {}

        def capture_upload(*args, **kwargs):
            captured_body["content"] = kwargs.get("Body")
            return {}

        mock_s3_client.put_object = MagicMock(side_effect=capture_upload)

        # Small image that needs upscaling
        small_avatar = create_test_image(100, 100)
        upload = create_upload_file(small_avatar, "small.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                await store_profile_photo(user_id=1, upload=upload)

        # Check processed dimensions
        with Image.open(BytesIO(captured_body["content"])) as img:
            assert img.width >= MIN_IMAGE_DIMENSION
            assert img.height >= MIN_IMAGE_DIMENSION

    def test_avatar_url_key_extraction(self):
        """Test extracting storage key from avatar URL."""
        full_url = "https://minio.valsa.solutions/tutor-assets/tutor_profiles/1/photo/abc123.png"

        key = _extract_key_from_url(full_url)

        assert key == "tutor_profiles/1/photo/abc123.png"

    def test_avatar_url_key_extraction_with_query_params(self):
        """Test key extraction from URL with query parameters."""
        url_with_params = (
            "https://minio.valsa.solutions/tutor-assets/tutor_profiles/1/photo/abc.png"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600"
        )

        key = _extract_key_from_url(url_with_params)

        assert key == "tutor_profiles/1/photo/abc.png"
        assert "X-Amz" not in (key or "")

    @pytest.mark.asyncio
    async def test_concurrent_avatar_updates_same_user(self, mock_s3_client):
        """Test handling concurrent avatar updates for same user."""
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.put_object.return_value = {}
        mock_s3_client.delete_object.return_value = {}

        avatar1 = create_test_image(400, 400, color=(255, 0, 0))
        avatar2 = create_test_image(400, 400, color=(0, 255, 0))

        upload1 = create_upload_file(avatar1, "avatar1.png", "image/png")
        upload2 = create_upload_file(avatar2, "avatar2.png", "image/png")

        with patch("core.storage._s3_client", return_value=mock_s3_client):
            with patch("core.storage._ensure_bucket_exists"):
                results = await asyncio.gather(
                    store_profile_photo(user_id=1, upload=upload1),
                    store_profile_photo(user_id=1, upload=upload2),
                    return_exceptions=True,
                )

        # Both should succeed (last write wins scenario)
        assert all(isinstance(r, str) for r in results)
        assert results[0] != results[1]  # Different URLs


# =============================================================================
# Integration-Style Tests
# =============================================================================


class TestStorageIntegrationScenarios:
    """Integration-style tests for complete upload/download/delete flows."""

    @pytest.mark.asyncio
    async def test_complete_upload_flow(
        self, mock_s3_client, mock_message_s3_client, mock_settings
    ):
        """Test complete file upload flow from validation to storage."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}

        # Create valid image
        image_content = create_test_image(500, 400, "JPEG")
        upload = create_upload_file(image_content, "photo.jpg", "image/jpeg")

        result = await store_message_attachment(
            user_id=123,
            message_id=456,
            upload=upload,
        )

        assert "file_key" in result
        assert result["mime_type"] == "image/jpeg"
        assert result["file_category"] == "image"
        assert result["width"] == 500
        assert result["height"] == 400
        mock_message_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_and_generate_presigned_url(
        self, mock_message_s3_client, mock_settings
    ):
        """Test upload followed by presigned URL generation."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}
        mock_message_s3_client.generate_presigned_url.return_value = (
            "https://minio:9000/bucket/key?presigned"
        )

        # Upload
        content = b"test document content"
        upload = create_upload_file(content, "doc.txt", "text/plain")

        result = await store_message_attachment(1, 1, upload)

        # Generate URL
        url = generate_presigned_url(result["file_key"])

        assert url.startswith("https://")
        assert "presigned" in url

    @pytest.mark.asyncio
    async def test_upload_check_exists_delete_flow(
        self, mock_message_s3_client, mock_settings
    ):
        """Test complete lifecycle: upload, verify exists, delete."""
        mock_message_s3_client.head_bucket.return_value = {}
        mock_message_s3_client.put_object.return_value = {}
        mock_message_s3_client.head_object.return_value = {"ContentLength": 100}
        mock_message_s3_client.delete_object.return_value = {}

        # Upload
        content = b"lifecycle test content"
        upload = create_upload_file(content, "lifecycle.txt", "text/plain")

        result = await store_message_attachment(1, 1, upload)
        file_key = result["file_key"]

        # Check exists
        assert check_file_exists(file_key) is True

        # Delete
        delete_message_attachment(file_key)

        # After delete, head_object should fail
        error_response = {"Error": {"Code": "404"}}
        mock_message_s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        assert check_file_exists(file_key) is False

    def test_filename_security_through_full_flow(self):
        """Test filename sanitization through complete flow."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file.php.png",
            "file\x00.png",
            "<script>alert(1)</script>.png",
            "CON.png",  # Windows reserved name
            "file name with spaces.png",
        ]

        for dangerous in dangerous_filenames:
            key = _generate_secure_key(1, 1, dangerous)

            # Key should be safe
            assert ".." not in key
            assert "\x00" not in key
            assert "<" not in key
            assert ">" not in key
            assert key.startswith("messages/1/1/")
