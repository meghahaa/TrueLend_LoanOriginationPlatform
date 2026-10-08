"""
Portfolio Service — provides portfolio metrics, application filtering/search, and audit log queries.
Pure service layer; no framework imports.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.domain.models import Actor
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository


class PortfolioService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        policy_repo: PolicyRepository,
    ) -> None:
        self._app_repo = app_repo
        self._policy_repo = policy_repo

    def list_applications(
        self,
        *,
        actor: Actor,
        status: Optional[str] = None,
        product: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if actor.role != "ADMIN":
            raise PermissionError("Access denied: ADMIN role required")

        valid_statuses = {"SUBMITTED", "MANUAL_REVIEW", "APPROVED", "REJECTED", "DISBURSED"}
        valid_products = {"PERSONAL", "VEHICLE", "EDUCATION"}

        if status and status not in valid_statuses:
            raise ValueError(f"Invalid status filter: {status!r}")
        if product and product not in valid_products:
            raise ValueError(f"Invalid product filter: {product!r}")

        page_size = min(max(1, page_size), 100)
        page = max(1, page)

        return self._app_repo.list_applications(
            status=status,
            product=product,
            page=page,
            page_size=page_size,
        )

    def get_portfolio_metrics(
        self,
        *,
        actor: Actor,
        as_of: Optional[date] = None,
    ) -> Dict[str, Any]:
        if actor.role != "ADMIN":
            raise PermissionError("Access denied: ADMIN role required")

        today = as_of or date.today()
        disbursed_apps = self._app_repo.list_disbursed_applications()

        per_product: Dict[str, Dict[str, Any]] = {}
        for p in ["PERSONAL", "VEHICLE", "EDUCATION"]:
            per_product[p] = {
                "count": 0,
                "disbursed_amount": "0.00",
                "outstanding_principal": "0.00",
            }

        per_bucket: Dict[str, Dict[str, Any]] = {
            "CURRENT": {"count": 0, "outstanding_principal": "0.00"},
            "DPD-30": {"count": 0, "outstanding_principal": "0.00"},
            "DPD-60": {"count": 0, "outstanding_principal": "0.00"},
            "DPD-90": {"count": 0, "outstanding_principal": "0.00"},
            "NPA": {"count": 0, "outstanding_principal": "0.00"},
        }

        total_overdue = Decimal("0.00")
        npa_count = 0
        npa_outstanding = Decimal("0.00")

        for app in disbursed_apps:
            prod = app["product"]
            amount = Decimal(app["amount"])
            outstanding = Decimal(app["outstanding_principal"] or app["amount"])
            bucket = app["delinquency_bucket"] or "CURRENT"

            # Per product
            if prod in per_product:
                per_product[prod]["count"] += 1
                curr_disb = Decimal(per_product[prod]["disbursed_amount"]) + amount
                curr_out = Decimal(per_product[prod]["outstanding_principal"]) + outstanding
                per_product[prod]["disbursed_amount"] = f"{curr_disb:.2f}"
                per_product[prod]["outstanding_principal"] = f"{curr_out:.2f}"

            # Per bucket
            if bucket in per_bucket:
                per_bucket[bucket]["count"] += 1
                curr_b_out = Decimal(per_bucket[bucket]["outstanding_principal"]) + outstanding
                per_bucket[bucket]["outstanding_principal"] = f"{curr_b_out:.2f}"

            # NPA metrics
            if bucket == "NPA":
                npa_count += 1
                npa_outstanding += outstanding

            # Calculate overdue installments (due date < today)
            schedule = self._app_repo.get_schedule(app["id"])
            if schedule:
                allocations = self._app_repo.get_allocations(app["id"])
                paid_per_inst: Dict[int, Decimal] = {}
                for a in allocations:
                    paid_per_inst[a.installment_number] = (
                        paid_per_inst.get(a.installment_number, Decimal("0.00"))
                        + a.interest_allocated
                        + a.principal_allocated
                    )
                for row in schedule.rows:
                    if row.due_date < today:
                        paid = paid_per_inst.get(row.installment_number, Decimal("0.00"))
                        unpaid = max(Decimal("0.00"), row.emi_amount - paid)
                        total_overdue += unpaid

        return {
            "per_product": per_product,
            "per_bucket": per_bucket,
            "npa_count": npa_count,
            "npa_outstanding": f"{npa_outstanding:.2f}",
            "total_overdue": f"{total_overdue:.2f}",
        }

    def get_audit_trail(
        self,
        *,
        actor: Actor,
        application_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if actor.role != "ADMIN":
            raise PermissionError("Access denied: ADMIN role required")
        return self._app_repo.get_audit_log(application_id)
