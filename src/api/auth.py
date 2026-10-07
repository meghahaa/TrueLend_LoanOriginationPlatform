"""
Auth utilities — role-based dependency for FastAPI routes.
Bearer token → Actor. Roles: CUSTOMER, UNDERWRITER, ADMIN.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
from fastapi import Depends, HTTPException, Header


@dataclass(frozen=True)
class Actor:
    user_id: str
    role: str  # "CUSTOMER" | "UNDERWRITER" | "ADMIN"


# Demo token map (synthetic data only)
_DEMO_TOKENS: dict[str, Actor] = {
    "customer-token": Actor(user_id="cust-001", role="CUSTOMER"),
    "underwriter-token": Actor(user_id="uw-001", role="UNDERWRITER"),
    "admin-token": Actor(user_id="admin-001", role="ADMIN"),
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
