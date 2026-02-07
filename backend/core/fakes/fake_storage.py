"""
Fake Storage - In-memory implementation of StoragePort for testing.

Stores files in memory and tracks operations for test assertions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from core.datetime_utils import utc_now
from typing import BinaryIO

from core.ports.storage import (
    FileMetadata,
    StorageResult,
    StorageStatus,
)


@dataclass
class StoredFile:
    """Record of a stored file."""

    key: str
    bucket: str
    data: bytes
    content_type: str
    metadata: dict[str, str]
    created_at: datetime = field(default_factory=lambda: utc_now())
    last_modified: datetime = field(default_factory=lambda: utc_now())


@dataclass
class StorageOperation:
    """Record of a storage operation."""

    operation: str
    bucket: str
    key: str
    timestamp: datetime = field(default_factory=lambda: utc_now())
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeStorage:
    """
    In-memory fake implementation of StoragePort for testing.

    Features:
    - Stores files in a dict
    - Tracks all operations for assertions
    - Configurable success/failure modes
    - Presigned URL generation (fake URLs)
    """

    files: dict[str, StoredFile] = field(default_factory=dict)
    operations: list[StorageOperation] = field(default_factory=list)
    buckets: set[str] = field(default_factory=set)
    should_fail: bool = False
    failure_message: str = "Simulated storage failure"
    presigned_url_base: str = "https://fake-storage.test"

    def _make_key(self, bucket: str, key: str) -> str:
        """Create composite key for storage."""
        return f"{bucket}/{key}"

    def _record_operation(
        self,
        operation: str,
        bucket: str,
        key: str,
        metadata: dict | None = None,
    ) -> None:
        """Record a storage operation."""
        self.operations.append(
            StorageOperation(
                operation=operation,
                bucket=bucket,
                key=key,
                metadata=metadata or {},
            )
        )

    async def ensure_bucket_exists(self, bucket: str) -> StorageResult:
        """Ensure a bucket exists."""
        self._record_operation("ensure_bucket", bucket, "")

        if self.should_fail:
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                bucket=bucket,
                error_message=self.failure_message,
            )

        self.buckets.add(bucket)
        return StorageResult(success=True, bucket=bucket)

    async def upload_file(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes | BinaryIO,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> StorageResult:
        """Upload a file to storage."""
        self._record_operation("upload", bucket, key, {"content_type": content_type})

        if self.should_fail:
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=self.failure_message,
            )

        # Ensure bucket exists
        self.buckets.add(bucket)

        # Convert BinaryIO to bytes if needed
        if hasattr(data, "read"):
            data = data.read()

        composite_key = self._make_key(bucket, key)
        self.files[composite_key] = StoredFile(
            key=key,
            bucket=bucket,
            data=data,
            content_type=content_type,
            metadata=metadata or {},
        )

        return StorageResult(
            success=True,
            status=StorageStatus.SUCCESS,
            key=key,
            bucket=bucket,
            size_bytes=len(data),
            content_type=content_type,
        )

    async def download_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> tuple[bytes | None, StorageResult]:
        """Download a file from storage."""
        self._record_operation("download", bucket, key)

        if self.should_fail:
            return None, StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=self.failure_message,
            )

        composite_key = self._make_key(bucket, key)
        stored = self.files.get(composite_key)

        if stored is None:
            return None, StorageResult(
                success=False,
                status=StorageStatus.NOT_FOUND,
                key=key,
                bucket=bucket,
                error_message="File not found",
            )

        return stored.data, StorageResult(
            success=True,
            status=StorageStatus.SUCCESS,
            key=key,
            bucket=bucket,
            size_bytes=len(stored.data),
            content_type=stored.content_type,
        )

    async def delete_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> StorageResult:
        """Delete a file from storage."""
        self._record_operation("delete", bucket, key)

        if self.should_fail:
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=self.failure_message,
            )

        composite_key = self._make_key(bucket, key)
        if composite_key in self.files:
            del self.files[composite_key]

        return StorageResult(
            success=True,
            status=StorageStatus.SUCCESS,
            key=key,
            bucket=bucket,
        )

    async def get_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        for_upload: bool = False,
    ) -> StorageResult:
        """Generate a fake presigned URL."""
        self._record_operation(
            "presigned_url",
            bucket,
            key,
            {"for_upload": for_upload, "expires": expires_in_seconds},
        )

        if self.should_fail:
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=self.failure_message,
            )

        token = uuid.uuid4().hex[:16]
        action = "upload" if for_upload else "download"
        url = f"{self.presigned_url_base}/{bucket}/{key}?action={action}&token={token}&expires={expires_in_seconds}"

        return StorageResult(
            success=True,
            status=StorageStatus.SUCCESS,
            key=key,
            bucket=bucket,
            presigned_url=url,
        )

    async def file_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Check if a file exists."""
        self._record_operation("exists", bucket, key)
        composite_key = self._make_key(bucket, key)
        return composite_key in self.files

    async def get_file_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> FileMetadata | None:
        """Get metadata for a stored file."""
        self._record_operation("get_metadata", bucket, key)

        composite_key = self._make_key(bucket, key)
        stored = self.files.get(composite_key)

        if stored is None:
            return None

        return FileMetadata(
            key=key,
            bucket=bucket,
            size_bytes=len(stored.data),
            content_type=stored.content_type,
            last_modified=stored.last_modified,
            etag=f'"{uuid.uuid4().hex[:32]}"',
            metadata=stored.metadata,
        )

    async def list_files(
        self,
        *,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
    ) -> list[FileMetadata]:
        """List files in a bucket."""
        self._record_operation("list", bucket, prefix or "")

        result = []
        bucket_prefix = f"{bucket}/"

        for composite_key, stored in self.files.items():
            if not composite_key.startswith(bucket_prefix):
                continue

            if prefix and not stored.key.startswith(prefix):
                continue

            result.append(
                FileMetadata(
                    key=stored.key,
                    bucket=bucket,
                    size_bytes=len(stored.data),
                    content_type=stored.content_type,
                    last_modified=stored.last_modified,
                )
            )

            if len(result) >= max_keys:
                break

        return result

    async def copy_file(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageResult:
        """Copy a file within storage."""
        self._record_operation(
            "copy",
            dest_bucket,
            dest_key,
            {"source_bucket": source_bucket, "source_key": source_key},
        )

        if self.should_fail:
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                error_message=self.failure_message,
            )

        source_composite = self._make_key(source_bucket, source_key)
        source = self.files.get(source_composite)

        if source is None:
            return StorageResult(
                success=False,
                status=StorageStatus.NOT_FOUND,
                error_message="Source file not found",
            )

        self.buckets.add(dest_bucket)
        dest_composite = self._make_key(dest_bucket, dest_key)
        self.files[dest_composite] = StoredFile(
            key=dest_key,
            bucket=dest_bucket,
            data=source.data,
            content_type=source.content_type,
            metadata=source.metadata.copy(),
        )

        return StorageResult(
            success=True,
            status=StorageStatus.SUCCESS,
            key=dest_key,
            bucket=dest_bucket,
        )

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def get_file(self, bucket: str, key: str) -> StoredFile | None:
        """Get a stored file directly (for testing)."""
        return self.files.get(self._make_key(bucket, key))

    def put_file(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store a file directly (for testing setup)."""
        self.buckets.add(bucket)
        self.files[self._make_key(bucket, key)] = StoredFile(
            key=key,
            bucket=bucket,
            data=data,
            content_type=content_type,
            metadata={},
        )

    def get_operations(self, operation: str) -> list[StorageOperation]:
        """Get all operations of a specific type."""
        return [o for o in self.operations if o.operation == operation]

    def clear(self) -> None:
        """Clear all stored files."""
        self.files.clear()
        self.buckets.clear()

    def reset(self) -> None:
        """Reset all state."""
        self.files.clear()
        self.operations.clear()
        self.buckets.clear()
        self.should_fail = False
