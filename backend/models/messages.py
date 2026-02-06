"""Messaging models."""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Conversation(Base):
    """
    Conversation between a student and tutor.

    Tracks conversation metadata including unread counts for both participants.
    Each conversation is unique per student-tutor pair (optionally per booking).
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tutor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Activity tracking
    last_message_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    student_unread_count = Column(Integer, default=0, nullable=False)
    tutor_unread_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Soft delete
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Unique constraint: one conversation per student-tutor pair (per booking if specified)
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "tutor_id",
            "booking_id",
            name="uq_conversation_participants",
        ),
    )

    # Relationships
    student = relationship(
        "User",
        foreign_keys=[student_id],
        backref="student_conversations",
    )
    tutor = relationship(
        "User",
        foreign_keys=[tutor_id],
        backref="tutor_conversations",
    )
    booking = relationship("Booking", backref="conversation")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.desc()",
        lazy="dynamic",
    )
    deleter = relationship("User", foreign_keys=[deleted_by])


class Message(Base):
    """In-platform messaging with edit/delete support and read receipts."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recipient_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    message = Column(Text, nullable=False)
    is_system_message = Column(Boolean, default=False, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages",
    )
    recipient = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="received_messages",
    )
    booking = relationship("Booking", back_populates="messages")
    deleter = relationship("User", foreign_keys=[deleted_by])
    attachments = relationship(
        "MessageAttachment",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="select",
    )


class MessageAttachment(Base):
    """Secure file attachments for messages with virus scanning and access control."""

    __tablename__ = "message_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    file_key = Column(String(500), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_category = Column(String(50), nullable=False)  # 'image', 'document', 'other'

    # Security & Access Control
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    is_scanned = Column(Boolean, default=False, nullable=False)
    scan_result = Column(String(50), nullable=True)  # 'clean', 'infected', 'pending'
    is_public = Column(Boolean, default=False, nullable=False)

    # Metadata
    width = Column(Integer, nullable=True)  # For images
    height = Column(Integer, nullable=True)  # For images
    duration_seconds = Column(Integer, nullable=True)  # For videos/audio

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    message = relationship("Message", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])
