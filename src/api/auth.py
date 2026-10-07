"""
Auth utilities — role-based dependency for FastAPI routes.
Bearer token → Actor. Roles: CUSTOMER, UNDERWRITER, ADMIN.
"""
from __future__ import annotations

from typing import Callable, Optional
from fastapi import Depends, HTTPException, Header

from src.domain.models import Actor


# Demo token map (synthetic data only — per app_spec.md §2)
_DEMO_TOKENS: dict[str, Actor] = {
    # Short aliases used in tests
    "customer-token": Actor(user_id="cust-001", role="CUSTOMER"),
    "customer-token-2": Actor(user_id="cust-002", role="CUSTOMER"),
    "underwriter-token": Actor(user_id="uw-001", role="UNDERWRITER"),
    "admin-token": Actor(user_id="admin-001", role="ADMIN"),
    # Spec-named tokens (app_spec.md §2)
    "demo-customer-1": Actor(user_id="cust-001", role="CUSTOMER"),
    "demo-customer-2": Actor(user_id="cust-002", role="CUSTOMER"),
    "demo-underwriter-1": Actor(user_id="uw-001", role="UNDERWRITER"),
    "demo-admin-1": Actor(user_id="adm-001", role="ADMIN"),
}


def get_actor(authorization: Optional[str] = Header(default=None)) -> Actor:
    """Resolve the Bearer token to an Actor. 401 if missing/unknown."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    actor = _DEMO_TOKENS.get(token)
    if actor is None:
        raise HTTPException(status_code=401, detail="Unknown token")
    return actor


def require_role(*roles: str) -> Callable:
    """FastAPI dependency factory: 403 if actor's role is not in roles."""
    def _check(actor: Actor = Depends(get_actor)) -> Actor:
        if actor.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {actor.role!r} not permitted")
        return actor
    return _check
