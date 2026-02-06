"""
Domain entities for messages module.

These are pure data classes representing the core messaging domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import datetime

from modules.messages.domain.value_objects import AttachmentInfo


@dataclass
class MessageEntity:
    """
    Core message domain entity.

    Represents a single message in a conversation between two users.

    Attributes:
        id: Unique message identifier (None for new messages)
        conversation_id: ID of the conversation this message belongs to
        sender_id: User ID of the message sender
        content: Message text content (1-2000 characters)
        created_at: Timestamp when message was created
        read_at: Timestamp when message was read by recipient (None if unread)
        attachment_url: URL to message attachment (if any)
        is_system_message: Whether this is a system-generated message
        is_edited: Whether the message has been edited
        edited_at: Timestamp of last edit (None if never edited)
        deleted_at: Timestamp of soft delete (None if not deleted)
    """

    id: int | None
    conversation_id: int
    sender_id: int
    content: str

    # Timestamps
    created_at: datetime | None = None
    read_at: datetime | None = None
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

    # Optional attachment
    attachment_url: str | None = None

    # Flags
    is_system_message: bool = False
    is_edited: bool = False

    # Recipient for direct message queries (legacy support)
    recipient_id: int | None = None

    # Booking context (optional)
    booking_id: int | None = None

    @property
    def is_read(self) -> bool:
        """Check if message has been read."""
        return self.read_at is not None

    @property
    def is_deleted(self) -> bool:
        """Check if message has been soft deleted."""
        return self.deleted_at is not None

    @property
    def has_attachment(self) -> bool:
        """Check if message has an attachment."""
        return self.attachment_url is not None

    def can_be_edited_by(self, user_id: int, edit_window_minutes: int = 15) -> bool:
        """
        Check if message can be edited by the given user.

        Args:
            user_id: User attempting to edit
            edit_window_minutes: Maximum time after creation to allow edits

        Returns:
            True if user can edit, False otherwise
        """
        if self.sender_id != user_id:
            return False
        if self.is_deleted:
            return False
        if self.is_system_message:
            return False
        if self.created_at is None:
            return False

        from datetime import UTC, timedelta

        now = datetime.now(UTC)
        created = self.created_at.replace(tzinfo=UTC) if self.created_at.tzinfo is None else self.created_at
        time_since_created = now - created

        return time_since_created <= timedelta(minutes=edit_window_minutes)

    def can_be_deleted_by(self, user_id: int) -> bool:
        """
        Check if message can be deleted by the given user.

        Args:
            user_id: User attempting to delete

        Returns:
            True if user can delete, False otherwise
        """
        return self.sender_id == user_id and not self.is_deleted


@dataclass
class ConversationEntity:
    """
    Conversation domain entity.

    Represents a conversation thread between a student and tutor.

    Attributes:
        id: Unique conversation identifier (None for new conversations)
        student_id: User ID of the student participant
        tutor_id: User ID of the tutor participant
        last_message_at: Timestamp of the most recent message
        student_unread_count: Number of unread messages for student
        tutor_unread_count: Number of unread messages for tutor
        created_at: Timestamp when conversation was created
        booking_id: Associated booking ID (optional, for booking-specific conversations)
    """

    id: int | None
    student_id: int
    tutor_id: int

    # Activity tracking
    last_message_at: datetime | None = None
    student_unread_count: int = 0
    tutor_unread_count: int = 0

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Optional booking context
    booking_id: int | None = None

    @property
    def participant_ids(self) -> tuple[int, int]:
        """Get both participant IDs as a tuple."""
        return (self.student_id, self.tutor_id)

    def includes_user(self, user_id: int) -> bool:
        """Check if user is a participant in this conversation."""
        return user_id in (self.student_id, self.tutor_id)

    def get_other_participant_id(self, user_id: int) -> int | None:
        """
        Get the ID of the other participant.

        Args:
            user_id: Current user's ID

        Returns:
            ID of the other participant, or None if user is not a participant
        """
        if user_id == self.student_id:
            return self.tutor_id
        elif user_id == self.tutor_id:
            return self.student_id
        return None

    def get_unread_count_for_user(self, user_id: int) -> int:
        """
        Get unread count for a specific user.

        Args:
            user_id: User to get unread count for

        Returns:
            Unread count for that user, or 0 if not a participant
        """
        if user_id == self.student_id:
            return self.student_unread_count
        elif user_id == self.tutor_id:
            return self.tutor_unread_count
        return 0

    def is_student(self, user_id: int) -> bool:
        """Check if the user is the student in this conversation."""
        return user_id == self.student_id

    def is_tutor(self, user_id: int) -> bool:
        """Check if the user is the tutor in this conversation."""
        return user_id == self.tutor_id


@dataclass
class MessageAttachmentEntity:
    """
    Message attachment domain entity.

    Represents a file attached to a message.

    Attributes:
        id: Unique attachment identifier
        message_id: ID of the message this attachment belongs to
        uploaded_by: User ID who uploaded the attachment
        file_key: Storage key/path for the file
        original_filename: Original filename from upload
        file_size: Size in bytes
        mime_type: MIME type of the file
        scan_result: Virus scan result (pending, clean, infected)
        is_public: Whether attachment is publicly accessible
        created_at: Upload timestamp
    """

    id: int | None
    message_id: int
    uploaded_by: int
    file_key: str
    original_filename: str
    file_size: int
    mime_type: str

    # Security
    scan_result: str = "pending"
    is_public: bool = False

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_safe(self) -> bool:
        """Check if attachment has passed virus scan."""
        return self.scan_result == "clean"

    @property
    def is_infected(self) -> bool:
        """Check if attachment failed virus scan."""
        return self.scan_result == "infected"

    @property
    def is_pending_scan(self) -> bool:
        """Check if attachment is awaiting virus scan."""
        return self.scan_result == "pending"

    def to_attachment_info(self, url: str) -> AttachmentInfo:
        """
        Convert to AttachmentInfo value object.

        Args:
            url: Presigned URL for the attachment

        Returns:
            AttachmentInfo value object
        """
        return AttachmentInfo(
            filename=self.original_filename,
            url=url,
            size_bytes=self.file_size,
            mime_type=self.mime_type,
        )
