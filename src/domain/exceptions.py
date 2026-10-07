"""Domain exceptions. No framework or IO imports."""
from __future__ import annotations
from typing import List


class PolicyViolationException(Exception):
    """Raised when an application violates policy eligibility rules."""

    def __init__(self, reason_codes: List[str], policy_version: int) -> None:
        self.reason_codes = reason_codes
        self.policy_version = policy_version
        super().__init__(f"Policy violation (v{policy_version}): {reason_codes}")


class InvalidDocumentStateException(Exception):
    """Raised when an action cannot be performed on a document due to its current state."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DocumentsNotVerifiedException(Exception):
    """Raised when an approval/disbursement is attempted without all required documents verified."""

    def __init__(self, message: str = "DOCUMENTS_NOT_VERIFIED") -> None:
        self.code = "DOCUMENTS_NOT_VERIFIED"
        super().__init__(message)


class AlreadyDisbursedException(Exception):
    """Raised when disbursement is attempted on an already disbursed loan."""

    def __init__(self, message: str = "ALREADY_DISBURSED") -> None:
        self.code = "ALREADY_DISBURSED"
        super().__init__(message)


class InvalidApplicationStateException(Exception):
    """Raised when an action is incompatible with the application's current state."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
