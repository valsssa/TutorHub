"""
Message Attachment Storage - Secure File Management for Messaging

DDD+KISS Principles:
- Separate bucket for message files (isolation from tutor assets)
- Private by default (access control required)
- Presigned URLs for temporary secure access
- Virus scanning placeholder (extensible)
- File type validation and size limits
"""

import logging
import secrets
from functools import lru_cache
from io import BytesIO

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
from PIL import Image

from core.config import settings
from core.sanitization import sanitize_filename

logger = logging.getLogger(__name__)

# File limits and allowed types (from settings)
MAX_FILE_SIZE = settings.MESSAGE_ATTACHMENT_MAX_FILE_SIZE
MAX_IMAGE_SIZE = settings.MESSAGE_ATTACHMENT_MAX_IMAGE_SIZE
PRESIGNED_URL_EXPIRY = settings.MESSAGE_ATTACHMENT_URL_TTL_SECONDS

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES


@lru_cache(maxsize=1)
def _s3_client():
    """Return a lazily constructed S3 client for MinIO."""
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=settings.MESSAGE_ATTACHMENT_STORAGE_ENDPOINT,
        aws_access_key_id=settings.MESSAGE_ATTACHMENT_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.MESSAGE_ATTACHMENT_STORAGE_SECRET_KEY,
        region_name=settings.MESSAGE_ATTACHMENT_STORAGE_REGION or None,
        use_ssl=settings.MESSAGE_ATTACHMENT_STORAGE_USE_SSL,
        config=BotoConfig(signature_version="s3v4"),
    )


def _ensure_bucket_exists() -> None:
    """Create message attachments bucket if it doesn't exist (private by default)."""
    client = _s3_client()
    bucket = settings.MESSAGE_ATTACHMENT_STORAGE_BUCKET
    region = settings.MESSAGE_ATTACHMENT_STORAGE_REGION

    try:
        client.head_bucket(Bucket=bucket)
        logger.debug(f"Bucket {bucket} exists")
        return
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code not in ("404", "NoSuchBucket"):
            logger.error(f"Error checking bucket: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to access storage",
            ) from exc

    # Create bucket (private by default - no public policy)
    try:
        create_params = {"Bucket": bucket}
        if region and region.lower() != "us-east-1":
            create_params["CreateBucketConfiguration"] = {"LocationConstraint": region}
        client.create_bucket(**create_params)
        logger.info(f"Created private bucket: {bucket}")
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            logger.error(f"Failed to create bucket: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create storage bucket",
            ) from exc


def _categorize_file(mime_type: str) -> str:
    """Determine file category based on MIME type."""
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif mime_type in ALLOWED_DOCUMENT_TYPES:
        return "document"
    else:
        return "other"


def _extract_image_dimensions(content: bytes) -> tuple[int | None, int | None]:
    """Extract width and height from image content."""
    try:
        with Image.open(BytesIO(content)) as img:
            return img.width, img.height
    except Exception as e:
        logger.warning(f"Failed to extract image dimensions: {e}")
        return None, None


def _generate_secure_key(user_id: int, message_id: int, original_filename: str) -> str:
    """Generate a secure, unique object key for file storage."""
    # Sanitize filename
    safe_name = sanitize_filename(original_filename)
    if not safe_name:
        safe_name = "file"

    # Extract extension
    extension = ""
    if "." in safe_name:
        extension = safe_name.rsplit(".", 1)[1].lower()
        # Only allow alphanumeric extensions
        if not extension.isalnum() or len(extension) > 10:
            extension = "bin"

    # Build key: messages/{user_id}/{message_id}/{random_hex}.{ext}
    random_part = secrets.token_hex(16)
    filename = f"{random_part}.{extension}" if extension else random_part

    return f"messages/{user_id}/{message_id}/{filename}"


async def store_message_attachment(
    user_id: int,
    message_id: int,
    upload: UploadFile,
) -> dict:
    """
    Store a message attachment securely in MinIO.

    Returns:
        dict with file metadata: {
            'file_key': str,
            'original_filename': str,
            'file_size': int,
            'mime_type': str,
            'file_category': str,
            'width': Optional[int],
            'height': Optional[int],
        }

    Raises:
        HTTPException: If file validation fails or storage error occurs
    """
    # 1. Validate MIME type
    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {upload.content_type}. "
            f"Allowed: images (JPEG, PNG, GIF, WebP) and documents (PDF, DOC, TXT)",
        )

    # 2. Read and validate size
    content = await upload.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {file_size / 1024 / 1024:.1f} MB (max: 10 MB)",
        )

    # 3. Additional image validation
    width, height = None, None
    if upload.content_type in ALLOWED_IMAGE_TYPES:
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image too large: {file_size / 1024 / 1024:.1f} MB (max: 5 MB)",
            )
        width, height = _extract_image_dimensions(content)

    # 4. Generate secure storage key
    file_key = _generate_secure_key(user_id, message_id, upload.filename or "file")
    file_category = _categorize_file(upload.content_type)

    # 5. Ensure bucket exists
    _ensure_bucket_exists()

    # 6. Upload to MinIO
    client = _s3_client()
    bucket = settings.MESSAGE_ATTACHMENT_STORAGE_BUCKET
    try:
        client.put_object(
            Bucket=bucket,
            Key=file_key,
            Body=content,
            ContentType=upload.content_type,
            Metadata={
                "user_id": str(user_id),
                "message_id": str(message_id),
                "original_filename": sanitize_filename(upload.filename or "file"),
            },
        )
        logger.info(
            f"Uploaded message attachment: user={user_id}, message={message_id}, "
            f"key={file_key}, size={file_size}, type={upload.content_type}"
        )
    except ClientError as exc:
        logger.error(f"Failed to upload attachment: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file",
        ) from exc

    # 7. Return metadata
    return {
        "file_key": file_key,
        "original_filename": sanitize_filename(upload.filename or "file"),
        "file_size": file_size,
        "mime_type": upload.content_type,
        "file_category": file_category,
        "width": width,
        "height": height,
    }


def generate_presigned_url(file_key: str, expiry_seconds: int = PRESIGNED_URL_EXPIRY) -> str:
    """
    Generate a presigned URL for secure temporary file access.

    Args:
        file_key: S3 object key
        expiry_seconds: URL validity duration (default: 1 hour)

    Returns:
        Presigned URL string

    Raises:
        HTTPException: If URL generation fails
    """
    client = _s3_client()
    bucket = settings.MESSAGE_ATTACHMENT_STORAGE_BUCKET

    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": file_key},
            ExpiresIn=expiry_seconds,
        )
        logger.debug(f"Generated presigned URL for {file_key} (expires in {expiry_seconds}s)")
        return url
    except ClientError as exc:
        logger.error(f"Failed to generate presigned URL for {file_key}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate file access URL",
        ) from exc


def delete_message_attachment(file_key: str) -> None:
    """
    Delete a message attachment from storage.

    Args:
        file_key: S3 object key to delete
    """
    if not file_key:
        return

    client = _s3_client()
    bucket = settings.MESSAGE_ATTACHMENT_STORAGE_BUCKET
    try:
        client.delete_object(Bucket=bucket, Key=file_key)
        logger.info(f"Deleted message attachment: {file_key}")
    except ClientError as exc:
        # Log but don't fail - idempotent delete
        logger.warning(f"Failed to delete attachment {file_key}: {exc}")


def check_file_exists(file_key: str) -> bool:
    """Check if a file exists in storage."""
    client = _s3_client()
    bucket = settings.MESSAGE_ATTACHMENT_STORAGE_BUCKET
    try:
        client.head_object(Bucket=bucket, Key=file_key)
        return True
    except ClientError:
        return False
