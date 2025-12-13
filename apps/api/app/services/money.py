from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_TWO_DP = Decimal("0.01")


def parse_money_2dp(value: str) -> Decimal:
    """Parse a decimal string into Decimal and quantize to 2 decimal places.

    API contract: requests/responses represent money as strings.
    Persistence uses NUMERIC(scale=15), but we normalize adjustments to 2dp.
    """

    try:
        dec = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid decimal string: {value}") from None

    return dec.quantize(_TWO_DP, rounding=ROUND_HALF_UP)
