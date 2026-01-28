"""Object storage utilities for tutor profile assets using MinIO."""

import os
import secrets
from collections.abc import Iterable
from contextlib import suppress
from functools import lru_cache
from io import BytesIO

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from core.sanitization import sanitize_filename

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MIN_IMAGE_DIMENSION = 300
MAX_IMAGE_DIMENSION = 4096
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
DOCUMENT_CONTENT_TYPES = IMAGE_CONTENT_TYPES | {"application/pdf"}

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "tutor-assets")
MINIO_REGION = os.getenv("MINIO_REGION")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "https://minio.valsa.solutions")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@lru_cache(maxsize=1)
def _s3_client():
    """Return a lazily constructed S3 client for MinIO."""
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION or None,
        use_ssl=MINIO_USE_SSL,
        config=BotoConfig(signature_version="s3v4"),
    )


def _ensure_bucket_exists() -> None:
    client = _s3_client()
    bucket_exists = False

    try:
        client.head_bucket(Bucket=MINIO_BUCKET)
        bucket_exists = True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            create_params = {"Bucket": MINIO_BUCKET}
            if MINIO_REGION and MINIO_REGION.lower() != "us-east-1":
                create_params["CreateBucketConfiguration"] = {"LocationConstraint": MINIO_REGION}
            try:
                client.create_bucket(**create_params)
                bucket_exists = True
            except ClientError as create_exc:
                error_code = create_exc.response.get("Error", {}).get("Code", "")
                if error_code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to create storage bucket",
                    ) from create_exc
                bucket_exists = True
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to access storage bucket",
            ) from exc

    # Set public read policy for tutor assets
    if bucket_exists:
        try:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"],
                    }
                ],
            }
            import json

            client.put_bucket_policy(Bucket=MINIO_BUCKET, Policy=json.dumps(policy))
        except ClientError:
            # Policy setting is best-effort, don't fail if it doesn't work
            pass


def _generate_filename(original_filename: str, *, forced_extension: str | None = None) -> str:
    """Generate secure filename with sanitization to prevent attacks."""
    # Sanitize the filename first to remove malicious characters
    safe_filename = sanitize_filename(original_filename)

    if not safe_filename:
        # If sanitization resulted in empty string, use default
        return f"{secrets.token_hex(16)}.{(forced_extension or 'bin')}"

    suffix = (forced_extension or "").lower()
    if not suffix and "." in safe_filename:
        suffix = safe_filename.rsplit(".", 1)[1].lower()

    # Only allow alphanumeric extensions
    if suffix and not suffix.isalnum():
        suffix = "bin"

    return f"{secrets.token_hex(16)}.{suffix or 'bin'}"


def _build_object_key(*parts: str) -> str:
    safe_parts = [str(part).strip("/") for part in parts if str(part).strip("/")]
    return "/".join(safe_parts)


def _validate_size(content: bytes, max_bytes: int, message: str) -> None:
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


def _process_image(content: bytes, *, original_content_type: str) -> tuple[bytes, str, str]:
    """
    Resize and normalize uploaded image content.

    Returns:
        Tuple containing processed bytes, resolved content-type, and file extension.
    """
    format_map = {
        "image/jpeg": ("JPEG", "jpg", "RGB"),
        "image/png": ("PNG", "png", "RGBA"),
    }
    target_format, extension, target_mode = format_map.get(original_content_type, ("PNG", "png", "RGBA"))
    try:
        with Image.open(BytesIO(content)) as image:
            image.load()
            if target_mode and image.mode != target_mode:
                image = image.convert(target_mode)
            width, height = image.size
            if width <= 0 or height <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image dimensions",
                )

            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                scale = max(MIN_IMAGE_DIMENSION / width, MIN_IMAGE_DIMENSION / height)
                new_size = (
                    max(MIN_IMAGE_DIMENSION, int(round(width * scale))),
                    max(MIN_IMAGE_DIMENSION, int(round(height * scale))),
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                width, height = image.size

            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                scale = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
                new_size = (
                    max(MIN_IMAGE_DIMENSION, int(round(width * scale))),
                    max(MIN_IMAGE_DIMENSION, int(round(height * scale))),
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                width, height = image.size

            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                target_width = max(width, MIN_IMAGE_DIMENSION)
                target_height = max(height, MIN_IMAGE_DIMENSION)
                if target_mode == "RGBA":
                    background_color = (255, 255, 255, 0)
                elif target_mode == "L":
                    background_color = 255
                else:
                    background_color = (255, 255, 255)
                canvas = Image.new(
                    target_mode or image.mode,
                    (target_width, target_height),
                    color=background_color,
                )
                offset = (
                    (target_width - width) // 2,
                    (target_height - height) // 2,
                )
                canvas.paste(image, offset)
                image = canvas

            buffer = BytesIO()
            save_kwargs = {"optimize": True}
            if target_format == "JPEG":
                save_kwargs.update({"quality": 90})
            image.save(buffer, format=target_format, **save_kwargs)
            buffer.seek(0)
            processed = buffer.read()
    except HTTPException:
        raise
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process image",
        ) from exc

    processed_content_type = "image/jpeg" if target_format == "JPEG" else "image/png"
    return processed, processed_content_type, extension


def _public_url_for_key(key: str) -> str:
    base = MINIO_PUBLIC_ENDPOINT.rstrip("/")
    return f"{base}/{MINIO_BUCKET}/{key}"


def _extract_key_from_url(public_url: str | None) -> str | None:
    if not public_url:
        return None

    url_without_query = public_url.split("?", 1)[0]
    candidates = {
        f"{MINIO_PUBLIC_ENDPOINT.rstrip('/')}/{MINIO_BUCKET}/",
        f"{MINIO_ENDPOINT.rstrip('/')}/{MINIO_BUCKET}/",
        f"{MINIO_BUCKET}/",
    }

    for prefix in candidates:
        if url_without_query.startswith(prefix):
            return url_without_query[len(prefix) :]

    return None


async def store_profile_photo(
    user_id: int,
    upload: UploadFile,
    *,
    existing_url: str | None = None,
) -> str:
    """Store a tutor profile photo and return its public URL."""
    if upload.content_type not in IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported")

    content = await upload.read()
    _validate_size(content, MAX_IMAGE_SIZE_BYTES, "Image exceeds 5 MB limit")
    processed_content, processed_content_type, extension = _process_image(
        content, original_content_type=upload.content_type
    )
    _validate_size(processed_content, MAX_IMAGE_SIZE_BYTES, "Image exceeds 5 MB limit")

    key = _build_object_key(
        "tutor_profiles",
        str(user_id),
        "photo",
        _generate_filename(upload.filename or "photo", forced_extension=extension),
    )
    _ensure_bucket_exists()

    client = _s3_client()
    try:
        client.put_object(
            Bucket=MINIO_BUCKET,
            Key=key,
            Body=processed_content,
            ContentType=processed_content_type,
        )
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store profile photo",
        ) from exc

    # Remove old photo after new upload succeeds
    delete_file(existing_url)
    return _public_url_for_key(key)


async def store_supporting_document(
    user_id: int,
    category: str,
    upload: UploadFile,
) -> str:
    """Store a certification or education document and return its public URL."""
    if upload.content_type not in DOCUMENT_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document type. Allowed: PDF, JPG, PNG",
        )

    content = await upload.read()
    _validate_size(content, MAX_DOCUMENT_SIZE_BYTES, "Document exceeds 5 MB limit")

    processed_content = content
    processed_content_type = upload.content_type
    forced_extension: str | None = None
    if upload.content_type in IMAGE_CONTENT_TYPES:
        processed_content, processed_content_type, forced_extension = _process_image(
            content, original_content_type=upload.content_type
        )
        _validate_size(
            processed_content,
            MAX_DOCUMENT_SIZE_BYTES,
            "Document exceeds 5 MB limit",
        )

    key = _build_object_key(
        "tutor_profiles",
        str(user_id),
        category,
        _generate_filename(upload.filename or "document", forced_extension=forced_extension),
    )
    _ensure_bucket_exists()

    client = _s3_client()
    try:
        client.put_object(
            Bucket=MINIO_BUCKET,
            Key=key,
            Body=processed_content,
            ContentType=processed_content_type,
        )
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store supporting document",
        ) from exc

    return _public_url_for_key(key)


def delete_file(public_url: str | None) -> None:
    """Delete a stored object using its public URL."""
    key = _extract_key_from_url(public_url)
    if not key:
        return

    client = _s3_client()
    with suppress(ClientError):
        client.delete_object(Bucket=MINIO_BUCKET, Key=key)


def delete_files(urls: Iterable[str | None]) -> None:
    """Delete multiple stored objects."""
    for url in urls:
        delete_file(url)
