"""
AC-01 — Product catalog lists exactly 3 products from the active policy.

RED test: asserts the GET /products endpoint returns 3 products.
No implementation exists yet — this must fail.
"""
import pytest


@pytest.mark.ac("AC-01")
def test_ac01_product_catalog_lists_three_products():
    """GET /products returns exactly 3 products (PERSONAL, VEHICLE, EDUCATION)."""
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    repo = PolicyRepository(policy_dir="policies")
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    assert len(result.products) == 3, (
        f"Expected 3 products, got {len(result.products)}"
    )


@pytest.mark.ac("AC-01")
def test_ac01_product_catalog_product_codes():
    """The three returned products are PERSONAL, VEHICLE and EDUCATION."""
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    repo = PolicyRepository(policy_dir="policies")
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    codes = {p.product_code for p in result.products}
    assert codes == {"PERSONAL", "VEHICLE", "EDUCATION"}


@pytest.mark.ac("AC-01")
def test_ac01_product_catalog_includes_policy_version():
    """Response includes policy_version (from the active policy file)."""
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    repo = PolicyRepository(policy_dir="policies")
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    assert result.policy_version == 1


@pytest.mark.ac("AC-01")
def test_ac01_product_each_has_required_documents():
    """Every product exposes a non-empty required_documents list."""
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    repo = PolicyRepository(policy_dir="policies")
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    for p in result.products:
        assert p.required_documents, (
            f"{p.product_code} has empty required_documents"
        )


@pytest.mark.ac("AC-01")
def test_ac01_product_thresholds_are_strings(tmp_path):
    """Money fields are returned as strings, not floats (NFR-01)."""
    import json, shutil
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    repo = PolicyRepository(policy_dir=str(tmp_path))
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    for p in result.products:
        assert isinstance(p.min_monthly_income, str)
        assert isinstance(p.annual_rate_percent, str)
        assert isinstance(p.max_foir, str)
        assert isinstance(p.min_amount, str)
        assert isinstance(p.max_amount, str)


@pytest.mark.ac("AC-01a")
def test_ac01a_config_driven_fourth_product(tmp_path):
    """A v002 policy with a fourth product causes 4 products to be returned (config-driven)."""
    import json, shutil
    from src.repositories.policy_repository import PolicyRepository
    from src.services.product_catalog_service import ProductCatalogService

    # Copy v001
    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")

    # Write v002 with an extra product
    with open("policies/loan_policy.v001.json") as fh:
        v2 = json.load(fh)
    v2["version"] = 2
    v2["products"]["HOME"] = {
        "display_name": "Home Loan",
        "min_monthly_income": "50000.00",
        "min_age": 21, "max_age": 65,
        "min_amount": "500000.00", "max_amount": "10000000.00",
        "min_tenure_months": 60, "max_tenure_months": 300,
        "annual_rate_percent": "8.00",
        "approve_score": 750, "reject_score": 600,
        "max_foir": "0.45",
        "required_documents": ["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP", "PROPERTY_DOCS"],
    }
    with open(tmp_path / "loan_policy.v002.json", "w") as fh:
        json.dump(v2, fh)

    repo = PolicyRepository(policy_dir=str(tmp_path))
    service = ProductCatalogService(policy_repo=repo)
    result = service.list_products()

    assert len(result.products) == 4
    assert result.policy_version == 2


@pytest.mark.ac("AC-01b")
def test_ac01b_highest_version_is_active(tmp_path):
    """When v001 and v002 both exist, v002 is the active policy."""
    import json, shutil
    from src.repositories.policy_repository import PolicyRepository

    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    with open("policies/loan_policy.v001.json") as fh:
        v2 = json.load(fh)
    v2["version"] = 2
    with open(tmp_path / "loan_policy.v002.json", "w") as fh:
        json.dump(v2, fh)

    repo = PolicyRepository(policy_dir=str(tmp_path))
    active = repo.get_active_policy()

    assert active.version == 2


@pytest.mark.ac("AC-01b")
def test_ac01b_gaps_in_version_numbers_pick_highest(tmp_path):
    """Gaps in version numbers (v001, v005) → v005 is active."""
    import json, shutil
    from src.repositories.policy_repository import PolicyRepository

    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    with open("policies/loan_policy.v001.json") as fh:
        v5 = json.load(fh)
    v5["version"] = 5
    with open(tmp_path / "loan_policy.v005.json", "w") as fh:
        json.dump(v5, fh)

    repo = PolicyRepository(policy_dir=str(tmp_path))
    active = repo.get_active_policy()

    assert active.version == 5
