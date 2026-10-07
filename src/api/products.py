"""
GET /products — unauthenticated endpoint (per api/CLAUDE.md).
Returns all products from the active policy with policy_version.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from src.services.product_catalog_service import ProductCatalogService


class ProductOut(BaseModel):
    product_code: str
    display_name: str
    min_monthly_income: str
    min_age: int
    max_age: int
    min_amount: str
    max_amount: str
    min_tenure_months: int
    max_tenure_months: int
    annual_rate_percent: str
    approve_score: int
    reject_score: int
    max_foir: str
    required_documents: List[str]


class ProductCatalogResponse(BaseModel):
    policy_version: int
    products: List[ProductOut]


def make_products_router(catalog_service: ProductCatalogService) -> APIRouter:
    """Factory: creates a fresh APIRouter per call, closes over the injected service."""
    router = APIRouter(tags=["products"])

    @router.get("/products", response_model=ProductCatalogResponse)
    def list_products() -> ProductCatalogResponse:
        result = catalog_service.list_products()
        return ProductCatalogResponse(
            policy_version=result.policy_version,
            products=[
                ProductOut(**p.__dict__)
                for p in result.products
            ],
        )

    return router
