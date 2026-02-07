"""Tests for wallet transactions response format.

Verifies that the /api/v1/wallet/transactions endpoint returns a consistent
response format matching the frontend's expected structure.
"""

from datetime import UTC, datetime

from core.datetime_utils import utc_now

import pytest

from modules.payments.wallet_router import (
    TransactionListResponse,
    TransactionResponse,
)


class TestTransactionResponseSchema:
    """Tests for TransactionResponse schema validation."""

    def test_transaction_response_has_required_fields(self):
        """Verify TransactionResponse has all expected fields."""
        response = TransactionResponse(
            id=1,
            type="DEPOSIT",
            amount_cents=5000,
            currency="USD",
            description="Wallet top-up",
            status="COMPLETED",
            reference_id="pi_test123",
            created_at=utc_now(),
            completed_at=utc_now(),
        )

        assert response.id == 1
        assert response.type == "DEPOSIT"
        assert response.amount_cents == 5000
        assert response.currency == "USD"
        assert response.description == "Wallet top-up"
        assert response.status == "COMPLETED"
        assert response.reference_id == "pi_test123"
        assert response.created_at is not None
        assert response.completed_at is not None

    def test_transaction_response_optional_fields(self):
        """Verify optional fields can be None."""
        response = TransactionResponse(
            id=2,
            type="PAYMENT",
            amount_cents=2500,
            currency="USD",
            description=None,
            status="PENDING",
            created_at=utc_now(),
        )

        assert response.description is None
        assert response.reference_id is None
        assert response.completed_at is None

    def test_transaction_response_serialization(self):
        """Verify response serializes to correct JSON format."""
        now = utc_now()
        response = TransactionResponse(
            id=3,
            type="REFUND",
            amount_cents=1000,
            currency="EUR",
            description="Session refund",
            status="COMPLETED",
            reference_id="ref_456",
            created_at=now,
            completed_at=now,
        )

        data = response.model_dump()

        assert data["id"] == 3
        assert data["type"] == "REFUND"
        assert data["amount_cents"] == 1000
        assert data["currency"] == "EUR"
        assert data["description"] == "Session refund"
        assert data["status"] == "COMPLETED"
        assert data["reference_id"] == "ref_456"
        # datetime should be included
        assert data["created_at"] is not None
        assert data["completed_at"] is not None

    def test_transaction_response_json_serialization(self):
        """Verify response produces valid JSON with ISO datetime strings."""
        now = datetime(2026, 2, 6, 12, 0, 0, tzinfo=UTC)
        response = TransactionResponse(
            id=4,
            type="DEPOSIT",
            amount_cents=10000,
            currency="USD",
            description="Top-up",
            status="COMPLETED",
            created_at=now,
            completed_at=now,
        )

        json_str = response.model_dump_json()

        # Should contain ISO format datetime
        assert "2026-02-06" in json_str
        assert '"id":4' in json_str or '"id": 4' in json_str

    def test_transaction_response_from_attributes_enabled(self):
        """Verify model_config has from_attributes for ORM compatibility."""
        config = TransactionResponse.model_config
        assert config.get("from_attributes") is True

    def test_all_transaction_types_valid(self):
        """Verify all transaction types from the database can be serialized."""
        valid_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "REFUND", "PAYOUT", "PAYMENT", "FEE"]
        now = utc_now()

        for tx_type in valid_types:
            response = TransactionResponse(
                id=1,
                type=tx_type,
                amount_cents=100,
                currency="USD",
                description=None,
                status="PENDING",
                created_at=now,
            )
            assert response.type == tx_type

    def test_all_transaction_statuses_valid(self):
        """Verify all transaction statuses from the database can be serialized."""
        valid_statuses = ["PENDING", "COMPLETED", "FAILED", "CANCELLED"]
        now = utc_now()

        for status in valid_statuses:
            response = TransactionResponse(
                id=1,
                type="DEPOSIT",
                amount_cents=100,
                currency="USD",
                description=None,
                status=status,
                created_at=now,
            )
            assert response.status == status


class TestTransactionListResponseSchema:
    """Tests for TransactionListResponse (paginated) schema validation."""

    def test_transaction_list_response_structure(self):
        """Verify paginated response has correct structure."""
        now = utc_now()
        items = [
            TransactionResponse(
                id=1,
                type="DEPOSIT",
                amount_cents=5000,
                currency="USD",
                description="Top-up",
                status="COMPLETED",
                created_at=now,
            ),
            TransactionResponse(
                id=2,
                type="PAYMENT",
                amount_cents=2000,
                currency="USD",
                description="Session payment",
                status="COMPLETED",
                created_at=now,
            ),
        ]

        response = TransactionListResponse(
            items=items,
            total=100,
            page=1,
            page_size=20,
            total_pages=5,
        )

        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 5

    def test_empty_transaction_list(self):
        """Verify empty list response is valid."""
        response = TransactionListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )

        assert response.items == []
        assert response.total == 0
        assert response.total_pages == 0

    def test_transaction_list_serialization(self):
        """Verify paginated response serializes correctly."""
        now = utc_now()
        items = [
            TransactionResponse(
                id=1,
                type="DEPOSIT",
                amount_cents=5000,
                currency="USD",
                description=None,
                status="PENDING",
                created_at=now,
            ),
        ]

        response = TransactionListResponse(
            items=items,
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        data = response.model_dump()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1

    def test_transaction_list_from_attributes_enabled(self):
        """Verify model_config has from_attributes for ORM compatibility."""
        config = TransactionListResponse.model_config
        assert config.get("from_attributes") is True


class TestWalletTransactionResponseConsistency:
    """Tests verifying frontend-backend contract consistency."""

    def test_response_matches_frontend_backend_transaction_interface(self):
        """Verify response matches frontend BackendTransaction interface.

        Frontend expects:
        - id: number
        - type: BackendTransactionType (DEPOSIT, WITHDRAWAL, etc.)
        - amount_cents: number
        - currency: string
        - description: string | null
        - status: string
        - reference_id?: string | null
        - created_at: string (ISO format)
        - completed_at?: string | null
        """
        now = utc_now()
        response = TransactionResponse(
            id=1,
            type="DEPOSIT",
            amount_cents=5000,
            currency="USD",
            description="Top-up",
            status="COMPLETED",
            reference_id="ref_123",
            created_at=now,
            completed_at=now,
        )

        # Serialize to JSON-compatible dict
        data = response.model_dump(mode="json")

        # Verify all frontend expected fields
        assert isinstance(data["id"], int)
        assert isinstance(data["type"], str)
        assert data["type"] in ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "REFUND", "PAYOUT", "PAYMENT", "FEE"]
        assert isinstance(data["amount_cents"], int)
        assert isinstance(data["currency"], str)
        assert data["description"] is None or isinstance(data["description"], str)
        assert isinstance(data["status"], str)
        assert data["reference_id"] is None or isinstance(data["reference_id"], str)
        assert isinstance(data["created_at"], str)  # ISO format string
        assert data["completed_at"] is None or isinstance(data["completed_at"], str)

    def test_pagination_matches_frontend_paginated_response(self):
        """Verify pagination matches frontend PaginatedResponse<T> interface.

        Frontend expects:
        - items: T[]
        - total: number
        - page: number
        - page_size: number
        - total_pages: number
        """
        response = TransactionListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )

        data = response.model_dump()

        assert "items" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["total_pages"], int)
