"""
DPD and Delinquency Bucket Calculator — pure domain rules.
No IO, no framework imports.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional


DEFAULT_BUCKET_THRESHOLDS = {
    "dpd_30": 30,
    "dpd_60": 60,
    "dpd_90": 90,
    "npa": 180,
}


def calculate_dpd(
    as_of: date,
    oldest_unpaid_due_date: Optional[date],
) -> int:
    """
    Calculate Days Past Due (DPD):
    Days between as_of and the due date of the oldest instalment not fully paid.
    Returns 0 if none overdue (as_of <= due_date or all paid).
    """
    if oldest_unpaid_due_date is None:
        return 0

    if as_of <= oldest_unpaid_due_date:
        return 0

    return (as_of - oldest_unpaid_due_date).days


def resolve_delinquency_bucket(
    dpd: int,
    bucket_thresholds: Optional[Dict[str, int]] = None,
) -> str:
    """
    Resolve delinquency bucket from DPD:
    - dpd < 30 -> CURRENT
    - 30 <= dpd < 60 -> DPD-30
    - 60 <= dpd < 90 -> DPD-60
    - 90 <= dpd < 180 -> DPD-90
    - dpd >= 180 -> NPA
    """
    thresholds = bucket_thresholds or DEFAULT_BUCKET_THRESHOLDS
    t30 = thresholds.get("dpd_30", 30)
    t60 = thresholds.get("dpd_60", 60)
    t90 = thresholds.get("dpd_90", 90)
    tnpa = thresholds.get("npa", 180)

    if dpd < t30:
        return "CURRENT"
    if dpd < t60:
        return "DPD-30"
    if dpd < t90:
        return "DPD-60"
    if dpd < tnpa:
        return "DPD-90"
    return "NPA"
