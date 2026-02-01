"""Tests for currency utilities."""

from decimal import Decimal

import pytest

from core.currency import (
    COMMISSION_TIERS,
    DEFAULT_CURRENCIES,
    CurrencyOption,
    calculate_platform_fee,
    cents_to_decimal,
    decimal_to_cents,
    get_commission_tier,
    validate_price,
)


class TestCurrencyOption:
    """Test CurrencyOption model."""

    def test_currency_option_creation(self):
        """Test creating a CurrencyOption."""
        option = CurrencyOption(
            code="USD",
            name="US Dollar",
            symbol="$",
            decimal_places=2,
        )
        assert option.code == "USD"
        assert option.name == "US Dollar"
        assert option.symbol == "$"
        assert option.decimal_places == 2

    def test_currency_option_validation(self):
        """Test CurrencyOption field types."""
        option = CurrencyOption(
            code="EUR",
            name="Euro",
            symbol="€",
            decimal_places=2,
        )
        assert isinstance(option.code, str)
        assert isinstance(option.decimal_places, int)


class TestDefaultCurrencies:
    """Test DEFAULT_CURRENCIES constant."""

    def test_default_currencies_not_empty(self):
        """Test that default currencies list is not empty."""
        assert len(DEFAULT_CURRENCIES) > 0

    def test_usd_in_defaults(self):
        """Test that USD is in default currencies."""
        codes = [c.code for c in DEFAULT_CURRENCIES]
        assert "USD" in codes

    def test_eur_in_defaults(self):
        """Test that EUR is in default currencies."""
        codes = [c.code for c in DEFAULT_CURRENCIES]
        assert "EUR" in codes

    def test_gbp_in_defaults(self):
        """Test that GBP is in default currencies."""
        codes = [c.code for c in DEFAULT_CURRENCIES]
        assert "GBP" in codes

    def test_all_have_required_fields(self):
        """Test that all default currencies have required fields."""
        for currency in DEFAULT_CURRENCIES:
            assert currency.code is not None
            assert len(currency.code) == 3
            assert currency.name is not None
            assert currency.symbol is not None
            assert currency.decimal_places >= 0


class TestCentsToDecimal:
    """Test cents_to_decimal function."""

    def test_basic_conversion(self):
        """Test basic cents to decimal conversion."""
        result = cents_to_decimal(1000)
        assert result == Decimal("10.00")

    def test_zero_cents(self):
        """Test zero cents conversion."""
        result = cents_to_decimal(0)
        assert result == Decimal("0.00")

    def test_with_cents_remainder(self):
        """Test conversion with cents remainder."""
        result = cents_to_decimal(1050)
        assert result == Decimal("10.50")

    def test_single_cent(self):
        """Test single cent conversion."""
        result = cents_to_decimal(1)
        assert result == Decimal("0.01")

    def test_large_amount(self):
        """Test large amount conversion."""
        result = cents_to_decimal(10000000)  # $100,000
        assert result == Decimal("100000.00")

    def test_custom_decimal_places(self):
        """Test conversion with custom decimal places."""
        result = cents_to_decimal(1000, decimal_places=3)
        assert result == Decimal("1.000")


class TestDecimalToCents:
    """Test decimal_to_cents function."""

    def test_basic_conversion(self):
        """Test basic decimal to cents conversion."""
        result = decimal_to_cents(Decimal("10.00"))
        assert result == 1000

    def test_zero_amount(self):
        """Test zero amount conversion."""
        result = decimal_to_cents(Decimal("0.00"))
        assert result == 0

    def test_with_decimal_part(self):
        """Test conversion with decimal part."""
        result = decimal_to_cents(Decimal("10.50"))
        assert result == 1050

    def test_single_cent(self):
        """Test single cent conversion."""
        result = decimal_to_cents(Decimal("0.01"))
        assert result == 1

    def test_large_amount(self):
        """Test large amount conversion."""
        result = decimal_to_cents(Decimal("100000.00"))
        assert result == 10000000

    def test_roundtrip(self):
        """Test roundtrip conversion."""
        original_cents = 1234
        decimal = cents_to_decimal(original_cents)
        back_to_cents = decimal_to_cents(decimal)
        assert back_to_cents == original_cents

    def test_custom_decimal_places(self):
        """Test conversion with custom decimal places."""
        result = decimal_to_cents(Decimal("1.000"), decimal_places=3)
        assert result == 1000


class TestCalculatePlatformFee:
    """Test calculate_platform_fee function."""

    def test_default_fee_percentage(self):
        """Test with default 3% fee."""
        fee, earnings = calculate_platform_fee(10000)  # $100
        assert fee == 300  # $3 fee
        assert earnings == 9700  # $97 earnings

    def test_custom_fee_percentage(self):
        """Test with custom fee percentage."""
        fee, earnings = calculate_platform_fee(10000, fee_percentage=Decimal("10.0"))
        assert fee == 1000  # $10 fee
        assert earnings == 9000  # $90 earnings

    def test_zero_amount(self):
        """Test with zero amount."""
        fee, earnings = calculate_platform_fee(0)
        assert fee == 0
        assert earnings == 0

    def test_small_amount(self):
        """Test with small amount (rounding)."""
        fee, earnings = calculate_platform_fee(100)  # $1
        # 3% of 100 cents = 3 cents
        assert fee == 3
        assert earnings == 97

    def test_fee_plus_earnings_equals_total(self):
        """Test that fee + earnings always equals total."""
        amounts = [100, 500, 1000, 5000, 10000, 99999]
        for amount in amounts:
            fee, earnings = calculate_platform_fee(amount)
            assert fee + earnings == amount


class TestValidatePrice:
    """Test validate_price function."""

    def test_valid_price(self):
        """Test valid price."""
        is_valid, error = validate_price(10.0)
        assert is_valid is True
        assert error is None

    def test_zero_price_default(self):
        """Test zero price with default min."""
        is_valid, error = validate_price(0.0)
        assert is_valid is True

    def test_negative_price(self):
        """Test negative price is invalid."""
        is_valid, error = validate_price(-10.0)
        assert is_valid is False
        assert error is not None

    def test_price_below_minimum(self):
        """Test price below custom minimum."""
        is_valid, error = validate_price(5.0, min_price=10.0)
        assert is_valid is False
        assert "at least" in error

    def test_price_at_minimum(self):
        """Test price exactly at minimum."""
        is_valid, error = validate_price(10.0, min_price=10.0)
        assert is_valid is True


class TestCommissionTiers:
    """Test commission tier logic."""

    def test_commission_tiers_structure(self):
        """Test COMMISSION_TIERS structure."""
        assert len(COMMISSION_TIERS) > 0
        for threshold, percentage in COMMISSION_TIERS:
            assert isinstance(threshold, int)
            assert isinstance(percentage, Decimal)
            assert threshold >= 0
            assert percentage > 0

    def test_tiers_are_ordered(self):
        """Test that tiers are ordered by threshold."""
        thresholds = [tier[0] for tier in COMMISSION_TIERS]
        assert thresholds == sorted(thresholds)

    def test_standard_tier(self):
        """Test standard tier (lowest earnings)."""
        fee_pct, tier_name = get_commission_tier(0)
        assert tier_name == "Standard"
        assert fee_pct == Decimal("20.0")

    def test_silver_tier(self):
        """Test silver tier ($1,000+)."""
        fee_pct, tier_name = get_commission_tier(100_000)  # $1,000 in cents
        assert tier_name == "Silver"
        assert fee_pct == Decimal("15.0")

    def test_gold_tier(self):
        """Test gold tier ($5,000+)."""
        fee_pct, tier_name = get_commission_tier(500_000)  # $5,000 in cents
        assert tier_name == "Gold"
        assert fee_pct == Decimal("10.0")

    def test_tier_boundary_below(self):
        """Test just below tier boundary."""
        # Just below silver tier
        fee_pct, tier_name = get_commission_tier(99_999)
        assert tier_name == "Standard"
        assert fee_pct == Decimal("20.0")

    def test_tier_boundary_at(self):
        """Test exactly at tier boundary."""
        # Exactly at silver tier
        fee_pct, tier_name = get_commission_tier(100_000)
        assert tier_name == "Silver"
        assert fee_pct == Decimal("15.0")

    def test_high_earnings(self):
        """Test high earnings stay in gold tier."""
        fee_pct, tier_name = get_commission_tier(10_000_000)  # $100,000
        assert tier_name == "Gold"
        assert fee_pct == Decimal("10.0")


class TestCurrencyEdgeCases:
    """Test edge cases in currency handling."""

    def test_very_large_amount(self):
        """Test very large amounts don't overflow."""
        large_cents = 999_999_999_999  # ~$10 billion
        decimal = cents_to_decimal(large_cents)
        back = decimal_to_cents(decimal)
        assert back == large_cents

    def test_fee_calculation_precision(self):
        """Test fee calculation maintains precision."""
        # Test with amount that would have rounding issues
        amount = 333  # $3.33
        fee, earnings = calculate_platform_fee(amount, fee_percentage=Decimal("20.0"))
        # 20% of 333 = 66.6, should round to 66
        assert fee == 66
        assert earnings == 267
        assert fee + earnings == amount

    def test_all_tiers_decrease_fees(self):
        """Test that higher tiers have lower fees."""
        previous_fee = Decimal("100.0")  # Start high
        for _threshold, fee_pct in COMMISSION_TIERS:
            assert fee_pct <= previous_fee
            previous_fee = fee_pct
