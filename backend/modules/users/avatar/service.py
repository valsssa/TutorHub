"""Avatar service providing validation, processing, and storage orchestration."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from core.avatar_storage import AvatarStorageClient, get_avatar_storage
from core.config import settings
from models import User
from modules.users.avatar.schemas import AvatarDeleteResponse, AvatarResponse

MAX_AVATAR_BYTES = 2_000_000  # 2 MB
MIN_DIMENSION = 150
MAX_DIMENSION = 2_000
TARGET_SIZE = (300, 300)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_FORMATS = {"JPEG", "PNG"}
CONTENT_TYPE_WEBP = "image/webp"


class AvatarService:
    """Coordinate avatar persistence between storage and database."""

    def __init__(self, db: Session, storage: AvatarStorageClient | None = None) -> None:
        self._db = db
        self._storage = storage or get_avatar_storage()

    async def upload_for_user(self, user: User, upload: UploadFile) -> AvatarResponse:
        """Validate, transform, and persist a user-provided avatar."""
        temp_path, new_key = await self._prepare_avatar(user_id=user.id, upload=upload)
        old_key = user.avatar_key

        try:
            await self._storage.upload_file(new_key, temp_path, content_type=CONTENT_TYPE_WEBP)
        except Exception:
            # Clean temp file before bubbling error
            self._cleanup_temp_file(temp_path)
            raise

        try:
            from datetime import datetime

            user.avatar_key = new_key
            user.updated_at = datetime.now(UTC)  # Update timestamp in code
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            # Rollback storage write to avoid orphaned objects
            await self._storage.delete_file(new_key)
            self._cleanup_temp_file(temp_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save avatar metadata",
            ) from exc
        finally:
            self._cleanup_temp_file(temp_path)

        if old_key and old_key != new_key:
            await self._storage.delete_file(old_key)

        return await self._build_response(new_key)

    async def fetch_for_user(self, user: User) -> AvatarResponse:
        """Return signed URL for the current user's avatar or default."""
        if not user.avatar_key:
            return self._default_response()

        return await self._build_response(user.avatar_key)

    async def delete_for_user(self, user: User) -> AvatarDeleteResponse:
        """Delete avatar from storage and reset metadata."""
        if not user.avatar_key:
            return AvatarDeleteResponse(detail="Avatar already removed")

        key_to_delete = user.avatar_key
        try:
            from datetime import datetime

            user.avatar_key = None
            user.updated_at = datetime.now(UTC)  # Update timestamp in code
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove avatar metadata",
            ) from exc

        await self._storage.delete_file(key_to_delete)
        return AvatarDeleteResponse(detail="Avatar removed successfully")

    async def _prepare_avatar(self, *, user_id: int, upload: UploadFile) -> tuple[str, str]:
        """Validate upload, transform to WebP, and persist to temp storage."""
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG and PNG avatars are supported",
            )

        payload = await upload.read()
        if len(payload) > MAX_AVATAR_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Avatar exceeds 2 MB limit",
            )

        try:
            with Image.open(BytesIO(payload)) as image:
                image_format = (image.format or "").upper()
                if image_format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Unsupported image format",
                    )

                width, height = image.size
                if width < MIN_DIMENSION or height < MIN_DIMENSION:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Avatar must be at least 150x150 pixels",
                    )
                if width > MAX_DIMENSION or height > MAX_DIMENSION:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Avatar exceeds maximum dimension of 2000x2000 pixels",
                    )

                rgb_image = image.convert("RGB")
                processed = ImageOps.fit(rgb_image, TARGET_SIZE, Image.Resampling.LANCZOS)

                buffer = BytesIO()
                processed.save(
                    buffer,
                    format="WEBP",
                    quality=90,
                    method=6,
                )
                buffer.seek(0)
                output_bytes = buffer.read()
        except HTTPException:
            raise
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data",
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive guard
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process avatar",
            ) from exc

        temp_dir = Path(os.getenv("AVATAR_TMP_DIR", "/tmp"))
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".webp", dir=temp_dir, delete=False) as temp_file:
            temp_file_path = Path(temp_file.name)
            async with aiofiles.open(temp_file_path, "wb") as tmp_fp:
                await tmp_fp.write(output_bytes)

        key = self._build_object_key(user_id=user_id)
        return str(temp_file_path), key

    async def _build_response(self, key: str) -> AvatarResponse:
        signed_url = await self._storage.generate_presigned_url(key)
        expires_at = datetime.now(UTC) + timedelta(seconds=self._storage.url_ttl())
        return AvatarResponse(avatar_url=signed_url, expires_at=expires_at)

    def _default_response(self) -> AvatarResponse:
        expires_at = datetime.now(UTC) + timedelta(seconds=self._storage.url_ttl())
        return AvatarResponse(avatar_url=settings.AVATAR_STORAGE_DEFAULT_URL, expires_at=expires_at)

    def _build_object_key(self, *, user_id: int) -> str:
        return f"avatars/{user_id}/{uuid4().hex}.webp"

    @staticmethod
    def _cleanup_temp_file(path: str) -> None:
        with suppress(FileNotFoundError):
            Path(path).unlink(missing_ok=True)
