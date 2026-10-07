"""
ProductCatalogService — lists products from the active policy.
No FastAPI imports; receives repo by injection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from src.repositories.policy_repository import PolicyRepository


@dataclass(frozen=True)
class ProductDTO:
    product_code: str
    display_name: str
    min_monthly_income: str   # Decimal serialised as string (NFR-01)
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


@dataclass(frozen=True)
class ProductCatalogResult:
    policy_version: int
    products: List[ProductDTO]


class ProductCatalogService:
    def __init__(self, policy_repo: PolicyRepository) -> None:
        self._repo = policy_repo

    def list_products(self) -> ProductCatalogResult:
        """Return all products in the active policy with policy_version."""
        policy = self._repo.get_active_policy()
        products = [
            ProductDTO(
                product_code=p.product_code,
                display_name=p.display_name,
                min_monthly_income=str(p.min_monthly_income),
                min_age=p.min_age,
                max_age=p.max_age,
                min_amount=str(p.min_amount),
                max_amount=str(p.max_amount),
                min_tenure_months=p.min_tenure_months,
                max_tenure_months=p.max_tenure_months,
                annual_rate_percent=str(p.annual_rate_percent),
                approve_score=p.approve_score,
                reject_score=p.reject_score,
                max_foir=str(p.max_foir),
                required_documents=p.required_documents,
            )
            for p in policy.products.values()
        ]
        return ProductCatalogResult(policy_version=policy.version, products=products)
