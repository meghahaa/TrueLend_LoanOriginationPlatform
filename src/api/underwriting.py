"""
Underwriting API — controllers only.
Auth enforced here; services receive Actor.
Routes:
  GET  /underwriter/queue
  POST /applications/{id}/documents/{doc_type}/verify
  POST /applications/{id}/decision
  POST /admin/applications/{id}/override
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import Actor, require_role
from src.domain.exceptions import (
    DocumentsNotVerifiedException,
    InvalidApplicationStateException,
    InvalidDocumentStateException,
)
from src.services.underwriting_service import UnderwritingService


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class VerifyDocumentRequest(BaseModel):
    status: str             # VERIFIED | REJECTED
    reason: Optional[str] = None


class MakeDecisionRequest(BaseModel):
    action: str             # APPROVE | REJECT
    reason_code: str
    comment: Optional[str] = None


class OverrideRequest(BaseModel):
    reason_code: str
    comment: str


class DocumentOut(BaseModel):
    doc_type: str
    status: str
    filename: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationOut(BaseModel):
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


def _to_out(app: Dict[str, Any]) -> ApplicationOut:
    docs = [DocumentOut(**d) for d in app["documents"]]
    missing = [d.doc_type for d in docs if d.status == "MISSING"]
    return ApplicationOut(
        id=app["id"],
        status=app["status"],
        decision=app.get("decision"),
        reason_codes=app["reason_codes"],
        policy_version=app["policy_version"],
        score=app["score"],
        pan_masked=app["pan_masked"],
        aadhaar_masked=app["aadhaar_masked"],
        documents=docs,
        missing_documents=missing,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Router factory
# ─────────────────────────────────────────────────────────────────────────────

def make_underwriting_router(uw_service: UnderwritingService) -> APIRouter:
    router = APIRouter(tags=["underwriting"])

    @router.get("/underwriter/queue", response_model=List[ApplicationOut])
    def get_queue(
        actor: Actor = Depends(require_role("UNDERWRITER", "ADMIN")),
    ) -> List[ApplicationOut]:
        apps = uw_service.get_queue(actor)
        return [_to_out(a) for a in apps]

    @router.post(
        "/applications/{app_id}/documents/{doc_type}/verify",
        response_model=ApplicationOut,
    )
    def verify_document(
        app_id: str,
        doc_type: str,
        body: VerifyDocumentRequest,
        actor: Actor = Depends(require_role("UNDERWRITER", "ADMIN")),
    ) -> ApplicationOut:
        try:
            app = uw_service.verify_document(
                actor, app_id, doc_type, body.status, body.reason
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except InvalidDocumentStateException as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return _to_out(app)

    @router.post("/applications/{app_id}/decision", response_model=ApplicationOut)
    def make_decision(
        app_id: str,
        body: MakeDecisionRequest,
        actor: Actor = Depends(require_role("UNDERWRITER", "ADMIN")),
    ) -> ApplicationOut:
        try:
            app = uw_service.make_decision(
                actor, app_id, body.action, body.reason_code, body.comment
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except DocumentsNotVerifiedException as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)})
        except InvalidApplicationStateException as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return _to_out(app)

    @router.post(
        "/admin/applications/{app_id}/override",
        response_model=ApplicationOut,
    )
    def admin_override(
        app_id: str,
        body: OverrideRequest,
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> ApplicationOut:
        try:
            app = uw_service.admin_override(
                actor, app_id, body.reason_code, body.comment
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except InvalidApplicationStateException as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return _to_out(app)

    return router
