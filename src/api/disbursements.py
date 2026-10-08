"""
Disbursements API — controllers only.
Routes:
  POST /applications/{id}/disburse
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import Actor, require_role
from src.domain.exceptions import (
    AlreadyDisbursedException,
    DocumentsNotVerifiedException,
    InvalidApplicationStateException,
)
from src.services.disbursement_service import DisbursementService


class DisbursementResponse(BaseModel):
    disbursement_id: str
    application_id: str
    amount: str
    funding_source: str
    reference: str
    disbursed_at: str
    released_by: str
    status: str


def make_disbursements_router(disbursement_service: DisbursementService) -> APIRouter:
    router = APIRouter(tags=["disbursements"])

    @router.post("/applications/{app_id}/disburse", response_model=DisbursementResponse)
    def disburse_loan(
        app_id: str,
        actor: Actor = Depends(require_role("UNDERWRITER", "ADMIN")),
    ) -> DisbursementResponse:
        try:
            record = disbursement_service.execute_disbursement(
                actor=actor,
                application_id=app_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except AlreadyDisbursedException as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except DocumentsNotVerifiedException as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)})
        except InvalidApplicationStateException as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        return DisbursementResponse(
            disbursement_id=record.disbursement_id,
            application_id=record.application_id,
            amount=str(record.amount),
            funding_source=record.funding_source,
            reference=record.reference,
            disbursed_at=record.disbursed_at,
            released_by=record.released_by,
            status=record.status,
        )

    return router
