"""Unit tests for money parsing and rounding utilities."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.money import parse_money_2dp


class TestParseMoney2dp:
    """Tests for parse_money_2dp function."""

    # -------------------------------------------------------------------------
    # Valid inputs
    # -------------------------------------------------------------------------

    def test_exact_two_decimals(self):
        """Normal case: input already has 2 decimal places."""
        assert parse_money_2dp("10.50") == Decimal("10.50")

    def test_one_decimal_padded(self):
        """Single decimal place should be padded to 2."""
        assert parse_money_2dp("10.5") == Decimal("10.50")

    def test_integer_becomes_two_decimals(self):
        """Integer input should become X.00."""
        assert parse_money_2dp("10") == Decimal("10.00")

    def test_zero(self):
        """Zero should parse to 0.00."""
        assert parse_money_2dp("0") == Decimal("0.00")

    def test_negative_value(self):
        """Negative values should parse correctly."""
        assert parse_money_2dp("-5.25") == Decimal("-5.25")

    def test_large_number(self):
        """Large numbers should work correctly."""
        assert parse_money_2dp("999999999.99") == Decimal("999999999.99")

    # -------------------------------------------------------------------------
    # Rounding behavior (ROUND_HALF_UP)
    # -------------------------------------------------------------------------

    def test_round_up_at_midpoint(self):
        """0.555 should round UP to 0.56 (ROUND_HALF_UP)."""
        assert parse_money_2dp("10.555") == Decimal("10.56")

    def test_round_down_below_midpoint(self):
        """0.554 should round down to 0.55."""
        assert parse_money_2dp("10.554") == Decimal("10.55")

    def test_round_up_above_midpoint(self):
        """0.556 should round up to 0.56."""
        assert parse_money_2dp("10.556") == Decimal("10.56")

    def test_half_up_not_bankers_rounding(self):
        """Verify ROUND_HALF_UP, not banker's rounding (ROUND_HALF_EVEN).

        With banker's rounding: 10.545 -> 10.54 (round to even)
        With ROUND_HALF_UP:     10.545 -> 10.55 (always round up at .5)
        """
        assert parse_money_2dp("10.545") == Decimal("10.55")

    def test_many_decimals_rounded(self):
        """Many decimal places should be properly rounded."""
        assert parse_money_2dp("10.12345678") == Decimal("10.12")

    def test_negative_rounding(self):
        """Negative values should also round correctly."""
        assert parse_money_2dp("-10.555") == Decimal("-10.56")

    # -------------------------------------------------------------------------
    # Invalid inputs
    # -------------------------------------------------------------------------

    def test_empty_string_raises(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("")

    def test_non_numeric_raises(self):
        """Non-numeric input should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("abc")

    def test_whitespace_only_raises(self):
        """Whitespace-only input should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("   ")

    def test_mixed_content_raises(self):
        """Mixed numeric/non-numeric should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("10.50abc")

    # -------------------------------------------------------------------------
    # Special Decimal values (potential bugs)
    # -------------------------------------------------------------------------

    def test_nan_raises(self):
        """NaN is not valid for money and should raise ValueError."""
        # NOTE: Decimal("NaN") is technically valid, but invalid for money
        # This test documents the expected behavior
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("NaN")

    def test_infinity_raises(self):
        """Infinity is not valid for money and should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("Infinity")

    def test_negative_infinity_raises(self):
        """Negative Infinity is not valid for money and should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal string"):
            parse_money_2dp("-Infinity")

    # -------------------------------------------------------------------------
    # Edge cases
    # -------------------------------------------------------------------------

    def test_scientific_notation(self):
        """Scientific notation should work but may lose precision.

        1e-5 = 0.00001, which rounds to 0.00.
        """
        assert parse_money_2dp("1e-5") == Decimal("0.00")

    def test_leading_zeros(self):
        """Leading zeros should be handled."""
        assert parse_money_2dp("00010.50") == Decimal("10.50")

    def test_plus_sign(self):
        """Explicit plus sign should work."""
        assert parse_money_2dp("+10.50") == Decimal("10.50")
