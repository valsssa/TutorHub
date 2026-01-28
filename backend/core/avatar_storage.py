"""Asynchronous MinIO/S3 storage client for user avatars."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import lru_cache

import aiofiles
from aiobotocore.session import get_session
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)


class AvatarStorageClient:
    """Async S3-compatible storage client with bucket auto-provisioning."""

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
        self._public_endpoint = public_endpoint or endpoint
        self._url_ttl_seconds = url_ttl_seconds
        self._session = get_session()
        self._client_config = BotoConfig(signature_version="s3v4")
        self._bucket_initialized = False
        self._bucket_lock = asyncio.Lock()

    @asynccontextmanager
    async def _client(self, *, use_public_endpoint: bool = False):
        endpoint = self._public_endpoint if use_public_endpoint else self._endpoint
        # Determine SSL from endpoint URL
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
        """Ensure the target bucket exists before storing objects."""
        if self._bucket_initialized:
            return

        async with self._bucket_lock:
            if self._bucket_initialized:
                return

            try:
                async with self._client() as client:
                    await client.head_bucket(Bucket=self._bucket)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in {"404", "NoSuchBucket"}:
                    create_params = {"Bucket": self._bucket}
                    if self._region and self._region.lower() != "us-east-1":
                        create_params["CreateBucketConfiguration"] = {"LocationConstraint": self._region}
                    try:
                        async with self._client() as client:
                            await client.create_bucket(**create_params)

                            # Set bucket policy: public read, authenticated write
                            import json

                            policy = {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Sid": "PublicReadAccess",
                                        "Effect": "Allow",
                                        "Principal": {"AWS": "*"},
                                        "Action": ["s3:GetObject"],
                                        "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
                                    },
                                    {
                                        "Sid": "AuthenticatedWriteAccess",
                                        "Effect": "Allow",
                                        "Principal": {"AWS": [f"arn:aws:iam:::user/{self._access_key}"]},
                                        "Action": ["s3:PutObject", "s3:DeleteObject"],
                                        "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
                                    },
                                ],
                            }
                            try:
                                await client.put_bucket_policy(Bucket=self._bucket, Policy=json.dumps(policy))
                                logger.info(
                                    "Set bucket policy for %s: public read, authenticated write",
                                    self._bucket,
                                )
                            except ClientError as policy_exc:
                                logger.warning("Failed to set bucket policy: %s", policy_exc)

                    except ClientError as create_exc:
                        logger.error(
                            "Failed to auto-create avatar bucket %s: %s",
                            self._bucket,
                            create_exc,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Unable to prepare avatar storage",
                        ) from create_exc
                else:
                    logger.error("Failed to access avatar bucket %s: %s", self._bucket, exc)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to access avatar storage",
                    ) from exc

            self._bucket_initialized = True

    async def upload_file(self, key: str, file_path: str, *, content_type: str) -> None:
        """Upload a file from disk to the storage bucket."""
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
                    ACL="private",
                )
        except ClientError as exc:
            logger.error("Failed to upload avatar to key %s: %s", key, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to store avatar",
            ) from exc

    async def delete_file(self, key: str) -> None:
        """Delete an object from the storage bucket."""
        if not key:
            return

        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            # Keep deletion idempotent but log for observability
            logger.warning("Failed to delete avatar key %s: %s", key, exc)

    async def generate_presigned_url(self, key: str) -> str:
        """Generate public URL for avatar access (bucket has public read policy)."""
        if not key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")

        # Return direct public URL since bucket has public read access
        public_url = f"{self._public_endpoint.rstrip('/')}/{self._bucket}/{key}"
        logger.debug("Generated public URL: %s", public_url)
        return public_url

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


def build_avatar_url(
    key: str | None,
    *,
    default: str | None = None,
    allow_absolute: bool = True,
) -> str | None:
    """
    Build a public avatar URL from a storage key.

    Args:
        key: Storage key or absolute URL.
        default: Value to return when key is falsy.
        allow_absolute: If True, return key unchanged when it already looks absolute.
    """
    if not key:
        return default

    if allow_absolute and (key.startswith("http://") or key.startswith("https://")):
        return key

    storage = get_avatar_storage()
    public_endpoint = storage.public_endpoint().rstrip("/")
    bucket = storage.bucket()
    return f"{public_endpoint}/{bucket}/{key}"
