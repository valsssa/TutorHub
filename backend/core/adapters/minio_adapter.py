"""
MinIO Adapter - Implementation of StoragePort for MinIO/S3.

Wraps the existing avatar_storage.py functionality with the StoragePort interface.
Preserves presigned URL generation and security best practices.
"""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import BinaryIO

from aiobotocore.session import get_session
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from core.config import settings
from core.ports.storage import (
    FileMetadata,
    StorageResult,
    StorageStatus,
)

logger = logging.getLogger(__name__)


class MinIOAdapter:
    """
    MinIO/S3 implementation of StoragePort.

    Features:
    - Private buckets with presigned URL access
    - Async and sync clients
    - Content-Type validation
    - Secure object keys
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
        use_ssl: bool = True,
        public_endpoint: str | None = None,
        url_ttl_seconds: int = 300,
    ) -> None:
        self._endpoint = endpoint or settings.AVATAR_STORAGE_ENDPOINT
        self._access_key = access_key or settings.AVATAR_STORAGE_ACCESS_KEY
        self._secret_key = secret_key or settings.AVATAR_STORAGE_SECRET_KEY
        self._region = region or settings.AVATAR_STORAGE_REGION
        self._use_ssl = use_ssl
        self._public_endpoint = public_endpoint or settings.AVATAR_STORAGE_PUBLIC_ENDPOINT or self._endpoint
        self._url_ttl_seconds = url_ttl_seconds
        self._session = get_session()
        self._client_config = BotoConfig(signature_version="s3v4")
        self._buckets_initialized: set[str] = set()

    @asynccontextmanager
    async def _client(self, *, use_public_endpoint: bool = False):
        """Create an S3 client context manager."""
        endpoint = self._public_endpoint if use_public_endpoint else self._endpoint
        use_ssl = endpoint.startswith("https://") if use_public_endpoint else self._use_ssl

        async with self._session.create_client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
            use_ssl=use_ssl,
            config=self._client_config,
        ) as client:
            yield client

    async def ensure_bucket_exists(
        self,
        bucket: str,
    ) -> StorageResult:
        """Ensure a bucket exists, creating it if necessary."""
        if bucket in self._buckets_initialized:
            return StorageResult(success=True, bucket=bucket)

        try:
            async with self._client() as client:
                try:
                    await client.head_bucket(Bucket=bucket)
                except ClientError as exc:
                    error_code = exc.response.get("Error", {}).get("Code")
                    if error_code in {"404", "NoSuchBucket"}:
                        # Create bucket
                        create_params = {"Bucket": bucket}
                        if self._region and self._region.lower() != "us-east-1":
                            create_params["CreateBucketConfiguration"] = {
                                "LocationConstraint": self._region
                            }
                        await client.create_bucket(**create_params)
                        logger.info("Created bucket: %s", bucket)
                    else:
                        return StorageResult(
                            success=False,
                            status=StorageStatus.SERVICE_ERROR,
                            bucket=bucket,
                            error_message=str(exc),
                        )

            self._buckets_initialized.add(bucket)
            return StorageResult(success=True, bucket=bucket)

        except Exception as e:
            logger.error("Failed to ensure bucket %s: %s", bucket, e)
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                bucket=bucket,
                error_message=str(e),
            )

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
        await self.ensure_bucket_exists(bucket)

        # Convert BinaryIO to bytes if needed
        if hasattr(data, "read"):
            data = data.read()

        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                    ACL="private",
                    CacheControl="max-age=31536000, immutable",
                    Metadata=metadata or {},
                )

            logger.debug("Uploaded file: %s/%s (%s)", bucket, key, content_type)
            return StorageResult(
                success=True,
                status=StorageStatus.SUCCESS,
                key=key,
                bucket=bucket,
                size_bytes=len(data),
                content_type=content_type,
            )

        except ClientError as exc:
            logger.error("Failed to upload to %s/%s: %s", bucket, key, exc)
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=str(exc),
            )

    async def download_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> tuple[bytes | None, StorageResult]:
        """Download a file from storage."""
        try:
            async with self._client() as client:
                response = await client.get_object(Bucket=bucket, Key=key)
                async with response["Body"] as stream:
                    data = await stream.read()

            return data, StorageResult(
                success=True,
                status=StorageStatus.SUCCESS,
                key=key,
                bucket=bucket,
                size_bytes=len(data),
                content_type=response.get("ContentType"),
            )

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                return None, StorageResult(
                    success=False,
                    status=StorageStatus.NOT_FOUND,
                    key=key,
                    bucket=bucket,
                    error_message="File not found",
                )
            return None, StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=str(exc),
            )

    async def delete_file(
        self,
        *,
        bucket: str,
        key: str,
    ) -> StorageResult:
        """Delete a file from storage (idempotent)."""
        if not key:
            return StorageResult(success=True, bucket=bucket)

        try:
            async with self._client() as client:
                await client.delete_object(Bucket=bucket, Key=key)

            logger.debug("Deleted file: %s/%s", bucket, key)
            return StorageResult(
                success=True,
                status=StorageStatus.SUCCESS,
                key=key,
                bucket=bucket,
            )

        except ClientError as exc:
            logger.warning("Failed to delete %s/%s: %s", bucket, key, exc)
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=str(exc),
            )

    async def get_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        for_upload: bool = False,
    ) -> StorageResult:
        """Generate a presigned URL for temporary access."""
        if not key:
            return StorageResult(
                success=False,
                status=StorageStatus.NOT_FOUND,
                error_message="Key is required",
            )

        expiry = expires_in_seconds or self._url_ttl_seconds
        operation = "put_object" if for_upload else "get_object"

        try:
            async with self._client(use_public_endpoint=True) as client:
                url = await client.generate_presigned_url(
                    operation,
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expiry,
                )

            return StorageResult(
                success=True,
                status=StorageStatus.SUCCESS,
                key=key,
                bucket=bucket,
                presigned_url=url,
            )

        except ClientError as exc:
            logger.error("Failed to generate presigned URL for %s/%s: %s", bucket, key, exc)
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                key=key,
                bucket=bucket,
                error_message=str(exc),
            )

    async def file_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Check if a file exists in storage."""
        if not key:
            return False

        try:
            async with self._client() as client:
                await client.head_object(Bucket=bucket, Key=key)
                return True
        except ClientError:
            return False

    async def get_file_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> FileMetadata | None:
        """Get metadata for a stored file."""
        try:
            async with self._client() as client:
                response = await client.head_object(Bucket=bucket, Key=key)

            return FileMetadata(
                key=key,
                bucket=bucket,
                size_bytes=response.get("ContentLength", 0),
                content_type=response.get("ContentType", "application/octet-stream"),
                last_modified=response.get("LastModified"),
                etag=response.get("ETag"),
                metadata=dict(response.get("Metadata", {})),
            )

        except ClientError:
            return None

    async def list_files(
        self,
        *,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
    ) -> list[FileMetadata]:
        """List files in a bucket."""
        try:
            async with self._client() as client:
                params = {"Bucket": bucket, "MaxKeys": max_keys}
                if prefix:
                    params["Prefix"] = prefix

                response = await client.list_objects_v2(**params)

            files = []
            for obj in response.get("Contents", []):
                files.append(
                    FileMetadata(
                        key=obj["Key"],
                        bucket=bucket,
                        size_bytes=obj.get("Size", 0),
                        content_type="application/octet-stream",
                        last_modified=obj.get("LastModified"),
                        etag=obj.get("ETag"),
                    )
                )
            return files

        except ClientError as exc:
            logger.error("Failed to list files in %s: %s", bucket, exc)
            return []

    async def copy_file(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageResult:
        """Copy a file within storage."""
        await self.ensure_bucket_exists(dest_bucket)

        try:
            async with self._client() as client:
                await client.copy_object(
                    Bucket=dest_bucket,
                    Key=dest_key,
                    CopySource={"Bucket": source_bucket, "Key": source_key},
                )

            logger.debug(
                "Copied file: %s/%s -> %s/%s",
                source_bucket, source_key, dest_bucket, dest_key,
            )
            return StorageResult(
                success=True,
                status=StorageStatus.SUCCESS,
                key=dest_key,
                bucket=dest_bucket,
            )

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                return StorageResult(
                    success=False,
                    status=StorageStatus.NOT_FOUND,
                    error_message="Source file not found",
                )
            return StorageResult(
                success=False,
                status=StorageStatus.SERVICE_ERROR,
                error_message=str(exc),
            )


@lru_cache(maxsize=1)
def get_minio_adapter() -> MinIOAdapter:
    """Get the default MinIO adapter instance."""
    return MinIOAdapter()


# Default instance
minio_adapter = MinIOAdapter()
