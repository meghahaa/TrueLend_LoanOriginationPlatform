"""
ApplicationService — orchestrates application intake (AC-02, AC-03, AC-05).
No FastAPI imports; receives Actor and repo by injection.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.credit_score import calculate_credit_score
from src.domain.eligibility_rules import check_policy_gate
from src.domain.exceptions import PolicyViolationException
from src.domain.models import Actor
from src.domain.money import to_money
from src.domain.underwriting_decision import make_underwriting_decision
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubmitApplicationInput:
    product: str
    amount: Decimal
    tenure_months: int
    full_name: str
    age: int
    monthly_income: Decimal
    pan: str
    aadhaar: str
    credit_history: str
    has_default: bool
    documents: List[Dict[str, str]]  # [{"doc_type": ..., "filename": ...}]


class ApplicationService:
    def __init__(
        self,
        policy_repo: PolicyRepository,
        app_repo: ApplicationRepository,
    ) -> None:
        self._policy_repo = policy_repo
        self._app_repo = app_repo

    def submit_application(
        self,
        actor: Actor,
        inp: SubmitApplicationInput,
    ) -> Dict[str, Any]:
        """
        AC-05: Run policy gate first; raise PolicyViolationException on any violation.
        AC-03: Calculate credit score.
        AC-04: Run automated underwriting decision.
        AC-02: Build required document checklist.
        Persist and return the created application.
        """
        policy = self._policy_repo.get_active_policy()

        if inp.product not in policy.products:
            raise ValueError(f"Unknown product: {inp.product!r}")

        product_policy = policy.products[inp.product]

        # AC-05: Policy gate (raises on any violation — nothing persisted)
        check_policy_gate(
            policy=product_policy,
            monthly_income=inp.monthly_income,
            age=inp.age,
            amount=inp.amount,
            tenure_months=inp.tenure_months,
            policy_version=policy.version,
        )

        # AC-03: Credit score
        score = calculate_credit_score(
            age=inp.age,
            monthly_income=inp.monthly_income,
            credit_history=inp.credit_history,
            has_default=inp.has_default,
        )

        # AC-04: Automated underwriting decision
        uw_result = make_underwriting_decision(
            policy=product_policy,
            score=score,
            monthly_income=inp.monthly_income,
            amount=inp.amount,
            tenure_months=inp.tenure_months,
            has_default=inp.has_default,
        )

        # AC-02: Build document checklist
        submitted_docs = {d["doc_type"]: d.get("filename") for d in inp.documents}
        doc_list = []
        for req_doc in product_policy.required_documents:
            if req_doc in submitted_docs:
                doc_list.append({
                    "doc_type": req_doc,
                    "filename": submitted_docs[req_doc],
                    "status": "UPLOADED",
                })
            else:
                doc_list.append({
                    "doc_type": req_doc,
                    "filename": None,
                    "status": "MISSING",
                })

        # Log only ids/codes — never PAN/Aadhaar (NFR-03)
        _log.info(
            "Submitting application: product=%s score=%d decision=%s policy_version=%d",
            inp.product, score, uw_result.decision, policy.version,
        )

        app = self._app_repo.create_application(
            owner_user_id=actor.user_id,
            product=inp.product,
            amount=inp.amount,
            tenure_months=inp.tenure_months,
            full_name=inp.full_name,
            age=inp.age,
            monthly_income=inp.monthly_income,
            pan=inp.pan,
            aadhaar=inp.aadhaar,
            credit_history=inp.credit_history,
            has_default=inp.has_default,
            status=uw_result.status,
            decision=uw_result.decision,
            reason_codes=uw_result.reason_codes,
            policy_version=policy.version,
            score=score,
            documents=doc_list,
        )

        if uw_result.status == "APPROVED":
            from datetime import date
            from src.domain.emi_calculator import generate_repayment_schedule
            schedule = generate_repayment_schedule(
                principal=inp.amount,
                annual_rate_percent=product_policy.annual_rate_percent,
                tenure_months=inp.tenure_months,
                start_date=date.today(),
            )
            self._app_repo.save_schedule(app["id"], schedule)

        return app

    def get_application(self, actor: Actor, app_id: str) -> Dict[str, Any]:
        """
        AC-02a: Get application by id. 404 if not found. 403 if not owner/staff.
        """
        app = self._app_repo.get_application(app_id)
        if app is None:
            raise KeyError(f"Application {app_id!r} not found")

        # Customers can only view their own applications
        if actor.role == "CUSTOMER" and app["owner_user_id"] != actor.user_id:
            raise PermissionError("Access denied")

        return app

    def upload_document(
        self,
        actor: Actor,
        app_id: str,
        doc_type: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        AC-02b: Upload a document. 403 if not owner.
        """
        app = self._app_repo.get_application(app_id)
        if app is None:
            raise KeyError(f"Application {app_id!r} not found")

        if actor.role == "CUSTOMER" and app["owner_user_id"] != actor.user_id:
            raise PermissionError("Access denied")

        self._app_repo.update_document_status(
            application_id=app_id,
            doc_type=doc_type,
            filename=filename,
            status="UPLOADED",
        )

        return self._app_repo.get_application(app_id)  # type: ignore[return-value]
