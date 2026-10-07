"""
Disbursement Service — manages loan fund releasing, metadata recording, and state transitions.
Pure service layer; no network IO, no framework imports.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from src.domain.exceptions import (
    AlreadyDisbursedException,
    DocumentsNotVerifiedException,
    InvalidApplicationStateException,
)
from src.domain.models import (
    ApplicationStatus,
    AuditEntry,
    DisbursementRecord,
    Document,
    DocumentStatus,
)
from src.services.document_verification_service import DocumentVerificationService


@dataclass(frozen=True)
class DisbursementResult:
    disbursement: DisbursementRecord
    audit_entry: AuditEntry
    new_status: ApplicationStatus
    outstanding_principal: Decimal
    delinquency_bucket: str
    dpd: int


class DisbursementService:
    def __init__(
        self,
        doc_verification_service: Optional[DocumentVerificationService] = None,
    ) -> None:
        self._doc_verifier = doc_verification_service or DocumentVerificationService()

    def disburse_loan(
        self,
        *,
        application_id: str,
        principal: Decimal,
        status: ApplicationStatus,
        has_schedule: bool,
        required_doc_types: List[str],
        documents: Dict[str, Document],
        released_by: str,
        already_disbursed: bool = False,
        disbursed_at: Optional[str] = None,
    ) -> DisbursementResult:
        """
        Execute disbursement for an approved application.
        Preconditions:
          - Not already disbursed (else AlreadyDisbursedException)
          - Status is APPROVED (else InvalidApplicationStateException)
          - Has schedule (else InvalidApplicationStateException)
          - All required documents VERIFIED (else DocumentsNotVerifiedException)
        """
        if already_disbursed:
            raise AlreadyDisbursedException("Application is already disbursed.")

        if status != ApplicationStatus.APPROVED:
            raise InvalidApplicationStateException(
                f"Application cannot be disbursed from status '{status.value}'."
            )

        if not has_schedule:
            raise InvalidApplicationStateException(
                "Application cannot be disbursed without a generated repayment schedule."
            )

        # Ensure all required documents are verified
        self._doc_verifier.validate_all_required_verified(required_doc_types, documents)

        ts = disbursed_at or datetime.now(timezone.utc).isoformat()
        disbursement_id = str(uuid.uuid4())

        record = DisbursementRecord(
            disbursement_id=disbursement_id,
            application_id=application_id,
            amount=principal,
            funding_source="STUB_FUNDING_ACCOUNT_01",
            reference=f"DSB-{application_id}",
            disbursed_at=ts,
            released_by=released_by,
            status="SUCCESS",
        )

        audit_entry = AuditEntry(
            actor_user_id=released_by,
            action="DISBURSE_LOAN",
            application_id=application_id,
            comment=f"Disbursed loan amount {principal}",
            timestamp=ts,
        )

        return DisbursementResult(
            disbursement=record,
            audit_entry=audit_entry,
            new_status=ApplicationStatus.DISBURSED,
            outstanding_principal=principal,
            delinquency_bucket="CURRENT",
            dpd=0,
        )
