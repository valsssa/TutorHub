"""
Domain exceptions for messages module.

These exceptions represent business rule violations specific to messaging.
"""


class MessageError(Exception):
    """Base exception for message domain errors."""

    pass


class MessageNotFoundError(MessageError):
    """Raised when a message is not found."""

    def __init__(self, message_id: int | None = None):
        self.message_id = message_id
        msg = f"Message not found: {message_id}" if message_id else "Message not found"
        super().__init__(msg)


class ConversationNotFoundError(MessageError):
    """Raised when a conversation is not found."""

    def __init__(
        self,
        conversation_id: int | None = None,
        participants: tuple[int, int] | None = None,
    ):
        self.conversation_id = conversation_id
        self.participants = participants
        if conversation_id:
            msg = f"Conversation not found: {conversation_id}"
        elif participants:
            msg = f"Conversation not found between users {participants[0]} and {participants[1]}"
        else:
            msg = "Conversation not found"
        super().__init__(msg)


class UnauthorizedMessageAccessError(MessageError):
    """Raised when user attempts to access a message they don't have permission for."""

    def __init__(
        self,
        user_id: int,
        message_id: int | None = None,
        action: str = "access",
    ):
        self.user_id = user_id
        self.message_id = message_id
        self.action = action
        if message_id:
            msg = f"User {user_id} not authorized to {action} message {message_id}"
        else:
            msg = f"User {user_id} not authorized to {action} this message"
        super().__init__(msg)


class MessageTooLongError(MessageError):
    """Raised when message content exceeds maximum length."""

    def __init__(
        self,
        actual_length: int,
        max_length: int = 2000,
    ):
        self.actual_length = actual_length
        self.max_length = max_length
        super().__init__(
            f"Message too long: {actual_length} characters (max {max_length})"
        )


class AttachmentNotFoundError(MessageError):
    """Raised when a message attachment is not found."""

    def __init__(self, attachment_id: int | None = None):
        self.attachment_id = attachment_id
        msg = f"Attachment not found: {attachment_id}" if attachment_id else "Attachment not found"
        super().__init__(msg)


class InvalidRecipientError(MessageError):
    """Raised when attempting to send a message to an invalid recipient."""

    def __init__(
        self,
        recipient_id: int | None = None,
        reason: str = "Invalid recipient",
    ):
        self.recipient_id = recipient_id
        self.reason = reason
        if recipient_id:
            msg = f"Cannot send message to user {recipient_id}: {reason}"
        else:
            msg = f"Cannot send message: {reason}"
        super().__init__(msg)


class MessageEditWindowExpiredError(MessageError):
    """Raised when attempting to edit a message outside the edit window."""

    def __init__(
        self,
        message_id: int,
        edit_window_minutes: int = 15,
    ):
        self.message_id = message_id
        self.edit_window_minutes = edit_window_minutes
        super().__init__(
            f"Cannot edit message {message_id}: edit window of {edit_window_minutes} minutes has expired"
        )


class EmptyMessageError(MessageError):
    """Raised when attempting to send an empty message."""

    def __init__(self) -> None:
        super().__init__("Message content cannot be empty")
