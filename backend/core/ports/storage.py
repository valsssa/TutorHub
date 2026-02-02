"""
Storage Port - Interface for file storage operations.

This port defines the contract for file storage operations,
abstracting away the specific storage provider (MinIO, S3, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, BinaryIO, Protocol


class StorageStatus(str, Enum):
    """Status of storage operation."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    INVALID_FILE = "invalid_file"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_ERROR = "service_error"


@dataclass(frozen=True)
class StorageResult:
    """Result of a storage operation."""

    success: bool
    status: StorageStatus = StorageStatus.SUCCESS
    key: str | None = None
    url: str | None = None
    presigned_url: str | None = None
    bucket: str | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FileMetadata:
    """Metadata about a stored file."""

    key: str
    bucket: str
    size_bytes: int
    content_type: str
    last_modified: datetime | None = None
    etag: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class StoragePort(Protocol):
    """
    Protocol for file storage operations.

    Implementations should handle:
    - Bucket creation and management
    - Secure file uploads with content type validation
    - Presigned URLs for temporary access
    - Proper error handling
    """

    async def upload_file(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes | BinaryIO,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> StorageResult:
        """
        Upload a file to storage.

        Args:
            bucket: Target bucket name
            key: Object key (path)
            data: File content (bytes or file-like object)
            content_type: MIME type of the file
            metadata: Optional metadata to store with the file

        Returns:
            StorageResult with upload details
        """
        ...

    async def download_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> tuple[bytes | None, StorageResult]:
        """
        Download a file from storage.

        Args:
            bucket: Source bucket name
            key: Object key (path)

        Returns:
            Tuple of (file_content, StorageResult)
        """
        ...

    async def delete_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> StorageResult:
        """
        Delete a file from storage.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            StorageResult with deletion status
        """
        ...

    async def get_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        for_upload: bool = False,
    ) -> StorageResult:
        """
        Generate a presigned URL for temporary access.

        Args:
            bucket: Bucket name
            key: Object key (path)
            expires_in_seconds: URL expiration time
            for_upload: If True, generate upload URL; else download URL

        Returns:
            StorageResult with presigned_url
        """
        ...

    async def file_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Check if a file exists in storage.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            True if file exists, False otherwise
        """
        ...

    async def get_file_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> FileMetadata | None:
        """
        Get metadata for a stored file.

        Args:
            bucket: Bucket name
            key: Object key (path)

        Returns:
            FileMetadata if file exists, None otherwise
        """
        ...

    async def list_files(
        self,
        *,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
    ) -> list[FileMetadata]:
        """
        List files in a bucket.

        Args:
            bucket: Bucket name
            prefix: Filter by key prefix
            max_keys: Maximum number of keys to return

        Returns:
            List of FileMetadata objects
        """
        ...

    async def ensure_bucket_exists(
        self,
        bucket: str,
    ) -> StorageResult:
        """
        Ensure a bucket exists, creating it if necessary.

        Args:
            bucket: Bucket name to ensure

        Returns:
            StorageResult with status
        """
        ...

    async def copy_file(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageResult:
        """
        Copy a file within storage.

        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key

        Returns:
            StorageResult with copy status
        """
        ...
