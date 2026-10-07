"""
Application intake API — controllers only.
Auth enforced here; services receive Actor.
Routes: POST /applications, GET /applications/{id}, POST /applications/{id}/documents
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import Actor, require_role, get_actor
from src.domain.exceptions import PolicyViolationException, InvalidApplicationStateException
from src.domain.money import to_money
from src.services.application_service import ApplicationService, SubmitApplicationInput


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class ApplicantIn(BaseModel):
    full_name: str
    age: int
    monthly_income: str      # Decimal string
    pan: str
    aadhaar: str
    credit_history: str      # CLEAN | THIN | LATE_PAYMENTS
    has_default: bool


class DocumentIn(BaseModel):
    doc_type: str
    filename: str


class SubmitApplicationRequest(BaseModel):
    product: str
    amount: str              # Decimal string
    tenure_months: int
    applicant: ApplicantIn
    documents: List[DocumentIn] = []


class DocumentUploadRequest(BaseModel):
    doc_type: str
    filename: str


class DocumentOut(BaseModel):
    doc_type: str
    status: str
    filename: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    status: str
    decision: Optional[str]
    reason_codes: List[str]
    policy_version: int
    score: int
    pan_masked: str
    aadhaar_masked: str
    documents: List[DocumentOut]
    missing_documents: List[str]


def _to_response(app: Dict[str, Any]) -> ApplicationResponse:
    docs_out = [DocumentOut(**d) for d in app["documents"]]
    missing = [d.doc_type for d in docs_out if d.status == "MISSING"]
    return ApplicationResponse(
        id=app["id"],
        status=app["status"],
        decision=app.get("decision"),
        reason_codes=app["reason_codes"],
        policy_version=app["policy_version"],
        score=app["score"],
        pan_masked=app["pan_masked"],
        aadhaar_masked=app["aadhaar_masked"],
        documents=docs_out,
        missing_documents=missing,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Router factory
# ─────────────────────────────────────────────────────────────────────────────

def make_applications_router(app_service: ApplicationService) -> APIRouter:
    router = APIRouter(tags=["applications"])

    @router.post("/applications", status_code=201, response_model=ApplicationResponse)
    def submit_application(
        body: SubmitApplicationRequest,
        actor: Actor = Depends(require_role("CUSTOMER")),
    ) -> ApplicationResponse:
        try:
            app = app_service.submit_application(
                actor,
                SubmitApplicationInput(
                    product=body.product,
                    amount=to_money(body.amount),
                    tenure_months=body.tenure_months,
                    full_name=body.applicant.full_name,
                    age=body.applicant.age,
                    monthly_income=to_money(body.applicant.monthly_income),
                    pan=body.applicant.pan,
                    aadhaar=body.applicant.aadhaar,
                    credit_history=body.applicant.credit_history,
                    has_default=body.applicant.has_default,
                    documents=[d.model_dump() for d in body.documents],
                ),
            )
        except PolicyViolationException as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "POLICY_VIOLATION",
                    "reason_codes": exc.reason_codes,
                    "policy_version": exc.policy_version,
                },
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return _to_response(app)

    @router.get("/applications/{app_id}", response_model=ApplicationResponse)
    def get_application(
        app_id: str,
        actor: Actor = Depends(get_actor),
    ) -> ApplicationResponse:
        try:
            app = app_service.get_application(actor, app_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        return _to_response(app)

    @router.post("/applications/{app_id}/documents", response_model=ApplicationResponse)
    def upload_document(
        app_id: str,
        body: DocumentUploadRequest,
        actor: Actor = Depends(get_actor),
    ) -> ApplicationResponse:
        try:
            app = app_service.upload_document(actor, app_id, body.doc_type, body.filename)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        return _to_response(app)

    return router
