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
    Actor,
    ApplicationStatus,
    AuditEntry,
    DisbursementRecord,
    Document,
    DocumentStatus,
)
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository
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
        app_repo: Optional[ApplicationRepository] = None,
        policy_repo: Optional[PolicyRepository] = None,
    ) -> None:
        self._doc_verifier = doc_verification_service or DocumentVerificationService()
        self._app_repo = app_repo
        self._policy_repo = policy_repo

    def execute_disbursement(
        self,
        *,
        actor: Actor,
        application_id: str,
    ) -> DisbursementRecord:
        """
        Orchestrate disbursement execution for an approved application.
        Preconditions:
          - Role is UNDERWRITER or ADMIN (else PermissionError -> 403)
          - Application exists (else KeyError -> 404)
          - Not already disbursed (else AlreadyDisbursedException -> 409)
          - Status is APPROVED (else InvalidApplicationStateException -> 409)
          - Has schedule (else InvalidApplicationStateException -> 409)
          - All required documents are VERIFIED (else DocumentsNotVerifiedException -> 409)
        """
        if self._app_repo is None or self._policy_repo is None:
            raise RuntimeError("Repositories not configured on DisbursementService")

        if actor.role not in ("UNDERWRITER", "ADMIN"):
            raise PermissionError("Access denied: only UNDERWRITER or ADMIN can disburse loans")

        app = self._app_repo.get_application(application_id)
        if app is None:
            raise KeyError(f"Application {application_id!r} not found")

        # Check existing disbursement
        existing_dsb = self._app_repo.get_disbursement(application_id)
        already_disbursed = existing_dsb is not None or app["status"] == "DISBURSED"

        # Check schedule
        schedule = self._app_repo.get_schedule(application_id)
        has_schedule = schedule is not None

        # Build document dictionary
        policy = self._policy_repo.get_active_policy()
        product_policy = policy.products[app["product"]]
        doc_dict: Dict[str, Document] = {}
        for d in app["documents"]:
            doc_dict[d["doc_type"]] = Document(
                doc_type=d["doc_type"],
                filename=d.get("filename"),
                status=DocumentStatus(d["status"]),
                rejection_reason=d.get("rejection_reason"),
            )

        status_enum = ApplicationStatus(app["status"])
        principal = Decimal(app["amount"])

        result = self.disburse_loan(
            application_id=application_id,
            principal=principal,
            status=status_enum,
            has_schedule=has_schedule,
            required_doc_types=product_policy.required_documents,
            documents=doc_dict,
            released_by=actor.user_id,
            already_disbursed=already_disbursed,
        )

        # Save to database
        self._app_repo.save_disbursement(result.disbursement)
        self._app_repo.update_application_status(
            app_id=application_id,
            status=result.new_status.value,
            outstanding_principal=str(result.outstanding_principal),
            delinquency_bucket=result.delinquency_bucket,
            dpd=result.dpd,
            disbursed_at=result.disbursement.disbursed_at,
        )

        self._app_repo.write_audit(
            actor_user_id=actor.user_id,
            role=actor.role,
            action=result.audit_entry.action,
            application_id=application_id,
            comment=result.audit_entry.comment,
        )

        return result.disbursement

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
