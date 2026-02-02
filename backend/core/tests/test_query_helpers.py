"""Tests for query helper utilities."""

import pytest
from fastapi import HTTPException
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from core.query_helpers import (
    exists_or_404,
    exists_or_409,
    get_by_id_or_404,
    get_or_404,
    get_or_none,
    get_with_options_or_404,
)

Base = declarative_base()


class MockModel(Base):
    """Mock model for testing."""

    __tablename__ = "mock_model"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    deleted_at = Column(DateTime, nullable=True)


class MockModelNoSoftDelete(Base):
    """Mock model without soft delete support."""

    __tablename__ = "mock_no_soft_delete"

    id = Column(Integer, primary_key=True)
    name = Column(String)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Create test data
    session.add(MockModel(id=1, name="Test 1"))
    session.add(MockModel(id=2, name="Test 2"))
    session.add(MockModel(id=3, name="Deleted", deleted_at="2024-01-01"))
    session.add(MockModelNoSoftDelete(id=1, name="No Soft Delete"))
    session.commit()

    yield session

    session.close()


class TestGetOr404:
    """Tests for get_or_404 function."""

    def test_returns_entity_when_found(self, db_session: Session):
        """Should return entity when it exists."""
        result = get_or_404(db_session, MockModel, {"id": 1})
        assert result.id == 1
        assert result.name == "Test 1"

    def test_raises_404_when_not_found(self, db_session: Session):
        """Should raise HTTPException 404 when entity not found."""
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db_session, MockModel, {"id": 999})
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resource not found"

    def test_custom_detail_message(self, db_session: Session):
        """Should use custom detail message when provided."""
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db_session, MockModel, {"id": 999}, detail="Custom message")
        assert exc_info.value.detail == "Custom message"

    def test_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should exclude soft-deleted records by default."""
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db_session, MockModel, {"id": 3})
        assert exc_info.value.status_code == 404

    def test_includes_soft_deleted_when_requested(self, db_session: Session):
        """Should include soft-deleted records when include_deleted=True."""
        result = get_or_404(db_session, MockModel, {"id": 3}, include_deleted=True)
        assert result.id == 3
        assert result.name == "Deleted"

    def test_filter_by_multiple_fields(self, db_session: Session):
        """Should filter by multiple fields."""
        result = get_or_404(db_session, MockModel, {"id": 1, "name": "Test 1"})
        assert result.id == 1

    def test_works_with_model_without_soft_delete(self, db_session: Session):
        """Should work with models that don't have deleted_at column."""
        result = get_or_404(db_session, MockModelNoSoftDelete, {"id": 1})
        assert result.id == 1
        assert result.name == "No Soft Delete"


class TestGetOrNone:
    """Tests for get_or_none function."""

    def test_returns_entity_when_found(self, db_session: Session):
        """Should return entity when it exists."""
        result = get_or_none(db_session, MockModel, {"id": 1})
        assert result is not None
        assert result.id == 1

    def test_returns_none_when_not_found(self, db_session: Session):
        """Should return None when entity not found."""
        result = get_or_none(db_session, MockModel, {"id": 999})
        assert result is None

    def test_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should exclude soft-deleted records by default."""
        result = get_or_none(db_session, MockModel, {"id": 3})
        assert result is None

    def test_includes_soft_deleted_when_requested(self, db_session: Session):
        """Should include soft-deleted records when include_deleted=True."""
        result = get_or_none(db_session, MockModel, {"id": 3}, include_deleted=True)
        assert result is not None
        assert result.id == 3


class TestExistsOr404:
    """Tests for exists_or_404 function."""

    def test_returns_true_when_exists(self, db_session: Session):
        """Should return True when entity exists."""
        result = exists_or_404(db_session, MockModel, {"id": 1})
        assert result is True

    def test_raises_404_when_not_exists(self, db_session: Session):
        """Should raise HTTPException 404 when entity not found."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_404(db_session, MockModel, {"id": 999})
        assert exc_info.value.status_code == 404

    def test_custom_detail_message(self, db_session: Session):
        """Should use custom detail message when provided."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_404(db_session, MockModel, {"id": 999}, detail="Entity not found")
        assert exc_info.value.detail == "Entity not found"

    def test_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should exclude soft-deleted records by default."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_404(db_session, MockModel, {"id": 3})
        assert exc_info.value.status_code == 404


class TestGetByIdOr404:
    """Tests for get_by_id_or_404 function."""

    def test_returns_entity_when_found(self, db_session: Session):
        """Should return entity when it exists."""
        result = get_by_id_or_404(db_session, MockModel, 1)
        assert result.id == 1

    def test_raises_404_when_not_found(self, db_session: Session):
        """Should raise HTTPException 404 when entity not found."""
        with pytest.raises(HTTPException) as exc_info:
            get_by_id_or_404(db_session, MockModel, 999)
        assert exc_info.value.status_code == 404

    def test_auto_generated_detail_message(self, db_session: Session):
        """Should generate detail message from model name."""
        with pytest.raises(HTTPException) as exc_info:
            get_by_id_or_404(db_session, MockModel, 999)
        # MockModel -> "Mock Model not found"
        assert "Mock Model not found" in exc_info.value.detail

    def test_custom_detail_message(self, db_session: Session):
        """Should use custom detail message when provided."""
        with pytest.raises(HTTPException) as exc_info:
            get_by_id_or_404(db_session, MockModel, 999, detail="Custom not found")
        assert exc_info.value.detail == "Custom not found"


class TestGetWithOptionsOr404:
    """Tests for get_with_options_or_404 function."""

    def test_returns_entity_when_found(self, db_session: Session):
        """Should return entity when query returns result."""
        query = db_session.query(MockModel).filter(MockModel.id == 1)
        result = get_with_options_or_404(query)
        assert result.id == 1

    def test_raises_404_when_not_found(self, db_session: Session):
        """Should raise HTTPException 404 when query returns no result."""
        query = db_session.query(MockModel).filter(MockModel.id == 999)
        with pytest.raises(HTTPException) as exc_info:
            get_with_options_or_404(query)
        assert exc_info.value.status_code == 404

    def test_custom_detail_message(self, db_session: Session):
        """Should use custom detail message when provided."""
        query = db_session.query(MockModel).filter(MockModel.id == 999)
        with pytest.raises(HTTPException) as exc_info:
            get_with_options_or_404(query, detail="Query returned nothing")
        assert exc_info.value.detail == "Query returned nothing"


class TestExistsOr409:
    """Tests for exists_or_409 function."""

    def test_does_not_raise_when_not_exists(self, db_session: Session):
        """Should not raise when entity does not exist."""
        # Should not raise
        exists_or_409(db_session, MockModel, {"id": 999})

    def test_raises_409_when_exists(self, db_session: Session):
        """Should raise HTTPException 409 when entity exists."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_409(db_session, MockModel, {"id": 1})
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Resource already exists"

    def test_custom_detail_message(self, db_session: Session):
        """Should use custom detail message when provided."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_409(db_session, MockModel, {"id": 1}, detail="Already exists!")
        assert exc_info.value.detail == "Already exists!"

    def test_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should exclude soft-deleted records (so no conflict raised)."""
        # Should not raise because id=3 is soft-deleted
        exists_or_409(db_session, MockModel, {"id": 3})

    def test_includes_soft_deleted_when_requested(self, db_session: Session):
        """Should include soft-deleted records when include_deleted=True."""
        with pytest.raises(HTTPException) as exc_info:
            exists_or_409(db_session, MockModel, {"id": 3}, include_deleted=True)
        assert exc_info.value.status_code == 409
