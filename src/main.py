"""
App factory — creates the FastAPI app with all routes wired.
DI happens here and only here.
"""
from __future__ import annotations

import os
import logging

from fastapi import FastAPI

from src.repositories.policy_repository import PolicyRepository
from src.repositories.application_repository import ApplicationRepository
from src.services.product_catalog_service import ProductCatalogService
from src.services.policy_service import PolicyService
from src.services.application_service import ApplicationService
from src.services.underwriting_service import UnderwritingService
from src.api.products import make_products_router
from src.api.admin_policies import make_admin_policies_router
from src.api.applications import make_applications_router
from src.api.underwriting import make_underwriting_router


def create_app(
    policy_dir: str | None = None,
    db_path: str | None = None,
) -> FastAPI:
    """Create and return the configured FastAPI application."""
    if policy_dir is None:
        policy_dir = os.environ.get("TRUELEND_POLICY_DIR", "policies")
    if db_path is None:
        db_path = os.environ.get("TRUELEND_DB_PATH", "truelend.db")

    app = FastAPI(title="TrueLend Loan Origination Platform")

    # Repositories
    policy_repo = PolicyRepository(policy_dir=policy_dir)
    app_repo = ApplicationRepository(db_path=db_path)

    # Services
    catalog_service = ProductCatalogService(policy_repo=policy_repo)
    policy_service = PolicyService(policy_repo=policy_repo)
    application_service = ApplicationService(policy_repo=policy_repo, app_repo=app_repo)
    underwriting_service = UnderwritingService(app_repo=app_repo, policy_repo=policy_repo)

    # Routers
    app.include_router(make_products_router(catalog_service))
    app.include_router(make_admin_policies_router(policy_service))
    app.include_router(make_applications_router(application_service))
    app.include_router(make_underwriting_router(underwriting_service))

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
