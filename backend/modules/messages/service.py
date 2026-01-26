"""
Messaging Service - DDD + KISS Architecture
Domain service for messaging with clean business logic.

Principles:
- Single Responsibility: Handle messaging domain logic only
- Clear Boundaries: Well-defined inputs/outputs
- Business Rules: Encoded in domain methods
- No External Dependencies: Only database access
"""

import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from core.exceptions import ValidationError
from models import Booking, Message, User

logger = logging.getLogger(__name__)


class MessageService:
    """
    Domain service for messaging operations.

    Core Responsibilities:
    1. Message Lifecycle: Send, edit, delete
    2. Conversation Management: Threads, history
    3. Read Receipts: Track message status
    4. PII Protection: Mask sensitive data pre-booking
    5. Content Safety: Sanitize and validate

    Business Rules:
    - Edit window: 15 minutes
    - Soft delete: Keep for audit
    - PII masking: Pre-booking only
    - Message length: 1-2000 chars
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    # ========================================================================
    # Core Messaging Operations
    # ========================================================================

    def send_message(
        self,
        sender_id: int,
        recipient_id: int,
        content: str,
        booking_id: int | None = None,
    ) -> Message:
        """
        Send a message from sender to recipient.

        Args:
            sender_id: ID of the message sender
            recipient_id: ID of the message recipient
            content: Message text content
            booking_id: Optional booking context

        Returns:
            Created Message object

        Raises:
            ValidationError: If validation fails

        Business Rules:
        - Cannot message yourself
        - Recipient must exist and be active
        - Content: 1-2000 characters after sanitization
        - PII masked in pre-booking conversations
        - All content sanitized for safety
        """
        # 1. Validate sender != recipient
        if sender_id == recipient_id:
            logger.warning(f"User {sender_id} attempted to message themselves")
            raise ValidationError("Cannot send message to yourself")

        # 2. Validate recipient exists and is active
        recipient = self.db.query(User).filter(User.id == recipient_id, User.is_active.is_(True)).first()
        if not recipient:
            logger.warning(f"Invalid recipient {recipient_id} for sender {sender_id}")
            raise ValidationError("Recipient not found or inactive")

        # 3. Sanitize and validate content
        content = self._sanitize_content(content)
        if not content or not content.strip():
            raise ValidationError("Message cannot be empty")
        if len(content) > 2000:
            raise ValidationError(f"Message too long ({len(content)}/2000 characters)")

        # 4. Apply PII protection if needed
        should_mask_pii = self._is_pre_booking_conversation(sender_id, recipient_id, booking_id)
        if should_mask_pii:
            content = self._mask_pii(content)
            logger.debug(f"PII masked for message from {sender_id} to {recipient_id}")

        # 5. Create and persist message
        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            booking_id=booking_id,
            message=content,
            is_read=False,
        )

        try:
            # Set updated_at explicitly (no DB triggers - all logic in code)
            from datetime import datetime

            message.updated_at = datetime.now(UTC)

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            logger.info(
                f"Message created: id={message.id}, "
                f"sender={sender_id}, recipient={recipient_id}, "
                f"booking={booking_id}, pii_masked={should_mask_pii}"
            )
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Database error saving message: {e}", exc_info=True)
            # Return more specific error message for debugging
            error_type = type(e).__name__
            raise ValidationError(f"Database error: {error_type} - {str(e)}") from e

    def get_conversation_messages(
        self,
        user1_id: int,
        user2_id: int,
        booking_id: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Message], int]:
        """
        Get messages between two users with pagination.

        Returns: (messages, total_count)
        """
        page_size = min(page_size, 100)  # Max 100 per page
        offset = (page - 1) * page_size

        # Base query
        query = self.db.query(Message).filter(
            Message.deleted_at.is_(None),
            or_(
                and_(
                    Message.sender_id == user1_id,
                    Message.recipient_id == user2_id,
                ),
                and_(
                    Message.sender_id == user2_id,
                    Message.recipient_id == user1_id,
                ),
            ),
        )

        if booking_id is not None:
            query = query.filter(Message.booking_id == booking_id)

        # Get total count
        total = query.count()

        # Get paginated messages
        messages = query.order_by(Message.created_at.desc()).offset(offset).limit(page_size).all()

        # Return in chronological order (oldest first)
        return list(reversed(messages)), total

    def get_user_threads(self, user_id: int, limit: int = 100) -> list[dict]:
        """
        Get all conversation threads for a user.

        Args:
            user_id: User ID to get threads for
            limit: Maximum number of threads (default: 100)

        Returns:
            List of thread dictionaries with:
            - other_user_id: Conversation partner ID
            - other_user_email: Partner's email
            - other_user_role: Partner's role (student/tutor/admin)
            - booking_id: Optional booking context
            - last_message: Last message text
            - last_message_time: Timestamp of last message
            - last_sender_id: Who sent the last message
            - unread_count: Number of unread messages in thread

        Note:
            Threads are sorted by most recent activity (last_message_time DESC)
        """
        try:
            # Subquery: Find latest message per conversation thread
            latest_msg_subquery = (
                self.db.query(
                    case(
                        (Message.sender_id == user_id, Message.recipient_id),
                        else_=Message.sender_id,
                    ).label("other_user_id"),
                    Message.booking_id,
                    func.max(Message.created_at).label("last_time"),
                )
                .filter(
                    Message.deleted_at.is_(None),
                    or_(
                        Message.sender_id == user_id,
                        Message.recipient_id == user_id,
                    ),
                )
                .group_by("other_user_id", Message.booking_id)  # Don't group by sender_id
                .subquery()
            )

            # Main query: Get thread details with latest message
            # Select User object directly for reliable attribute access
            threads_query = (
                self.db.query(
                    latest_msg_subquery.c.other_user_id,
                    User,  # Select entire User object
                    latest_msg_subquery.c.booking_id,
                    Message.sender_id,
                    Message.message,
                    latest_msg_subquery.c.last_time,
                )
                .select_from(latest_msg_subquery)
                .join(User, User.id == latest_msg_subquery.c.other_user_id)
                .join(
                    Message,
                    and_(
                        Message.created_at == latest_msg_subquery.c.last_time,
                        Message.deleted_at.is_(None),
                        or_(
                            and_(
                                Message.sender_id == user_id,
                                Message.recipient_id == latest_msg_subquery.c.other_user_id,
                            ),
                            and_(
                                Message.sender_id == latest_msg_subquery.c.other_user_id,
                                Message.recipient_id == user_id,
                            ),
                        ),
                        or_(
                            Message.booking_id == latest_msg_subquery.c.booking_id,
                            and_(
                                latest_msg_subquery.c.booking_id.is_(None),
                                Message.booking_id.is_(None),
                            ),
                        ),
                    ),
                )
                .order_by(latest_msg_subquery.c.last_time.desc())
                .limit(limit)
                .all()
            )

            # Calculate unread count per thread separately (more accurate)
            threads = []
            for t in threads_query:
                # t[0] = other_user_id, t[2] = booking_id
                booking_id = t[2]
                unread_count = (
                    self.db.query(func.count(Message.id))
                    .filter(
                        Message.deleted_at.is_(None),
                        Message.recipient_id == user_id,
                        Message.sender_id == t[0],  # other_user_id
                        Message.is_read.is_(False),
                        or_(
                            Message.booking_id == booking_id,
                            and_(
                                booking_id.is_(None) if booking_id is None else False,
                                Message.booking_id.is_(None),
                            ),
                        )
                        if booking_id is not None
                        else Message.booking_id.is_(None),
                    )
                    .scalar()
                ) or 0

                # Access by index with User object
                # Query columns order: other_user_id, User, booking_id, sender_id, message, last_time
                user_obj = t[1]  # User object
                threads.append(
                    {
                        "other_user_id": t[0],  # other_user_id
                        "other_user_email": user_obj.email,
                        "other_user_first_name": user_obj.first_name,
                        "other_user_last_name": user_obj.last_name,
                        "other_user_avatar_url": getattr(user_obj, "avatar_url", None),
                        "other_user_role": user_obj.role,
                        "booking_id": t[2],  # booking_id
                        "last_sender_id": t[3],  # sender_id
                        "last_message": t[4],  # message
                        "last_message_time": t[5],  # last_time
                        "unread_count": unread_count,
                    }
                )

            logger.debug(f"Retrieved {len(threads)} threads for user {user_id}")
            return threads

        except Exception as e:
            logger.error(f"Failed to get threads for user {user_id}: {e}", exc_info=True)
            raise ValidationError("Failed to load conversation threads") from e

    def search_messages(
        self,
        user_id: int,
        search_query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Message], int]:
        """
        Search user's messages by content.

        Returns: (messages, total_count)
        """
        search_query = search_query.strip()
        if not search_query or len(search_query) < 2:
            raise ValidationError("Search query must be at least 2 characters")

        page_size = min(page_size, 50)
        offset = (page - 1) * page_size

        # Search pattern
        search_pattern = f"%{search_query}%"

        # Base query
        query = self.db.query(Message).filter(
            Message.deleted_at.is_(None),
            or_(
                Message.sender_id == user_id,
                Message.recipient_id == user_id,
            ),
            Message.message.ilike(search_pattern),
        )

        total = query.count()

        messages = query.order_by(Message.created_at.desc()).offset(offset).limit(page_size).all()

        return messages, total

    # ========================================================================
    # Read Receipts
    # ========================================================================

    def mark_message_read(self, message_id: int, user_id: int) -> Message:
        """Mark a message as read (recipient only)."""
        message = (
            self.db.query(Message)
            .filter(
                Message.id == message_id,
                Message.recipient_id == user_id,
                Message.deleted_at.is_(None),
            )
            .first()
        )

        if not message:
            raise ValidationError("Message not found or not authorized")

        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.now(UTC)
            message.updated_at = datetime.now(UTC)  # Update timestamp in code
            self.db.commit()
            self.db.refresh(message)

        return message

    def mark_thread_read(self, user_id: int, other_user_id: int, booking_id: int | None = None) -> int:
        """Mark all messages in a thread as read."""
        query = self.db.query(Message).filter(
            Message.deleted_at.is_(None),
            Message.sender_id == other_user_id,
            Message.recipient_id == user_id,
            Message.is_read.is_(False),
        )

        if booking_id is not None:
            query = query.filter(Message.booking_id == booking_id)

        now = datetime.now(UTC)
        count = query.update(
            {"is_read": True, "read_at": now, "updated_at": now},  # Update timestamp in code
            synchronize_session=False,
        )
        self.db.commit()

        logger.info(f"Marked {count} messages as read in thread for user {user_id}")
        return count

    def get_unread_count(self, user_id: int) -> int:
        """Get total unread message count for user."""
        return (
            self.db.query(Message)
            .filter(
                Message.recipient_id == user_id,
                Message.is_read.is_(False),
                Message.deleted_at.is_(None),
            )
            .count()
        )

    def get_unread_count_by_thread(self, user_id: int) -> dict:
        """Get unread counts grouped by sender."""
        results = (
            self.db.query(
                Message.sender_id,
                func.count(Message.id).label("count"),
            )
            .filter(
                Message.recipient_id == user_id,
                Message.is_read.is_(False),
                Message.deleted_at.is_(None),
            )
            .group_by(Message.sender_id)
            .all()
        )

        return dict(results)

    # ========================================================================
    # Edit & Delete
    # ========================================================================

    def edit_message(self, message_id: int, user_id: int, new_content: str) -> Message:
        """
        Edit a message (sender only, within 15 minutes).

        Business Rules:
        - Only sender can edit
        - Must be within 15 minutes of sending
        - Cannot edit deleted messages
        - PII protection still applies
        """
        message = (
            self.db.query(Message)
            .filter(
                Message.id == message_id,
                Message.sender_id == user_id,
                Message.deleted_at.is_(None),
            )
            .first()
        )

        if not message:
            raise ValidationError("Message not found or not authorized")

        # Check 15-minute window
        time_since_sent = datetime.now(UTC) - message.created_at.replace(tzinfo=UTC)
        if time_since_sent > timedelta(minutes=15):
            raise ValidationError("Cannot edit messages older than 15 minutes")

        # Sanitize and validate new content
        new_content = self._sanitize_content(new_content)
        if not new_content:
            raise ValidationError("Message cannot be empty")
        if len(new_content) > 2000:
            raise ValidationError("Message too long (max 2000 characters)")

        # Apply PII protection
        if self._is_pre_booking_conversation(message.sender_id, message.recipient_id, message.booking_id):
            new_content = self._mask_pii(new_content)

        message.message = new_content
        message.is_edited = True
        message.edited_at = datetime.now(UTC)
        message.updated_at = datetime.now(UTC)  # Update timestamp in code
        self.db.commit()
        self.db.refresh(message)

        logger.info(f"Message {message_id} edited by user {user_id}")
        return message

    def delete_message(self, message_id: int, user_id: int) -> Message:
        """
        Soft-delete a message (sender only).

        Business Rules:
        - Only sender can delete
        - Soft delete (keep for audit)
        """
        message = (
            self.db.query(Message)
            .filter(
                Message.id == message_id,
                Message.sender_id == user_id,
                Message.deleted_at.is_(None),
            )
            .first()
        )

        if not message:
            raise ValidationError("Message not found or not authorized")

        message.deleted_at = datetime.now(UTC)
        message.deleted_by = user_id
        message.updated_at = datetime.now(UTC)  # Update timestamp in code
        self.db.commit()
        self.db.refresh(message)

        logger.info(f"Message {message_id} deleted by user {user_id}")
        return message

    # ========================================================================
    # Helper Methods - Content Safety & PII Protection
    # ========================================================================

    def _sanitize_content(self, content: str) -> str:
        """Basic content sanitization and normalization."""
        if not content:
            return ""

        # Strip whitespace
        content = content.strip()

        # Remove null bytes and control characters
        content = content.replace("\x00", "")
        content = "".join(char for char in content if ord(char) >= 32 or char in "\n\r\t")

        # Normalize whitespace
        content = " ".join(content.split())

        return content

    def _is_pre_booking_conversation(self, user1_id: int, user2_id: int, booking_id: int | None) -> bool:
        """
        Determine if conversation requires PII protection.

        Pre-booking = no booking OR booking is still PENDING
        Post-booking = CONFIRMED, COMPLETED, or later states
        """
        if not booking_id:
            return True

        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return True

        # Allow contact info only after booking is confirmed
        safe_statuses = ["confirmed", "completed", "no_show_student", "no_show_tutor"]
        return booking.status.lower() not in safe_statuses

    def _mask_pii(self, content: str) -> str:
        """
        Mask PII (Personal Identifiable Information) in messages.

        Masks:
        - Email addresses
        - Phone numbers (various formats)
        - External URLs
        - Social media handles
        - Messaging app mentions
        """
        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        content = re.sub(email_pattern, "***@***.***", content)

        # Phone patterns (international + various formats)
        phone_patterns = [
            r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",  # Standard
            r"\d{10,}",  # Long digit sequences
            r"(\+\d{1,3}[\s-]?)?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,9}",  # International
        ]
        for pattern in phone_patterns:
            content = re.sub(pattern, "***-***-****", content, flags=re.IGNORECASE)

        # URL pattern (external links)
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        content = re.sub(url_pattern, "[link removed]", content)

        # Domain pattern (website mentions without http)
        domain_pattern = r"\b(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\b"
        content = re.sub(domain_pattern, "[website removed]", content)

        # Social media handles (@username)
        content = re.sub(r"@\w{3,}", "@***", content)

        # Messaging apps (case-insensitive)
        messaging_apps = [
            "whatsapp",
            "telegram",
            "signal",
            "wechat",
            "line",
            "viber",
            "skype",
            "discord",
            "snapchat",
            "facebook messenger",
            "instagram",
        ]
        for app in messaging_apps:
            # Match app name followed by optional colon/dash and contact info
            pattern = rf"\b{app}\b\s*[:\-]?\s*\S+"
            content = re.sub(pattern, f"[{app.title()} contact hidden]", content, flags=re.IGNORECASE)

        return content
