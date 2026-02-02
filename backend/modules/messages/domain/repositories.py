"""
Repository interfaces for messages module.

Defines the contracts for message and conversation persistence operations.
"""

from datetime import datetime
from typing import Protocol

from modules.messages.domain.entities import (
    ConversationEntity,
    MessageAttachmentEntity,
    MessageEntity,
)


class MessageRepository(Protocol):
    """
    Protocol for message repository operations.

    Implementations should handle:
    - Message CRUD operations
    - Conversation-based queries
    - Soft delete handling
    """

    def get_by_id(self, message_id: int) -> MessageEntity | None:
        """
        Get a message by its ID.

        Args:
            message_id: Message's unique identifier

        Returns:
            MessageEntity if found, None otherwise
        """
        ...

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
        ...

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
        ...

    def create(self, message: MessageEntity) -> MessageEntity:
        """
        Create a new message.

        Args:
            message: Message entity to create

        Returns:
            Created message with populated ID and timestamps
        """
        ...

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
        ...

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
        ...

    def update(self, message: MessageEntity) -> MessageEntity:
        """
        Update an existing message.

        Args:
            message: Message entity with updated fields

        Returns:
            Updated message entity
        """
        ...

    def delete(self, message_id: int, deleted_by: int) -> bool:
        """
        Soft delete a message.

        Args:
            message_id: Message ID to delete
            deleted_by: User ID performing the deletion

        Returns:
            True if deleted, False if not found
        """
        ...

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
        ...

    def get_unread_count(self, user_id: int) -> int:
        """
        Get total unread message count for a user.

        Args:
            user_id: User to count unread messages for

        Returns:
            Total unread count
        """
        ...

    def get_unread_count_by_sender(self, user_id: int) -> dict[int, int]:
        """
        Get unread counts grouped by sender.

        Args:
            user_id: User to count unread messages for

        Returns:
            Dictionary mapping sender_id to unread count
        """
        ...


class ConversationRepository(Protocol):
    """
    Protocol for conversation repository operations.

    Implementations should handle:
    - Conversation CRUD operations
    - Participant-based queries
    - Unread count management
    """

    def get_by_id(self, conversation_id: int) -> ConversationEntity | None:
        """
        Get a conversation by its ID.

        Args:
            conversation_id: Conversation's unique identifier

        Returns:
            ConversationEntity if found, None otherwise
        """
        ...

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
        ...

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
        ...

    def create(self, conversation: ConversationEntity) -> ConversationEntity:
        """
        Create a new conversation.

        Args:
            conversation: Conversation entity to create

        Returns:
            Created conversation with populated ID and timestamps
        """
        ...

    def update(self, conversation: ConversationEntity) -> ConversationEntity:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation entity with updated fields

        Returns:
            Updated conversation entity
        """
        ...

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
        ...

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
        ...

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
        ...

    def get_total_unread_count(self, user_id: int) -> int:
        """
        Get total unread messages across all conversations for a user.

        Args:
            user_id: User to count for

        Returns:
            Total unread count
        """
        ...


class MessageAttachmentRepository(Protocol):
    """
    Protocol for message attachment repository operations.

    Implementations should handle:
    - Attachment CRUD operations
    - File metadata management
    - Scan result updates
    """

    def get_by_id(self, attachment_id: int) -> MessageAttachmentEntity | None:
        """
        Get an attachment by its ID.

        Args:
            attachment_id: Attachment's unique identifier

        Returns:
            MessageAttachmentEntity if found, None otherwise
        """
        ...

    def get_by_message(self, message_id: int) -> list[MessageAttachmentEntity]:
        """
        Get all attachments for a message.

        Args:
            message_id: Message ID

        Returns:
            List of attachments for the message
        """
        ...

    def create(self, attachment: MessageAttachmentEntity) -> MessageAttachmentEntity:
        """
        Create a new attachment record.

        Args:
            attachment: Attachment entity to create

        Returns:
            Created attachment with populated ID and timestamps
        """
        ...

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
        ...

    def delete(self, attachment_id: int) -> bool:
        """
        Delete an attachment record.

        Args:
            attachment_id: Attachment ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...
