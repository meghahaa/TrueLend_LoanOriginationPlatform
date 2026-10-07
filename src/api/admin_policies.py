"""
Admin policy routes:
  GET  /admin/policies         — list all versions (ADMIN)
  POST /admin/policies         — publish new version (ADMIN)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from src.api.auth import Actor, require_role
from src.domain.policy_validator import PolicyValidationError
from src.services.policy_service import PolicyService


class PolicyVersionOut(BaseModel):
    version: int
    effective_from: str
    created_by: str
    change_note: str


class PublishPolicyIn(BaseModel):
    products: Optional[Dict[str, Any]] = None
    change_note: str


class PublishPolicyOut(BaseModel):
    version: int


def make_admin_policies_router(policy_service: PolicyService) -> APIRouter:
    """Factory: creates a fresh APIRouter per call, closes over the injected service."""
    router = APIRouter(prefix="/admin/policies", tags=["admin-policies"])

    @router.get("", response_model=List[PolicyVersionOut])
    def list_versions(actor: Actor = Depends(require_role("ADMIN"))) -> List[PolicyVersionOut]:
        return [PolicyVersionOut(**v) for v in policy_service.list_versions()]

    @router.post("", response_model=PublishPolicyOut, status_code=201)
    def publish_policy(
        body: PublishPolicyIn,
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> PublishPolicyOut:
        try:
            new_version = policy_service.publish_new_version(
                partial_update={"products": body.products or {}},
                change_note=body.change_note,
                created_by=actor.user_id,
            )
        except PolicyValidationError as exc:
            raise HTTPException(status_code=422, detail={"messages": exc.messages})
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return PublishPolicyOut(version=new_version)

    return router
