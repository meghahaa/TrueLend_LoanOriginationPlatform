"""Domain exceptions. No framework or IO imports."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


class PolicyViolationException(Exception):
    """Raised when an application violates policy eligibility rules."""

    def __init__(self, reason_codes: List[str], policy_version: int) -> None:
        self.reason_codes = reason_codes
        self.policy_version = policy_version
        super().__init__(f"Policy violation (v{policy_version}): {reason_codes}")
