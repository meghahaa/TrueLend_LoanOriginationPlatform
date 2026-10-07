"""Domain money utilities. No IO, no float."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP


def to_money(value: "str | int") -> Decimal:
    """Parse a string or int into a Decimal with 2 dp (ROUND_HALF_UP)."""
    if isinstance(value, float):
        raise TypeError("float is forbidden for money; use str or int")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize(d: Decimal) -> Decimal:
    """Ensure 2 dp ROUND_HALF_UP."""
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
