"""Centralized currency management module."""

import logging
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import SupportedCurrency

logger = logging.getLogger(__name__)


class CurrencyOption(BaseModel):
    """Currency option schema."""

    code: str
    name: str
    symbol: str
    decimal_places: int


DEFAULT_CURRENCIES: List[CurrencyOption] = [
    CurrencyOption(code="USD", name="US Dollar", symbol="$", decimal_places=2),
    CurrencyOption(code="EUR", name="Euro", symbol="€", decimal_places=2),
    CurrencyOption(code="GBP", name="British Pound", symbol="£", decimal_places=2),
]


def load_supported_currencies(db: Session) -> List[CurrencyOption]:
    """Load active currencies from database, fallback to defaults."""
    records = (
        db.query(SupportedCurrency)
        .filter(SupportedCurrency.is_active.is_(True))
        .order_by(SupportedCurrency.currency_code.asc())
        .all()
    )
    if not records:
        return DEFAULT_CURRENCIES

    return [
        CurrencyOption(
            code=record.currency_code.strip(),
            name=record.currency_name,
            symbol=record.currency_symbol,
            decimal_places=record.decimal_places or 2,
        )
        for record in records
    ]


def validate_currency_code(currency: str, db: Session) -> tuple[bool, Optional[str]]:
    """
    Validate currency code against supported currencies.

    Returns:
        (is_valid, error_message)
    """
    if not currency:
        return False, "Currency code is required"

    if len(currency) != 3 or not currency.isupper():
        return False, "Currency must be 3-letter uppercase ISO code"

    currencies = load_supported_currencies(db)
    allowed_codes = {item.code.upper() for item in currencies}

    if currency not in allowed_codes:
        return False, f"Unsupported currency code: {currency}"

    return True, None


def validate_price(price: float, min_price: float = 0) -> tuple[bool, Optional[str]]:
    """Validate price value."""
    if price < min_price:
        return False, f"Price must be at least {min_price}"
    return True, None


def format_price(amount: Decimal, currency: str, db: Session) -> str:
    """
    Format price with currency symbol.

    Args:
        amount: Price amount
        currency: Currency code (e.g., 'USD')
        db: Database session

    Returns:
        Formatted price string (e.g., '$10.50')
    """
    currencies = load_supported_currencies(db)
    currency_map = {c.code: c for c in currencies}

    currency_info = currency_map.get(currency)
    if not currency_info:
        # Fallback to default formatting
        return f"{currency} {amount:.2f}"

    decimal_places = currency_info.decimal_places
    symbol = currency_info.symbol

    return f"{symbol}{amount:.{decimal_places}f}"


def cents_to_decimal(cents: int, decimal_places: int = 2) -> Decimal:
    """Convert cents (minor units) to decimal amount."""
    divisor = 10**decimal_places
    return Decimal(cents) / Decimal(divisor)


def decimal_to_cents(amount: Decimal, decimal_places: int = 2) -> int:
    """Convert decimal amount to cents (minor units)."""
    multiplier = 10**decimal_places
    return int(amount * Decimal(multiplier))


def calculate_platform_fee(
    amount_cents: int, fee_percentage: Decimal = Decimal("3.0")
) -> tuple[int, int]:
    """
    Calculate platform fee and tutor earnings.

    Args:
        amount_cents: Total amount in cents
        fee_percentage: Platform fee percentage (default 3%)

    Returns:
        (platform_fee_cents, tutor_earnings_cents)
    """
    platform_fee_cents = int(amount_cents * (fee_percentage / 100))
    tutor_earnings_cents = amount_cents - platform_fee_cents

    return platform_fee_cents, tutor_earnings_cents
