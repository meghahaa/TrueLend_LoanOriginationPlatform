"""
Admin Portfolio API — controllers for application search, portfolio health, and audit trail.
Routes:
  GET /admin/applications
  GET /admin/portfolio
  GET /admin/audit
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.auth import Actor, require_role
from src.services.portfolio_service import PortfolioService


class ApplicationItemOut(BaseModel):
    id: str
    owner_user_id: str
    product: str
    amount: str
    tenure_months: int
    full_name: str
    applicant_name: Optional[str] = None
    age: int
    monthly_income: str
    pan_masked: str
    aadhaar_masked: str
    masked_pan: Optional[str] = None
    masked_aadhaar: Optional[str] = None
    credit_history: str
    has_default: bool
    status: str
    decision: Optional[str] = None
    reason_codes: List[str] = []
    policy_version: int
    score: int
    outstanding_principal: Optional[str] = None
    delinquency_bucket: Optional[str] = None
    dpd: Optional[int] = 0
    disbursed_at: Optional[str] = None
    documents: List[Any] = []



class ApplicationsListResponse(BaseModel):
    items: List[ApplicationItemOut]
    total: int
    page: int
    page_size: int


class ProductMetric(BaseModel):
    count: int
    disbursed_amount: str
    outstanding_principal: str


class BucketMetric(BaseModel):
    count: int
    outstanding_principal: str


class PortfolioMetricsResponse(BaseModel):
    per_product: Dict[str, ProductMetric]
    per_bucket: Dict[str, BucketMetric]
    npa_count: int
    npa_outstanding: str
    total_overdue: str


class AuditEntryOut(BaseModel):
    id: str
    user_id: str
    role: str
    action: str
    application_id: Optional[str] = None
    doc_type: Optional[str] = None
    reason_code: Optional[str] = None
    comment: Optional[str] = None
    timestamp: Optional[str] = None


def make_admin_portfolio_router(portfolio_service: PortfolioService) -> APIRouter:
    router = APIRouter(tags=["admin-portfolio"])

    @router.get("/admin/applications", response_model=ApplicationsListResponse)
    def list_applications(
        status: Optional[str] = None,
        product: Optional[str] = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> ApplicationsListResponse:
        try:
            items, total = portfolio_service.list_applications(
                actor=actor,
                status=status,
                product=product,
                page=page,
                page_size=page_size,
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        items_out = [
            ApplicationItemOut(
                id=a["id"],
                owner_user_id=a["owner_user_id"],
                product=a["product"],
                amount=a["amount"],
                tenure_months=a["tenure_months"],
                full_name=a["full_name"],
                applicant_name=a["full_name"],
                age=a["age"],
                monthly_income=a["monthly_income"],
                pan_masked=a["pan_masked"],
                aadhaar_masked=a["aadhaar_masked"],
                masked_pan=a["pan_masked"],
                masked_aadhaar=a["aadhaar_masked"],
                credit_history=a["credit_history"],
                has_default=a["has_default"],
                status=a["status"],
                decision=a.get("decision"),
                reason_codes=a.get("reason_codes", []),
                policy_version=a["policy_version"],
                score=a["score"],
                outstanding_principal=a.get("outstanding_principal"),
                delinquency_bucket=a.get("delinquency_bucket"),
                dpd=a.get("dpd", 0),
                disbursed_at=a.get("disbursed_at"),
                documents=a.get("documents", []),
            )
            for a in items
        ]

        return ApplicationsListResponse(
            items=items_out,
            total=total,
            page=page,
            page_size=page_size,
        )

    @router.get("/admin/portfolio", response_model=PortfolioMetricsResponse)
    def get_portfolio(
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> PortfolioMetricsResponse:
        try:
            metrics = portfolio_service.get_portfolio_metrics(actor=actor)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")

        return PortfolioMetricsResponse(**metrics)

    @router.get("/admin/audit", response_model=List[AuditEntryOut])
    def get_audit_trail(
        application_id: Optional[str] = None,
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> List[AuditEntryOut]:
        try:
            rows = portfolio_service.get_audit_trail(actor=actor, application_id=application_id)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")

        return [AuditEntryOut(**r) for r in rows]

    return router
