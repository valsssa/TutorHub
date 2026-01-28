"""Centralized currency management module."""

import logging
from decimal import Decimal

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


DEFAULT_CURRENCIES: list[CurrencyOption] = [
    CurrencyOption(code="USD", name="US Dollar", symbol="$", decimal_places=2),
    CurrencyOption(code="EUR", name="Euro", symbol="€", decimal_places=2),
    CurrencyOption(code="GBP", name="British Pound", symbol="£", decimal_places=2),
]


def load_supported_currencies(db: Session) -> list[CurrencyOption]:
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


def validate_currency_code(currency: str, db: Session) -> tuple[bool, str | None]:
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


def validate_price(price: float, min_price: float = 0) -> tuple[bool, str | None]:
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
    currency_map = {currency.code: currency for currency in currencies}

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


def calculate_platform_fee(amount_cents: int, fee_percentage: Decimal = Decimal("3.0")) -> tuple[int, int]:
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


# ============================================================================
# Revenue-Based Commission Tiers
# ============================================================================

# Commission tiers based on tutor lifetime earnings (in cents)
# Structure: [(threshold_cents, fee_percentage), ...]
# Sorted by threshold ascending - first matching tier wins
COMMISSION_TIERS = [
    (0, Decimal("20.0")),           # $0 - $999.99: 20% fee
    (100_000, Decimal("15.0")),     # $1,000 - $4,999.99: 15% fee
    (500_000, Decimal("10.0")),     # $5,000+: 10% fee
]


def get_tutor_lifetime_earnings(db: Session, tutor_profile_id: int) -> int:
    """
    Calculate tutor's total lifetime earnings in cents from completed bookings.

    Args:
        db: Database session
        tutor_profile_id: Tutor profile ID

    Returns:
        Total earnings in cents
    """
    from sqlalchemy import func

    from models import Booking

    result = (
        db.query(func.coalesce(func.sum(Booking.tutor_earnings_cents), 0))
        .filter(
            Booking.tutor_profile_id == tutor_profile_id,
            Booking.status == "COMPLETED",
        )
        .scalar()
    )

    return int(result or 0)


def get_commission_tier(lifetime_earnings_cents: int) -> tuple[Decimal, str]:
    """
    Determine commission tier based on lifetime earnings.

    Args:
        lifetime_earnings_cents: Tutor's total lifetime earnings in cents

    Returns:
        (fee_percentage, tier_name) tuple
    """
    fee_pct = COMMISSION_TIERS[0][1]  # Default to highest fee
    tier_name = "Standard"

    for threshold, pct in COMMISSION_TIERS:
        if lifetime_earnings_cents >= threshold:
            fee_pct = pct
            if threshold >= 500_000:
                tier_name = "Gold"
            elif threshold >= 100_000:
                tier_name = "Silver"
            else:
                tier_name = "Standard"

    return fee_pct, tier_name


def get_dynamic_platform_fee(db: Session, tutor_profile_id: int) -> tuple[Decimal, str, int]:
    """
    Get the dynamic platform fee percentage for a tutor based on their earnings.

    Args:
        db: Database session
        tutor_profile_id: Tutor profile ID

    Returns:
        (fee_percentage, tier_name, lifetime_earnings_cents) tuple
    """
    lifetime_earnings = get_tutor_lifetime_earnings(db, tutor_profile_id)
    fee_pct, tier_name = get_commission_tier(lifetime_earnings)

    logger.debug(
        f"Tutor {tutor_profile_id} commission tier: {tier_name} "
        f"({fee_pct}% fee, ${lifetime_earnings / 100:.2f} lifetime earnings)"
    )

    return fee_pct, tier_name, lifetime_earnings


def calculate_platform_fee_dynamic(
    db: Session,
    tutor_profile_id: int,
    amount_cents: int,
) -> tuple[int, int, Decimal, str]:
    """
    Calculate platform fee using dynamic revenue-based tiers.

    Args:
        db: Database session
        tutor_profile_id: Tutor profile ID
        amount_cents: Total booking amount in cents

    Returns:
        (platform_fee_cents, tutor_earnings_cents, fee_percentage, tier_name)
    """
    fee_pct, tier_name, _ = get_dynamic_platform_fee(db, tutor_profile_id)

    platform_fee_cents = int(amount_cents * (fee_pct / 100))
    tutor_earnings_cents = amount_cents - platform_fee_cents

    return platform_fee_cents, tutor_earnings_cents, fee_pct, tier_name
