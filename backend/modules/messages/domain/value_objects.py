"""
Value objects for messages module.

Immutable value objects representing domain concepts.
"""

from dataclasses import dataclass
from typing import NewType

from modules.messages.domain.exceptions import EmptyMessageError, MessageTooLongError


# Type aliases for IDs
MessageId = NewType("MessageId", int)
ConversationId = NewType("ConversationId", int)
UserId = NewType("UserId", int)
AttachmentId = NewType("AttachmentId", int)


# Maximum message content length
MAX_MESSAGE_LENGTH = 2000


@dataclass(frozen=True)
class MessageContent:
    """
    Value object representing validated message content.

    Immutable and validated on creation.

    Attributes:
        text: The message text content (1-2000 characters after sanitization)
    """

    text: str

    def __post_init__(self) -> None:
        """Validate message content on creation."""
        # Use object.__setattr__ because dataclass is frozen
        sanitized = self._sanitize(self.text)
        object.__setattr__(self, "text", sanitized)

        if not sanitized or not sanitized.strip():
            raise EmptyMessageError()

        if len(sanitized) > MAX_MESSAGE_LENGTH:
            raise MessageTooLongError(
                actual_length=len(sanitized),
                max_length=MAX_MESSAGE_LENGTH,
            )

    @staticmethod
    def _sanitize(content: str) -> str:
        """Basic content sanitization and normalization."""
        if not content:
            return ""

        # Strip whitespace
        content = content.strip()

        # Remove null bytes and control characters (keep newlines, tabs)
        content = content.replace("\x00", "")
        content = "".join(
            char for char in content if ord(char) >= 32 or char in "\n\r\t"
        )

        return content

    def __str__(self) -> str:
        """Return the text content."""
        return self.text

    def __len__(self) -> int:
        """Return the length of the text content."""
        return len(self.text)

    @property
    def truncated(self) -> str:
        """Return truncated version for display (max 100 chars)."""
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."


@dataclass(frozen=True)
class AttachmentInfo:
    """
    Value object representing message attachment metadata.

    Immutable container for attachment information.

    Attributes:
        filename: Original filename of the attachment
        url: Storage URL or key for the attachment
        size_bytes: File size in bytes
        mime_type: MIME type of the file
    """

    filename: str
    url: str
    size_bytes: int
    mime_type: str

    def __post_init__(self) -> None:
        """Validate attachment info on creation."""
        if not self.filename:
            raise ValueError("Attachment filename cannot be empty")
        if not self.url:
            raise ValueError("Attachment URL cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("Attachment size cannot be negative")
        if not self.mime_type:
            raise ValueError("Attachment MIME type cannot be empty")

    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return self.mime_type.startswith("image/")

    @property
    def is_document(self) -> bool:
        """Check if attachment is a document (PDF, DOC, etc.)."""
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]
        return self.mime_type in document_types

    @property
    def size_kb(self) -> float:
        """Return size in kilobytes."""
        return self.size_bytes / 1024

    @property
    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    def is_within_limit(self, max_mb: float = 10.0) -> bool:
        """Check if attachment is within size limit."""
        return self.size_mb <= max_mb
