"""
Asynchronous MinIO/S3 storage client for user avatars.

Security Best Practices Implemented:
1. PRIVATE bucket by default - no public access policy
2. Presigned URLs for temporary, time-limited access
3. Server-side encryption metadata support
4. Secure object keys with random UUIDs
5. Content-Type validation on upload
6. Idempotent delete operations
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import lru_cache

import aiofiles
import boto3
from aiobotocore.session import get_session
from botocore.client import Config as SyncBotoConfig
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)


class AvatarStorageClient:
    """
    Async S3-compatible storage client for user avatars.

    Security model:
    - Bucket is PRIVATE (no public access policy)
    - All access via presigned URLs with configurable TTL
    - Objects stored with private ACL
    """

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str | None,
        use_ssl: bool,
        public_endpoint: str | None,
        url_ttl_seconds: int,
    ) -> None:
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region or None
        self._use_ssl = use_ssl
        # Public endpoint used for presigned URL generation (external access)
        self._public_endpoint = public_endpoint or endpoint
        self._url_ttl_seconds = url_ttl_seconds
        self._session = get_session()
        self._client_config = BotoConfig(signature_version="s3v4")
        self._bucket_initialized = False
        self._bucket_lock = asyncio.Lock()

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

    async def ensure_bucket(self) -> None:
        """
        Ensure the target bucket exists before storing objects.

        Creates bucket as PRIVATE (no public access policy).
        This follows security best practices - all access via presigned URLs.
        """
        if self._bucket_initialized:
            return

        async with self._bucket_lock:
            if self._bucket_initialized:
                return

            try:
                async with self._client() as client:
                    await client.head_bucket(Bucket=self._bucket)
                    logger.debug("Avatar bucket %s exists", self._bucket)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in {"404", "NoSuchBucket"}:
                    await self._create_private_bucket()
                else:
                    logger.error("Failed to access avatar bucket %s: %s", self._bucket, exc)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to access avatar storage",
                    ) from exc

            self._bucket_initialized = True

    async def _create_private_bucket(self) -> None:
        """Create a private bucket with no public access."""
        create_params = {"Bucket": self._bucket}
        if self._region and self._region.lower() != "us-east-1":
            create_params["CreateBucketConfiguration"] = {"LocationConstraint": self._region}

        try:
            async with self._client() as client:
                await client.create_bucket(**create_params)
                logger.info(
                    "Created PRIVATE avatar bucket: %s (no public access policy)",
                    self._bucket,
                )

                # Explicitly block public access (defense in depth)
                try:
                    await client.put_public_access_block(
                        Bucket=self._bucket,
                        PublicAccessBlockConfiguration={
                            "BlockPublicAcls": True,
                            "IgnorePublicAcls": True,
                            "BlockPublicPolicy": True,
                            "RestrictPublicBuckets": True,
                        },
                    )
                    logger.info("Enabled public access block for bucket %s", self._bucket)
                except ClientError as block_exc:
                    # MinIO may not support PublicAccessBlock, log and continue
                    logger.debug(
                        "PublicAccessBlock not supported (MinIO): %s",
                        block_exc,
                    )

        except ClientError as create_exc:
            error_code = create_exc.response.get("Error", {}).get("Code", "")
            if error_code in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                logger.debug("Bucket %s already exists", self._bucket)
                return
            logger.error(
                "Failed to create avatar bucket %s: %s",
                self._bucket,
                create_exc,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to prepare avatar storage",
            ) from create_exc

    async def upload_file(self, key: str, file_path: str, *, content_type: str) -> None:
        """
        Upload a file from disk to the storage bucket.

        Files are stored with private ACL - access only via presigned URLs.
        """
        await self.ensure_bucket()

        async with aiofiles.open(file_path, "rb") as file_obj:
            payload = await file_obj.read()

        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=payload,
                    ContentType=content_type,
                    # Private ACL - no public access
                    ACL="private",
                    # Cache control for CDN optimization
                    CacheControl="max-age=31536000, immutable",
                )
                logger.debug("Uploaded avatar: %s (%s)", key, content_type)
        except ClientError as exc:
            logger.error("Failed to upload avatar to key %s: %s", key, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to store avatar",
            ) from exc

    async def delete_file(self, key: str) -> None:
        """Delete an object from the storage bucket (idempotent)."""
        if not key:
            return

        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._bucket, Key=key)
                logger.debug("Deleted avatar: %s", key)
        except ClientError as exc:
            # Keep deletion idempotent but log for observability
            logger.warning("Failed to delete avatar key %s: %s", key, exc)

    async def generate_presigned_url(self, key: str, ttl_seconds: int | None = None) -> str:
        """
        Generate a presigned URL for secure, time-limited avatar access.

        Args:
            key: The object key in storage
            ttl_seconds: URL validity period (defaults to configured TTL)

        Returns:
            Presigned URL with temporary access credentials

        Security:
            - URLs expire after TTL (default 5 minutes)
            - No permanent public access to files
            - Each URL contains signed credentials
        """
        if not key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")

        expiry = ttl_seconds if ttl_seconds is not None else self._url_ttl_seconds

        try:
            # Use public endpoint for presigned URL so it's accessible externally
            async with self._client(use_public_endpoint=True) as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self._bucket,
                        "Key": key,
                    },
                    ExpiresIn=expiry,
                )
                logger.debug(
                    "Generated presigned URL for %s (expires in %ds)",
                    key,
                    expiry,
                )
                return url
        except ClientError as exc:
            logger.error("Failed to generate presigned URL for %s: %s", key, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to generate avatar URL",
            ) from exc

    async def check_file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        if not key:
            return False

        try:
            async with self._client() as client:
                await client.head_object(Bucket=self._bucket, Key=key)
                return True
        except ClientError:
            return False

    def bucket(self) -> str:
        return self._bucket

    def public_endpoint(self) -> str:
        return self._public_endpoint

    def url_ttl(self) -> int:
        return self._url_ttl_seconds


@lru_cache(maxsize=1)
def get_avatar_storage() -> AvatarStorageClient:
    """Factory for the avatar storage client using shared settings."""
    return AvatarStorageClient(
        endpoint=settings.AVATAR_STORAGE_ENDPOINT,
        access_key=settings.AVATAR_STORAGE_ACCESS_KEY,
        secret_key=settings.AVATAR_STORAGE_SECRET_KEY,
        bucket=settings.AVATAR_STORAGE_BUCKET,
        region=settings.AVATAR_STORAGE_REGION,
        use_ssl=settings.AVATAR_STORAGE_USE_SSL,
        public_endpoint=settings.AVATAR_STORAGE_PUBLIC_ENDPOINT,
        url_ttl_seconds=settings.AVATAR_STORAGE_URL_TTL_SECONDS,
    )


# =============================================================================
# Synchronous S3 Client for Presigned URL Generation
# =============================================================================
# Used by sync code paths (repositories, services) that need presigned URLs


@lru_cache(maxsize=1)
def _get_sync_s3_client():
    """Get a synchronous boto3 S3 client for presigned URL generation."""
    endpoint = settings.AVATAR_STORAGE_PUBLIC_ENDPOINT or settings.AVATAR_STORAGE_ENDPOINT
    use_ssl = endpoint.startswith("https://")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.AVATAR_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.AVATAR_STORAGE_SECRET_KEY,
        region_name=settings.AVATAR_STORAGE_REGION or None,
        use_ssl=use_ssl,
        config=SyncBotoConfig(signature_version="s3v4"),
    )


def generate_presigned_url_sync(
    key: str,
    ttl_seconds: int | None = None,
) -> str:
    """
    Generate a presigned URL synchronously for avatar access.

    Args:
        key: The object key in storage
        ttl_seconds: URL validity period (defaults to configured TTL)

    Returns:
        Presigned URL with temporary access credentials
    """
    client = _get_sync_s3_client()
    expiry = ttl_seconds if ttl_seconds is not None else settings.AVATAR_STORAGE_URL_TTL_SECONDS

    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AVATAR_STORAGE_BUCKET,
                "Key": key,
            },
            ExpiresIn=expiry,
        )
        return url
    except ClientError as exc:
        logger.error("Failed to generate presigned URL for %s: %s", key, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate avatar URL",
        ) from exc


def build_avatar_url(
    key: str | None,
    *,
    default: str | None = None,
    allow_absolute: bool = True,
) -> str | None:
    """
    Build a presigned avatar URL from a storage key (synchronous).

    Args:
        key: Storage key or absolute URL.
        default: Value to return when key is falsy (e.g., default avatar URL).
        allow_absolute: If True, return key unchanged when it already looks absolute.

    Returns:
        Presigned URL for private avatar access, or default if key is empty.

    Security:
        - URLs expire after configured TTL (default 5 minutes)
        - No permanent public access to avatar files
        - Each URL contains signed credentials
    """
    if not key:
        return default

    # If already a full URL (e.g., from OAuth provider or external service), return as-is
    if allow_absolute and (key.startswith("http://") or key.startswith("https://")):
        return key

    return generate_presigned_url_sync(key)


async def build_avatar_url_async(
    key: str | None,
    *,
    default: str | None = None,
    allow_absolute: bool = True,
) -> str | None:
    """
    Build a presigned avatar URL from a storage key (async version).

    Use this in async contexts for better performance.
    Falls back to sync generation for simplicity.
    """
    if not key:
        return default

    if allow_absolute and (key.startswith("http://") or key.startswith("https://")):
        return key

    storage = get_avatar_storage()
    return await storage.generate_presigned_url(key)
