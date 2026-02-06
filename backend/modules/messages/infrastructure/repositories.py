"""
SQLAlchemy repository implementations for messages module.

Provides concrete implementations of the MessageRepository,
ConversationRepository, and MessageAttachmentRepository protocols.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from models.messages import Conversation, Message, MessageAttachment
from modules.messages.domain.entities import (
    ConversationEntity,
    MessageAttachmentEntity,
    MessageEntity,
)
from modules.messages.domain.repositories import (
    ConversationRepository,
    MessageAttachmentRepository,
    MessageRepository,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageRepositoryImpl(MessageRepository):
    """
    SQLAlchemy implementation of MessageRepository.

    Handles all message persistence operations with soft delete support.
    """

    db: Session

    def get_by_id(self, message_id: int) -> MessageEntity | None:
        """
        Get a message by its ID.

        Args:
            message_id: Message's unique identifier

        Returns:
            MessageEntity if found, None otherwise
        """
        message = (
            self.db.query(Message)
            .filter(
                Message.id == message_id,
                Message.deleted_at.is_(None),
            )
            .first()
        )
        if not message:
            return None
        return self._to_entity(message)

    def get_by_conversation(
        self,
        conversation_id: int,
        *,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
    ) -> tuple[list[MessageEntity], int]:
        """
        Get messages in a conversation with pagination.

        Args:
            conversation_id: Conversation ID
            page: Page number (1-indexed)
            page_size: Items per page
            include_deleted: Whether to include soft-deleted messages

        Returns:
            Tuple of (messages list, total count)
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )

        if not include_deleted:
            query = query.filter(Message.deleted_at.is_(None))

        total = query.count()

        offset = (page - 1) * page_size
        messages = (
            query.order_by(Message.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_entity(m) for m in messages], total

    def get_by_participants(
        self,
        user1_id: int,
        user2_id: int,
        *,
        booking_id: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[MessageEntity], int]:
        """
        Get messages between two users (legacy sender/recipient model).

        Args:
            user1_id: First user ID
            user2_id: Second user ID
            booking_id: Optional booking context filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (messages list, total count)
        """
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

        total = query.count()

        offset = (page - 1) * page_size
        messages = (
            query.order_by(Message.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_entity(m) for m in messages], total

    def create(self, message: MessageEntity) -> MessageEntity:
        """
        Create a new message.

        Args:
            message: Message entity to create

        Returns:
            Created message with populated ID and timestamps
        """
        now = datetime.now(UTC)
        model = self._to_model(message)
        model.created_at = now
        model.updated_at = now

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(
            f"Message created: id={model.id}, "
            f"conversation_id={model.conversation_id}, "
            f"sender_id={model.sender_id}"
        )

        return self._to_entity(model)

    def mark_as_read(
        self,
        message_id: int,
        user_id: int,
        read_at: datetime | None = None,
    ) -> MessageEntity | None:
        """
        Mark a message as read.

        Args:
            message_id: Message to mark as read
            user_id: User marking the message (must be recipient)
            read_at: Read timestamp (defaults to now)

        Returns:
            Updated message, or None if not found/not authorized
        """
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
            return None

        if not message.is_read:
            message.is_read = True
            message.read_at = read_at or datetime.now(UTC)
            message.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(message)

        return self._to_entity(message)

    def mark_conversation_as_read(
        self,
        user_id: int,
        other_user_id: int,
        *,
        booking_id: int | None = None,
    ) -> int:
        """
        Mark all messages in a conversation as read.

        Args:
            user_id: User marking messages as read
            other_user_id: Other participant in conversation
            booking_id: Optional booking context filter

        Returns:
            Number of messages marked as read
        """
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
            {"is_read": True, "read_at": now, "updated_at": now},
            synchronize_session=False,
        )
        self.db.commit()

        logger.info(
            f"Marked {count} messages as read for user {user_id} "
            f"from sender {other_user_id}"
        )

        return count

    def update(self, message: MessageEntity) -> MessageEntity:
        """
        Update an existing message.

        Args:
            message: Message entity with updated fields

        Returns:
            Updated message entity
        """
        if message.id is None:
            raise ValueError("Cannot update message without ID")

        model = (
            self.db.query(Message)
            .filter(
                Message.id == message.id,
                Message.deleted_at.is_(None),
            )
            .first()
        )

        if not model:
            raise ValueError(f"Message with ID {message.id} not found")

        now = datetime.now(UTC)
        model.message = message.content
        model.is_read = message.is_read
        model.read_at = message.read_at
        model.is_edited = message.is_edited
        model.edited_at = message.edited_at
        model.is_system_message = message.is_system_message
        model.attachment_url = message.attachment_url
        model.updated_at = now

        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def delete(self, message_id: int, deleted_by: int) -> bool:
        """
        Soft delete a message.

        Args:
            message_id: Message ID to delete
            deleted_by: User ID performing the deletion

        Returns:
            True if deleted, False if not found
        """
        message = (
            self.db.query(Message)
            .filter(
                Message.id == message_id,
                Message.deleted_at.is_(None),
            )
            .first()
        )

        if not message:
            return False

        now = datetime.now(UTC)
        message.deleted_at = now
        message.deleted_by = deleted_by
        message.updated_at = now
        self.db.commit()

        logger.info(f"Message {message_id} soft-deleted by user {deleted_by}")

        return True

    def search(
        self,
        user_id: int,
        query: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[MessageEntity], int]:
        """
        Search messages by content for a user.

        Args:
            user_id: User to search messages for
            query: Search query string
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (matching messages, total count)
        """
        search_pattern = f"%{query}%"

        base_query = self.db.query(Message).filter(
            Message.deleted_at.is_(None),
            or_(
                Message.sender_id == user_id,
                Message.recipient_id == user_id,
            ),
            Message.message.ilike(search_pattern),
        )

        total = base_query.count()

        offset = (page - 1) * page_size
        messages = (
            base_query.order_by(Message.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_entity(m) for m in messages], total

    def get_unread_count(self, user_id: int) -> int:
        """
        Get total unread message count for a user.

        Args:
            user_id: User to count unread messages for

        Returns:
            Total unread count
        """
        return (
            self.db.query(Message)
            .filter(
                Message.recipient_id == user_id,
                Message.is_read.is_(False),
                Message.deleted_at.is_(None),
            )
            .count()
        )

    def get_unread_count_by_sender(self, user_id: int) -> dict[int, int]:
        """
        Get unread counts grouped by sender.

        Args:
            user_id: User to count unread messages for

        Returns:
            Dictionary mapping sender_id to unread count
        """
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

    def _to_entity(self, model: Message) -> MessageEntity:
        """Convert SQLAlchemy model to domain entity."""
        return MessageEntity(
            id=model.id,
            conversation_id=model.conversation_id or 0,
            sender_id=model.sender_id or 0,
            content=model.message,
            created_at=model.created_at,
            read_at=model.read_at,
            edited_at=model.edited_at,
            deleted_at=model.deleted_at,
            attachment_url=model.attachment_url,
            is_system_message=model.is_system_message or False,
            is_edited=model.is_edited or False,
            recipient_id=model.recipient_id,
            booking_id=model.booking_id,
        )

    def _to_model(self, entity: MessageEntity) -> Message:
        """Convert domain entity to SQLAlchemy model for creation."""
        model = Message(
            conversation_id=entity.conversation_id if entity.conversation_id else None,
            sender_id=entity.sender_id,
            recipient_id=entity.recipient_id,
            booking_id=entity.booking_id,
            message=entity.content,
            is_system_message=entity.is_system_message,
            is_read=entity.is_read,
            read_at=entity.read_at,
            is_edited=entity.is_edited,
            edited_at=entity.edited_at,
            attachment_url=entity.attachment_url,
        )

        if entity.id is not None:
            model.id = entity.id

        return model


@dataclass(slots=True)
class ConversationRepositoryImpl(ConversationRepository):
    """
    SQLAlchemy implementation of ConversationRepository.

    Handles all conversation persistence operations.
    """

    db: Session

    def get_by_id(self, conversation_id: int) -> ConversationEntity | None:
        """
        Get a conversation by its ID.

        Args:
            conversation_id: Conversation's unique identifier

        Returns:
            ConversationEntity if found, None otherwise
        """
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return None
        return self._to_entity(conversation)

    def get_by_participants(
        self,
        student_id: int,
        tutor_id: int,
        *,
        booking_id: int | None = None,
    ) -> ConversationEntity | None:
        """
        Get a conversation between two specific participants.

        Args:
            student_id: Student user ID
            tutor_id: Tutor user ID
            booking_id: Optional booking context

        Returns:
            ConversationEntity if found, None otherwise
        """
        query = self.db.query(Conversation).filter(
            Conversation.student_id == student_id,
            Conversation.tutor_id == tutor_id,
        )

        if booking_id is not None:
            query = query.filter(Conversation.booking_id == booking_id)
        else:
            query = query.filter(Conversation.booking_id.is_(None))

        conversation = query.first()
        if not conversation:
            return None
        return self._to_entity(conversation)

    def get_for_user(
        self,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ConversationEntity], int]:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID to get conversations for
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (conversations list, total count)
        """
        query = self.db.query(Conversation).filter(
            or_(
                Conversation.student_id == user_id,
                Conversation.tutor_id == user_id,
            )
        )

        total = query.count()

        offset = (page - 1) * page_size
        conversations = (
            query.order_by(Conversation.last_message_at.desc().nullslast())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_entity(c) for c in conversations], total

    def create(self, conversation: ConversationEntity) -> ConversationEntity:
        """
        Create a new conversation.

        Args:
            conversation: Conversation entity to create

        Returns:
            Created conversation with populated ID and timestamps
        """
        now = datetime.now(UTC)
        model = self._to_model(conversation)
        model.created_at = now
        model.updated_at = now

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(
            f"Conversation created: id={model.id}, "
            f"student_id={model.student_id}, tutor_id={model.tutor_id}"
        )

        return self._to_entity(model)

    def update(self, conversation: ConversationEntity) -> ConversationEntity:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation entity with updated fields

        Returns:
            Updated conversation entity
        """
        if conversation.id is None:
            raise ValueError("Cannot update conversation without ID")

        model = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation.id)
            .first()
        )

        if not model:
            raise ValueError(f"Conversation with ID {conversation.id} not found")

        now = datetime.now(UTC)
        model.last_message_at = conversation.last_message_at
        model.student_unread_count = conversation.student_unread_count
        model.tutor_unread_count = conversation.tutor_unread_count
        model.updated_at = now

        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

    def update_last_message(
        self,
        conversation_id: int,
        last_message_at: datetime,
        increment_unread_for: int | None = None,
    ) -> ConversationEntity | None:
        """
        Update the last message timestamp and optionally increment unread count.

        Args:
            conversation_id: Conversation to update
            last_message_at: Timestamp of the last message
            increment_unread_for: User ID to increment unread count for

        Returns:
            Updated conversation, or None if not found
        """
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return None

        now = datetime.now(UTC)
        conversation.last_message_at = last_message_at
        conversation.updated_at = now

        if increment_unread_for is not None:
            if increment_unread_for == conversation.student_id:
                conversation.student_unread_count += 1
            elif increment_unread_for == conversation.tutor_id:
                conversation.tutor_unread_count += 1

        self.db.commit()
        self.db.refresh(conversation)

        return self._to_entity(conversation)

    def get_or_create(
        self,
        student_id: int,
        tutor_id: int,
        *,
        booking_id: int | None = None,
    ) -> tuple[ConversationEntity, bool]:
        """
        Get existing conversation or create a new one.

        Args:
            student_id: Student user ID
            tutor_id: Tutor user ID
            booking_id: Optional booking context

        Returns:
            Tuple of (conversation, created_flag)
            created_flag is True if new conversation was created
        """
        existing = self.get_by_participants(
            student_id, tutor_id, booking_id=booking_id
        )
        if existing:
            return existing, False

        new_conversation = ConversationEntity(
            id=None,
            student_id=student_id,
            tutor_id=tutor_id,
            booking_id=booking_id,
            student_unread_count=0,
            tutor_unread_count=0,
        )

        created = self.create(new_conversation)
        return created, True

    def reset_unread_count(
        self,
        conversation_id: int,
        user_id: int,
    ) -> bool:
        """
        Reset unread count to zero for a user in a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User to reset count for

        Returns:
            True if updated, False if conversation not found
        """
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return False

        now = datetime.now(UTC)
        if user_id == conversation.student_id:
            conversation.student_unread_count = 0
        elif user_id == conversation.tutor_id:
            conversation.tutor_unread_count = 0
        else:
            return False

        conversation.updated_at = now
        self.db.commit()

        logger.info(
            f"Reset unread count for user {user_id} in conversation {conversation_id}"
        )

        return True

    def get_total_unread_count(self, user_id: int) -> int:
        """
        Get total unread messages across all conversations for a user.

        Args:
            user_id: User to count for

        Returns:
            Total unread count
        """
        student_unread = (
            self.db.query(func.sum(Conversation.student_unread_count))
            .filter(Conversation.student_id == user_id)
            .scalar()
        ) or 0

        tutor_unread = (
            self.db.query(func.sum(Conversation.tutor_unread_count))
            .filter(Conversation.tutor_id == user_id)
            .scalar()
        ) or 0

        return int(student_unread) + int(tutor_unread)

    def _to_entity(self, model: Conversation) -> ConversationEntity:
        """Convert SQLAlchemy model to domain entity."""
        return ConversationEntity(
            id=model.id,
            student_id=model.student_id,
            tutor_id=model.tutor_id,
            last_message_at=model.last_message_at,
            student_unread_count=model.student_unread_count or 0,
            tutor_unread_count=model.tutor_unread_count or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
            booking_id=model.booking_id,
        )

    def _to_model(self, entity: ConversationEntity) -> Conversation:
        """Convert domain entity to SQLAlchemy model for creation."""
        model = Conversation(
            student_id=entity.student_id,
            tutor_id=entity.tutor_id,
            booking_id=entity.booking_id,
            last_message_at=entity.last_message_at,
            student_unread_count=entity.student_unread_count,
            tutor_unread_count=entity.tutor_unread_count,
        )

        if entity.id is not None:
            model.id = entity.id

        return model


@dataclass(slots=True)
class MessageAttachmentRepositoryImpl(MessageAttachmentRepository):
    """
    SQLAlchemy implementation of MessageAttachmentRepository.

    Handles all message attachment persistence operations.
    """

    db: Session

    def get_by_id(self, attachment_id: int) -> MessageAttachmentEntity | None:
        """
        Get an attachment by its ID.

        Args:
            attachment_id: Attachment's unique identifier

        Returns:
            MessageAttachmentEntity if found, None otherwise
        """
        attachment = (
            self.db.query(MessageAttachment)
            .filter(
                MessageAttachment.id == attachment_id,
                MessageAttachment.deleted_at.is_(None),
            )
            .first()
        )
        if not attachment:
            return None
        return self._to_entity(attachment)

    def get_by_message(self, message_id: int) -> list[MessageAttachmentEntity]:
        """
        Get all attachments for a message.

        Args:
            message_id: Message ID

        Returns:
            List of attachments for the message
        """
        attachments = (
            self.db.query(MessageAttachment)
            .filter(
                MessageAttachment.message_id == message_id,
                MessageAttachment.deleted_at.is_(None),
            )
            .order_by(MessageAttachment.created_at.asc())
            .all()
        )

        return [self._to_entity(a) for a in attachments]

    def create(self, attachment: MessageAttachmentEntity) -> MessageAttachmentEntity:
        """
        Create a new attachment record.

        Args:
            attachment: Attachment entity to create

        Returns:
            Created attachment with populated ID and timestamps
        """
        now = datetime.now(UTC)
        model = self._to_model(attachment)
        model.created_at = now
        model.updated_at = now

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(
            f"Attachment created: id={model.id}, "
            f"message_id={model.message_id}, "
            f"filename={model.original_filename}"
        )

        return self._to_entity(model)

    def update_scan_result(
        self,
        attachment_id: int,
        scan_result: str,
    ) -> bool:
        """
        Update the virus scan result for an attachment.

        Args:
            attachment_id: Attachment to update
            scan_result: Scan result (pending, clean, infected)

        Returns:
            True if updated, False if not found
        """
        attachment = (
            self.db.query(MessageAttachment)
            .filter(
                MessageAttachment.id == attachment_id,
                MessageAttachment.deleted_at.is_(None),
            )
            .first()
        )

        if not attachment:
            return False

        now = datetime.now(UTC)
        attachment.scan_result = scan_result
        attachment.is_scanned = True
        attachment.updated_at = now
        self.db.commit()

        logger.info(
            f"Attachment {attachment_id} scan result updated to: {scan_result}"
        )

        return True

    def delete(self, attachment_id: int) -> bool:
        """
        Delete an attachment record (soft delete).

        Args:
            attachment_id: Attachment ID to delete

        Returns:
            True if deleted, False if not found
        """
        attachment = (
            self.db.query(MessageAttachment)
            .filter(
                MessageAttachment.id == attachment_id,
                MessageAttachment.deleted_at.is_(None),
            )
            .first()
        )

        if not attachment:
            return False

        now = datetime.now(UTC)
        attachment.deleted_at = now
        attachment.updated_at = now
        self.db.commit()

        logger.info(f"Attachment {attachment_id} soft-deleted")

        return True

    def _to_entity(self, model: MessageAttachment) -> MessageAttachmentEntity:
        """Convert SQLAlchemy model to domain entity."""
        return MessageAttachmentEntity(
            id=model.id,
            message_id=model.message_id,
            uploaded_by=model.uploaded_by,
            file_key=model.file_key,
            original_filename=model.original_filename,
            file_size=model.file_size,
            mime_type=model.mime_type,
            scan_result=model.scan_result or "pending",
            is_public=model.is_public or False,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: MessageAttachmentEntity) -> MessageAttachment:
        """Convert domain entity to SQLAlchemy model for creation."""
        # Determine file category from mime type
        if entity.mime_type.startswith("image/"):
            file_category = "image"
        elif entity.mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]:
            file_category = "document"
        else:
            file_category = "other"

        model = MessageAttachment(
            message_id=entity.message_id,
            uploaded_by=entity.uploaded_by,
            file_key=entity.file_key,
            original_filename=entity.original_filename,
            file_size=entity.file_size,
            mime_type=entity.mime_type,
            file_category=file_category,
            scan_result=entity.scan_result,
            is_scanned=entity.scan_result != "pending",
            is_public=entity.is_public,
        )

        if entity.id is not None:
            model.id = entity.id

        return model
