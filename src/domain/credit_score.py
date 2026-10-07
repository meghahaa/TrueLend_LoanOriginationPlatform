"""
Credit score stub — deterministic pure function.
No IO, no framework imports, no float.

Formula (specs/application-intake_spec.md §AC-03):
  score = clamp(300 + age_pts + income_pts + history_pts − default_pen, 300, 900)
Integer arithmetic only.
"""
from __future__ import annotations


def _age_pts(age: int) -> int:
    if 18 <= age <= 20:
        return 20
    if 21 <= age <= 25:
        return 40
    if 26 <= age <= 35:
        return 80
    if 36 <= age <= 50:
        return 100
    if 51 <= age <= 65:
        return 60
    return 20  # > 65


def _income_pts(monthly_income: "int | float") -> int:
    # Spec says integer arithmetic; income compared as a number
    if monthly_income < 25000:
        return 40
    if monthly_income < 50000:
        return 100
    if monthly_income < 100000:
        return 160
    return 220


_HISTORY_PTS = {
    "CLEAN": 200,
    "THIN": 80,
    "LATE_PAYMENTS": 0,
}


def calculate_credit_score(
    *,
    age: int,
    monthly_income: "int | float",
    credit_history: str,
    has_default: bool,
) -> int:
    """Return the clamped credit score [300, 900]."""
    history_pts = _HISTORY_PTS.get(credit_history, 0)
    default_pen = 100 if has_default else 0
    raw = 300 + _age_pts(age) + _income_pts(monthly_income) + history_pts - default_pen
    return max(300, min(900, raw))
