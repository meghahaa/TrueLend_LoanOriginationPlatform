"""
App factory — creates the FastAPI app with all routes wired.
DI happens here and only here.
"""
from __future__ import annotations

import os
import logging

from fastapi import FastAPI

from src.repositories.policy_repository import PolicyRepository
from src.services.product_catalog_service import ProductCatalogService
from src.services.policy_service import PolicyService
from src.api.products import make_products_router
from src.api.admin_policies import make_admin_policies_router


def create_app(policy_dir: str | None = None) -> FastAPI:
    """Create and return the configured FastAPI application."""
    if policy_dir is None:
        policy_dir = os.environ.get("TRUELEND_POLICY_DIR", "policies")

    app = FastAPI(title="TrueLend Loan Origination Platform")

    # Wiring
    policy_repo = PolicyRepository(policy_dir=policy_dir)
    catalog_service = ProductCatalogService(policy_repo=policy_repo)
    policy_service = PolicyService(policy_repo=policy_repo)

    # Routers
    app.include_router(make_products_router(catalog_service))
    app.include_router(make_admin_policies_router(policy_service))

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
