"""Parametric tests for soft delete columns across ALL models that should support it."""

import pytest
from sqlalchemy import inspect

from models.auth import User
from models.messages import Conversation, Message, MessageAttachment
from models.notifications import Notification
from models.payments import Payment, Payout, Refund, Wallet, WalletTransaction
from models.reviews import Review
from models.students import FavoriteTutor, StudentPackage, StudentProfile
from models.tutors import (
    TutorAvailability,
    TutorCertification,
    TutorEducation,
    TutorProfile,
    TutorSubject,
)

# All models that should have soft delete (deleted_at column)
SOFT_DELETE_MODELS = [
    User,
    Notification,
    Conversation,
    Message,
    MessageAttachment,
    Payment,
    Refund,
    Payout,
    Wallet,
    WalletTransaction,
    Review,
    StudentProfile,
    FavoriteTutor,
    StudentPackage,
    TutorProfile,
    TutorSubject,
    TutorAvailability,
    TutorCertification,
    TutorEducation,
]

# Models that should have both deleted_at AND deleted_by
SOFT_DELETE_WITH_ACTOR_MODELS = [
    User,
    Notification,
    Conversation,
    Message,
    Payment,
    Refund,
    Payout,
    Wallet,
    WalletTransaction,
    Review,
    StudentProfile,
    FavoriteTutor,
    StudentPackage,
    TutorProfile,
    TutorSubject,
    TutorAvailability,
    TutorCertification,
    TutorEducation,
]


@pytest.mark.parametrize(
    "model_class",
    SOFT_DELETE_MODELS,
    ids=lambda m: m.__name__,
)
def test_model_has_deleted_at(model_class):
    """All soft-deletable models should have a deleted_at column."""
    mapper = inspect(model_class)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns, (
        f"{model_class.__name__} is missing 'deleted_at' column"
    )


@pytest.mark.parametrize(
    "model_class",
    SOFT_DELETE_WITH_ACTOR_MODELS,
    ids=lambda m: m.__name__,
)
def test_model_has_deleted_by(model_class):
    """Models with soft delete actor tracking should have a deleted_by column."""
    mapper = inspect(model_class)
    columns = {c.key for c in mapper.columns}
    assert "deleted_by" in columns, (
        f"{model_class.__name__} is missing 'deleted_by' column"
    )


@pytest.mark.parametrize(
    "model_class",
    SOFT_DELETE_MODELS,
    ids=lambda m: m.__name__,
)
def test_deleted_at_is_nullable(model_class):
    """deleted_at should be nullable (NULL = not deleted)."""
    mapper = inspect(model_class)
    col = mapper.columns["deleted_at"]
    assert col.nullable is True, (
        f"{model_class.__name__}.deleted_at should be nullable"
    )
