"""Tests to verify all models have soft delete columns."""
import pytest
from sqlalchemy import inspect

from models.payments import Payout, Refund, Wallet, WalletTransaction
from models.reviews import Review
from models.students import FavoriteTutor, StudentPackage, StudentProfile
from models.tutors import TutorAvailability, TutorCertification, TutorEducation, TutorSubject

MODELS_REQUIRING_SOFT_DELETE = [
    FavoriteTutor, StudentPackage, StudentProfile,
    Refund, Payout, Wallet, WalletTransaction,
    Review,
    TutorSubject, TutorAvailability, TutorCertification, TutorEducation,
]


@pytest.mark.parametrize("model_class", MODELS_REQUIRING_SOFT_DELETE)
def test_model_has_deleted_at(model_class):
    mapper = inspect(model_class)
    assert "deleted_at" in [c.key for c in mapper.columns], f"{model_class.__name__} missing deleted_at"


@pytest.mark.parametrize("model_class", MODELS_REQUIRING_SOFT_DELETE)
def test_model_has_deleted_by(model_class):
    mapper = inspect(model_class)
    assert "deleted_by" in [c.key for c in mapper.columns], f"{model_class.__name__} missing deleted_by"
