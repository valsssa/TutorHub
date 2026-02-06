"""
Messages domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for the messaging system following Clean Architecture/DDD patterns.
"""

from modules.messages.domain.entities import (
    ConversationEntity,
    MessageAttachmentEntity,
    MessageEntity,
)
from modules.messages.domain.exceptions import (
    AttachmentNotFoundError,
    ConversationNotFoundError,
    EmptyMessageError,
    InvalidRecipientError,
    MessageEditWindowExpiredError,
    MessageError,
    MessageNotFoundError,
    MessageTooLongError,
    UnauthorizedMessageAccessError,
)
from modules.messages.domain.repositories import (
    ConversationRepository,
    MessageAttachmentRepository,
    MessageRepository,
)
from modules.messages.domain.value_objects import (
    MAX_MESSAGE_LENGTH,
    AttachmentId,
    AttachmentInfo,
    ConversationId,
    MessageContent,
    MessageId,
    UserId,
)

__all__ = [
    # Entities
    "MessageEntity",
    "ConversationEntity",
    "MessageAttachmentEntity",
    # Value Objects
    "MessageId",
    "ConversationId",
    "UserId",
    "AttachmentId",
    "MessageContent",
    "AttachmentInfo",
    "MAX_MESSAGE_LENGTH",
    # Exceptions
    "MessageError",
    "MessageNotFoundError",
    "ConversationNotFoundError",
    "UnauthorizedMessageAccessError",
    "MessageTooLongError",
    "AttachmentNotFoundError",
    "InvalidRecipientError",
    "MessageEditWindowExpiredError",
    "EmptyMessageError",
    # Repository Protocols
    "MessageRepository",
    "ConversationRepository",
    "MessageAttachmentRepository",
]
