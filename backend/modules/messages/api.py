"""
Messages REST API - Clean, Fast, Production-Ready
DDD + KISS: Simple endpoints with comprehensive features + File Attachments.
"""

import contextlib
import logging

from core.datetime_utils import utc_now

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.avatar_storage import build_avatar_url
from core.dependencies import CompleteProfileUser, CurrentUser
from core.exceptions import ValidationError
from core.message_storage import (
    delete_message_attachment,
    generate_presigned_url,
    store_message_attachment,
)
from core.query_helpers import get_by_id_or_404, get_or_404
from database import get_db
from models import Message, MessageAttachment
from modules.messages.service import MessageService
from modules.messages.websocket import manager
from schemas import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    recipient_id: int = Field(..., gt=0, description="ID of the message recipient")
    message: str = Field(..., min_length=1, max_length=2000, description="Message content (1-2000 characters)")
    booking_id: int | None = Field(None, gt=0, description="Optional booking context for the message")


class EditMessageRequest(BaseModel):
    """Request to edit a message (within 15 minutes)."""

    message: str = Field(..., min_length=1, max_length=2000, description="Updated message content")


class MessageThreadResponse(BaseModel):
    """Conversation thread summary with metadata."""

    other_user_id: int
    other_user_email: str
    other_user_first_name: str | None = None
    other_user_last_name: str | None = None
    other_user_avatar_url: str | None = None
    other_user_role: str
    booking_id: int | None = None
    last_message: str
    last_message_time: str
    last_sender_id: int
    unread_count: int


class MessageSearchResponse(BaseModel):
    """Search results for messages."""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedMessagesResponse(BaseModel):
    """Paginated message list."""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    """Unread message counts."""

    total: int
    by_sender: dict[int, int] = Field(default_factory=dict, description="Unread count per sender user ID")


class UserBasicInfoResponse(BaseModel):
    """Basic user information for messaging."""

    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    role: str


# ============================================================================
# Dependency Injection
# ============================================================================


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    """Get message service instance with database session."""
    return MessageService(db)


# ============================================================================
# Core Messaging Endpoints
# ============================================================================


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: SendMessageRequest,
    current_user: CompleteProfileUser,
    service: MessageService = Depends(get_message_service),
):
    """
    Send a message to another user. Requires complete profile (first/last name).

    **Business Rules:**
    - Message length: 1-2000 characters
    - PII (email, phone, external links) automatically masked in pre-booking chats
    - Real-time delivery via WebSocket to online recipients
    - Sender cannot message themselves

    **Returns:** Created message with ID and timestamp
    """
    try:
        # 1. Send message via service (includes validation) - run in thread pool
        message = await run_in_threadpool(
            service.send_message,
            sender_id=current_user.id,
            recipient_id=request.recipient_id,
            content=request.message,
            booking_id=request.booking_id,
        )

        # 2. Real-time notification via WebSocket to recipient
        await manager.send_personal_message(
            {
                "type": "new_message",
                "message_id": message.id,
                "sender_id": current_user.id,
                "sender_email": current_user.email,
                "sender_role": current_user.role,
                "recipient_id": request.recipient_id,
                "booking_id": request.booking_id,
                "message": message.message,
                "created_at": message.created_at.isoformat(),
                "is_read": False,
                "is_edited": False,
            },
            request.recipient_id,
        )

        # 3. Multi-device sync: notify sender's other devices
        await manager.send_personal_message(
            {
                "type": "message_sent",
                "message_id": message.id,
                "recipient_id": request.recipient_id,
                "message": message.message,
                "created_at": message.created_at.isoformat(),
            },
            current_user.id,
        )

        logger.info(f"Message sent successfully: id={message.id}, from={current_user.id}, to={request.recipient_id}")

        return message

    except ValidationError as e:
        error_message = str(e)
        logger.warning(f"Message validation failed: {error_message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}", exc_info=True)
        # Return generic error message to avoid information disclosure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message",
        ) from e


@router.get("/threads", response_model=list[MessageThreadResponse])
async def list_threads(
    current_user: CurrentUser,
    limit: int = Query(100, ge=1, le=200, description="Maximum threads to return"),
    service: MessageService = Depends(get_message_service),
):
    """
    Get all conversation threads for current user.

    **Returns:**
    - Threads sorted by most recent activity
    - Unread count per thread
    - Last message preview
    - Sender of last message
    - Other user's role (student/tutor/admin)

    **Use Cases:**
    - Inbox/message list view
    - Unread notification counts
    - Quick conversation access
    - Thread organization

    **Performance:**
    - Optimized query with proper indexing
    - Limited to 200 threads max
    - Includes all relevant metadata
    """
    try:
        threads = service.get_user_threads(current_user.id, limit=limit)

        return [
            MessageThreadResponse(
                other_user_id=t["other_user_id"],
                other_user_email=t["other_user_email"],
                other_user_first_name=t.get("other_user_first_name"),
                other_user_last_name=t.get("other_user_last_name"),
                other_user_avatar_url=t.get("other_user_avatar_url"),
                other_user_role=t["other_user_role"],
                booking_id=t["booking_id"],
                last_message=t["last_message"],
                last_message_time=t["last_message_time"].isoformat(),
                last_sender_id=t["last_sender_id"],
                unread_count=t["unread_count"],
            )
            for t in threads
        ]
    except Exception as e:
        logger.error(f"Error fetching threads: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load conversations",
        ) from e


@router.get("/threads/{other_user_id}", response_model=PaginatedMessagesResponse)
async def get_conversation(
    other_user_id: int,
    current_user: CurrentUser,
    booking_id: int | None = Query(None, description="Filter by booking context"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Messages per page"),
    service: MessageService = Depends(get_message_service),
):
    """
    Get messages in a conversation with another user.

    **Parameters:**
    - `other_user_id`: The other participant's ID
    - `booking_id`: Optional - filter by booking context
    - `page`: Page number (1-indexed)
    - `page_size`: Messages per page (max 100)

    **Returns:**
    - Messages in chronological order (oldest first)
    - Total message count
    - Pagination metadata

    **Use Cases:**
    - Load chat history
    - Infinite scroll pagination
    - Booking-specific messages
    - Message search within thread
    """
    try:
        messages, total = service.get_conversation_messages(
            user1_id=current_user.id,
            user2_id=other_user_id,
            booking_id=booking_id,
            page=page,
            page_size=page_size,
        )

        return PaginatedMessagesResponse(
            messages=messages,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load messages",
        ) from e


@router.get("/search", response_model=MessageSearchResponse)
async def search_messages(
    current_user: CurrentUser,
    search_query: str = Query(..., min_length=2, description="Search query", alias="q"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    service: MessageService = Depends(get_message_service),
):
    """
    Search user's messages by content.

    **Parameters:**
    - `search_query`: Search query (minimum 2 characters)
    - `page`: Page number
    - `page_size`: Results per page (max 50)

    **Returns:**
    - Matching messages (sent or received)
    - Total match count
    - Pagination metadata

    **Use Cases:**
    - Find past conversations
    - Search for specific information
    - Locate booking details
    """
    try:
        messages, total = service.search_messages(
            user_id=current_user.id,
            search_query=search_query,
            page=page,
            page_size=page_size,
        )

        total_pages = (total + page_size - 1) // page_size

        return MessageSearchResponse(
            messages=messages,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages",
        ) from e


# ============================================================================
# Read Receipts & Notifications
# ============================================================================


@router.patch("/{message_id}/read", status_code=status.HTTP_200_OK)
async def mark_read(
    message_id: int,
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """
    Mark a message as read (recipient only).

    **Business Rules:**
    - Only recipient can mark as read
    - Sets read_at timestamp
    - Sends real-time read receipt to sender

    **Use Cases:**
    - User opens/reads a message
    - Automatic read tracking
    - Read receipt notifications
    """
    try:
        message = await run_in_threadpool(service.mark_message_read, message_id, current_user.id)

        # Send read receipt to sender via WebSocket
        await manager.send_personal_message(
            {
                "type": "message_read",
                "message_id": message.id,
                "reader_id": current_user.id,
                "read_at": message.read_at.isoformat() if message.read_at else None,
            },
            message.sender_id,
        )

        return {
            "message": "Marked as read",
            "read_at": message.read_at.isoformat() if message.read_at else None,
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error marking message read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark message as read",
        ) from e


@router.patch("/threads/{other_user_id}/read-all", status_code=status.HTTP_200_OK)
async def mark_thread_read(
    other_user_id: int,
    current_user: CurrentUser,
    booking_id: int | None = Query(None),
    service: MessageService = Depends(get_message_service),
):
    """
    Mark all messages in a thread as read.

    **Use Cases:**
    - User opens a conversation
    - Bulk mark as read
    - Clear unread notifications
    """
    try:
        count = await run_in_threadpool(
            service.mark_thread_read,
            user_id=current_user.id,
            other_user_id=other_user_id,
            booking_id=booking_id,
        )

        # Notify sender that messages were read
        if count > 0:
            await manager.send_personal_message(
                {
                    "type": "thread_read",
                    "reader_id": current_user.id,
                    "message_count": count,
                },
                other_user_id,
            )

        return {"message": f"Marked {count} messages as read", "count": count}

    except Exception as e:
        logger.error(f"Error marking thread read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark thread as read",
        )


# ============================================================================
# File Attachments
# ============================================================================


@router.post("/with-attachment", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message_with_attachment(
    current_user: CompleteProfileUser,
    recipient_id: int = Form(..., gt=0),
    message: str = Form(..., min_length=1, max_length=2000),
    booking_id: int | None = Form(None, gt=0),
    file: UploadFile = File(...),
    service: MessageService = Depends(get_message_service),
    db: Session = Depends(get_db),
):
    """
    Send a message with a file attachment. Requires complete profile (first/last name).

    **Business Rules:**
    - File size limits: 10 MB (5 MB for images)
    - Allowed types: Images (JPEG, PNG, GIF, WebP), Documents (PDF, DOC, TXT)
    - Files stored in private bucket (presigned URLs for access)
    - Automatic virus scanning placeholder
    - PII masking applied to message text

    **Security:**
    - Only sender and recipient can access files
    - Presigned URLs expire after 1 hour
    - Virus scan status tracked (future: integration with ClamAV/VirusTotal)

    **Returns:** Message with attachment metadata
    """
    try:
        # 1. Create message first (validates participants, applies PII masking)
        msg = await run_in_threadpool(
            service.send_message,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=message,
            booking_id=booking_id,
        )

        # 2. Upload file to secure storage
        attachment_data = await store_message_attachment(
            user_id=current_user.id,
            message_id=msg.id,
            upload=file,
        )

        # 3. Create attachment record in database
        from datetime import datetime

        attachment = MessageAttachment(
            message_id=msg.id,
            uploaded_by=current_user.id,
            **attachment_data,
            scan_result="pending",  # Placeholder for virus scanning
            is_public=False,  # Private by default
        )
        attachment.updated_at = utc_now()

        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        logger.info(
            f"Message with attachment sent: msg_id={msg.id}, "
            f"file={attachment.original_filename}, size={attachment.file_size}, "
            f"from={current_user.id}, to={recipient_id}"
        )

        # 4. Refresh message to include attachment
        db.refresh(msg)

        # 5. Real-time notification to recipient with attachment info
        await manager.send_personal_message(
            {
                "type": "new_message",
                "message_id": msg.id,
                "sender_id": current_user.id,
                "sender_email": current_user.email,
                "sender_role": current_user.role,
                "recipient_id": recipient_id,
                "booking_id": booking_id,
                "message": msg.message,
                "created_at": msg.created_at.isoformat(),
                "has_attachment": True,
                "attachment_count": 1,
                "is_read": False,
                "is_edited": False,
            },
            recipient_id,
        )

        return msg

    except ValidationError as e:
        logger.warning(f"Message/file validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message with attachment: {e}", exc_info=True)
        # Cleanup: try to delete uploaded file if message creation failed
        if "attachment_data" in locals():
            with contextlib.suppress(Exception):
                delete_message_attachment(attachment_data["file_key"])
        # Return generic error message to avoid information disclosure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message with attachment",
        )


@router.get("/attachments/{attachment_id}/download")
async def get_attachment_download_url(
    attachment_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Generate a presigned URL for downloading a message attachment.

    **Security:**
    - Only sender or recipient of the message can access attachments
    - URLs expire after 1 hour
    - Access control validated before URL generation

    **Returns:**
    - Presigned S3 URL for secure temporary access
    - Attachment metadata (filename, size, type)

    **Use Cases:**
    - Download file from message
    - View image inline
    - Preview document
    """
    # 1. Get attachment with message context
    attachment = get_or_404(
        db, MessageAttachment,
        {"id": attachment_id},
        detail="Attachment not found"
    )

    # 2. Access control: only sender or recipient can download
    message = get_by_id_or_404(db, Message, attachment.message_id, detail="Message not found")

    is_authorized = current_user.id in {message.sender_id, message.recipient_id}
    if not is_authorized:
        logger.warning(
            f"Unauthorized attachment access attempt: user={current_user.id}, "
            f"attachment={attachment_id}, message={message.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to access this file"
        )

    # 3. Check virus scan status (block infected files)
    if attachment.scan_result == "infected":
        logger.warning(f"Attempted download of infected file: attachment={attachment_id}, user={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This file has been flagged as potentially unsafe and cannot be downloaded",
        )

    # 4. Generate presigned URL (expires in 1 hour)
    try:
        download_url = generate_presigned_url(attachment.file_key, expiry_seconds=3600)

        logger.info(
            f"Presigned URL generated: attachment={attachment_id}, "
            f"user={current_user.id}, filename={attachment.original_filename}"
        )

        return {
            "download_url": download_url,
            "filename": attachment.original_filename,
            "size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "expires_in_seconds": 3600,
        }

    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate download link"
        )


@router.get("/unread/count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """
    Get total unread message count for current user.

    **Returns:**
    - Total unread count (all threads)
    - Unread count per sender

    **Use Cases:**
    - Notification badge count
    - Unread indicator
    - Per-thread unread counts
    """
    try:
        total = service.get_unread_count(current_user.id)
        by_sender = service.get_unread_count_by_thread(current_user.id)

        return UnreadCountResponse(
            total=total,
            by_sender=by_sender,
        )
    except Exception as e:
        logger.error(f"Error fetching unread count: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count",
        )


@router.get("/users/{user_id}", response_model=UserBasicInfoResponse)
async def get_user_basic_info(
    user_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Get basic user information for messaging purposes.

    **Returns:**
    - User's ID, email, first name, last name, and role

    **Use Cases:**
    - Display user information when starting a new conversation
    - Show user details in message threads

    **Security:**
    - Only authenticated users can access this endpoint
    - Returns basic public information only
    """
    try:
        from models import User

        user = get_or_404(db, User, {"id": user_id, "is_active": True}, detail="User not found")

        avatar_key = getattr(user, "avatar_key", None)
        return UserBasicInfoResponse(
            id=user.id,
            email=user.email,
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            avatar_url=build_avatar_url(avatar_key),
            role=user.role,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )


# ============================================================================
# Edit & Delete Operations
# ============================================================================


@router.patch("/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: int,
    request: EditMessageRequest,
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """
    Edit a message (sender only, within 15 minutes).

    **Business Rules:**
    - Only sender can edit their own messages
    - Must be within 15 minutes of sending
    - PII protection still applies to edited content
    - Sets is_edited flag and edited_at timestamp

    **Use Cases:**
    - Fix typos
    - Clarify message
    - Update information
    """
    try:
        message = await run_in_threadpool(
            service.edit_message,
            message_id=message_id,
            user_id=current_user.id,
            new_content=request.message,
        )

        # Notify recipient of edit via WebSocket
        await manager.send_personal_message(
            {
                "type": "message_edited",
                "message_id": message.id,
                "new_content": message.message,
                "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                "is_edited": message.is_edited,
            },
            message.recipient_id,
        )

        return message

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit message",
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """
    Delete a message (sender only, soft delete).

    **Business Rules:**
    - Only sender can delete their own messages
    - Soft delete (kept for audit trail)
    - Sets deleted_at and deleted_by fields
    - Message hidden from both sender and recipient

    **Use Cases:**
    - Remove inappropriate content
    - Delete sent by mistake
    - Clean up conversation
    """
    try:
        message = await run_in_threadpool(service.delete_message, message_id, current_user.id)

        # Notify recipient of deletion via WebSocket
        await manager.send_personal_message(
            {
                "type": "message_deleted",
                "message_id": message_id,
                "deleted_by": current_user.id,
            },
            message.recipient_id,
        )

        return None

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message",
        )
