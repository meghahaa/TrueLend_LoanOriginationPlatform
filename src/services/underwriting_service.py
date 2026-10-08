"""
UnderwritingService — orchestrates document verification, manual decisions, and admin overrides.
Covers AC-06, AC-04 (status transitions), AC-10.
No FastAPI imports; receives Actor and repos by injection.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.domain.exceptions import (
    DocumentsNotVerifiedException,
    InvalidApplicationStateException,
    InvalidDocumentStateException,
)
from src.domain.models import Actor, Document, DocumentStatus
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository

_log = logging.getLogger(__name__)


class UnderwritingService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        policy_repo: PolicyRepository,
    ) -> None:
        self._app_repo = app_repo
        self._policy_repo = policy_repo

    def get_queue(self, actor: Actor) -> List[Dict[str, Any]]:
        """
        AC-06: GET /underwriter/queue — MANUAL_REVIEW applications, oldest first.
        """
        if actor.role not in ("UNDERWRITER", "ADMIN"):
            raise PermissionError("Access denied")
        return self._app_repo.list_manual_review()

    def verify_document(
        self,
        actor: Actor,
        app_id: str,
        doc_type: str,
        status: str,       # "VERIFIED" | "REJECTED"
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AC-06: Mark an UPLOADED document VERIFIED or REJECTED. Audited.
        AC-06a: REJECTED without reason → ValueError (422).
        AC-06b: MISSING/already VERIFIED → InvalidDocumentStateException (409).
        AC-06c: CUSTOMER → PermissionError (403).
        """
        if actor.role not in ("UNDERWRITER", "ADMIN"):
            raise PermissionError("Access denied")

        app = self._app_repo.get_application(app_id)
        if app is None:
            raise KeyError(f"Application {app_id!r} not found")

        # Find the document
        doc_map = {d["doc_type"]: d for d in app["documents"]}
        if doc_type not in doc_map:
            raise KeyError(f"Document {doc_type!r} not found on application {app_id!r}")

        raw_doc = doc_map[doc_type]
        current_status = raw_doc["status"]

        if current_status != "UPLOADED":
            raise InvalidDocumentStateException(
                f"Document '{doc_type}' has status '{current_status}', only UPLOADED documents can be verified."
            )

        if status == "REJECTED":
            if not reason or not reason.strip():
                raise ValueError("Reason is mandatory when rejecting a document.")

        self._app_repo.update_document_status(
            application_id=app_id,
            doc_type=doc_type,
            filename=raw_doc.get("filename"),
            status=status,
            rejection_reason=reason if status == "REJECTED" else None,
        )

        self._app_repo.write_audit(
            actor_user_id=actor.user_id,
            action="VERIFY_DOCUMENT",
            application_id=app_id,
            doc_type=doc_type,
            reason=reason,
            comment=f"Marked {doc_type} as {status}",
        )

        return self._app_repo.get_application(app_id)  # type: ignore[return-value]

    def make_decision(
        self,
        actor: Actor,
        app_id: str,
        action: str,          # "APPROVE" | "REJECT"
        reason_code: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AC-06d: Manual APPROVE/REJECT from MANUAL_REVIEW.
        APPROVE requires all required docs VERIFIED; else 409 DOCUMENTS_NOT_VERIFIED.
        REJECT → REJECTED + MANUAL_REJECTED. Audited.
        """
        if actor.role not in ("UNDERWRITER", "ADMIN"):
            raise PermissionError("Access denied")

        app = self._app_repo.get_application(app_id)
        if app is None:
            raise KeyError(f"Application {app_id!r} not found")

        if app["status"] != "MANUAL_REVIEW":
            raise InvalidApplicationStateException(
                f"Application {app_id!r} is not in MANUAL_REVIEW (status={app['status']!r})"
            )

        if action == "APPROVE":
            policy = self._policy_repo.get_active_policy()
            product_policy = policy.products[app["product"]]
            doc_map = {d["doc_type"]: d for d in app["documents"]}
            for req_doc in product_policy.required_documents:
                doc = doc_map.get(req_doc)
                if doc is None or doc["status"] != "VERIFIED":
                    raise DocumentsNotVerifiedException(
                        f"Required document '{req_doc}' is not verified."
                    )
            new_status = "APPROVED"
            new_codes = ["MANUAL_APPROVED"]
            new_decision = "AUTO_APPROVE"  # manual path, store as MANUAL_REVIEW decision

        elif action == "REJECT":
            new_status = "REJECTED"
            new_codes = ["MANUAL_REJECTED"]
            new_decision = "MANUAL_REVIEW"
        else:
            raise ValueError(f"Unknown action: {action!r}")

        self._app_repo.update_application_status(
            app_id=app_id,
            status=new_status,
            decision=new_decision,
            reason_codes=new_codes,
        )

        if new_status == "APPROVED":
            from datetime import date
            from decimal import Decimal
            from src.domain.emi_calculator import generate_repayment_schedule
            policy = self._policy_repo.get_active_policy()
            product_policy = policy.products[app["product"]]
            schedule = generate_repayment_schedule(
                principal=Decimal(app["amount"]),
                annual_rate_percent=product_policy.annual_rate_percent,
                tenure_months=int(app["tenure_months"]),
                start_date=date.today(),
            )
            try:
                self._app_repo.save_schedule(app_id, schedule)
            except FileExistsError:
                pass

        self._app_repo.write_audit(
            actor_user_id=actor.user_id,
            action=f"MANUAL_{action}",
            application_id=app_id,
            reason=reason_code,
            comment=comment,
        )

        return self._app_repo.get_application(app_id)  # type: ignore[return-value]

    def admin_override(
        self,
        actor: Actor,
        app_id: str,
        reason_code: str,
        comment: str,
    ) -> Dict[str, Any]:
        """
        AC-10: Override an AUTO_REJECT application → APPROVED + schedule.
        AC-10b: Missing reason/comment → ValueError (422).
                UNDERWRITER/CUSTOMER → PermissionError (403).
                Non AUTO_REJECT → InvalidApplicationStateException (409).
        """
        if actor.role != "ADMIN":
            raise PermissionError("Access denied: ADMIN role required")

        if not reason_code or not reason_code.strip():
            raise ValueError("reason_code is mandatory for override")
        if not comment or not comment.strip():
            raise ValueError("comment is mandatory for override")

        app = self._app_repo.get_application(app_id)
        if app is None:
            raise KeyError(f"Application {app_id!r} not found")

        # Only AUTO_REJECT with REJECTED status can be overridden (not manual rejections)
        if app["decision"] != "AUTO_REJECT" or app["status"] != "REJECTED":
            raise InvalidApplicationStateException(
                f"Override only applies to AUTO_REJECT applications (current: decision={app['decision']!r}, status={app['status']!r})"
            )

        new_codes = list(app["reason_codes"]) + ["ADMIN_OVERRIDE"]

        self._app_repo.update_application_status(
            app_id=app_id,
            status="APPROVED",
            decision="AUTO_REJECT",   # original decision preserved
            reason_codes=new_codes,
        )

        from datetime import date
        from decimal import Decimal
        from src.domain.emi_calculator import generate_repayment_schedule
        policy = self._policy_repo.get_active_policy()
        product_policy = policy.products[app["product"]]
        schedule = generate_repayment_schedule(
            principal=Decimal(app["amount"]),
            annual_rate_percent=product_policy.annual_rate_percent,
            tenure_months=int(app["tenure_months"]),
            start_date=date.today(),
        )
        try:
            self._app_repo.save_schedule(app_id, schedule)
        except FileExistsError:
            pass

        self._app_repo.write_audit(
            actor_user_id=actor.user_id,
            action="ADMIN_OVERRIDE",
            application_id=app_id,
            reason=reason_code,
            comment=comment,
        )

        return self._app_repo.get_application(app_id)  # type: ignore[return-value]
