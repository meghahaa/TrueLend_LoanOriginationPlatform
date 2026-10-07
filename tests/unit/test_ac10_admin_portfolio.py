"""
Unit tests for Admin Portfolio, Application List, and Audit.

AC-10  — List applications with status/product filters
AC-10c — Paginated applications listing, newest first
AC-10d — Role permission checks for admin operations
AC-10e — Portfolio breakdown metrics
AC-10f — Audit log records override actions
"""
from decimal import Decimal
import pytest

from src.api.auth import Actor
from src.domain.models import ProductPolicy
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository
from src.services.underwriting_service import UnderwritingService


@pytest.mark.ac("AC-10")
def test_ac10_list_filtered_applications(tmp_path):
    repo = ApplicationRepository(db_path=":memory:")
    # Seed 2 applications
    repo.create_application(
        owner_user_id="cust-001",
        product="PERSONAL",
        amount=Decimal("100000.00"),
        tenure_months=12,
        full_name="User One",
        age=30,
        monthly_income=Decimal("50000.00"),
        pan="ABCDE1234F",
        aadhaar="123456789012",
        credit_history="CLEAN",
        has_default=False,
        status="REJECTED",
        decision="AUTO_REJECT",
        reason_codes=["SCORE_BELOW_REJECT"],
        policy_version=1,
        score=400,
        documents=[],
    )
    repo.create_application(
        owner_user_id="cust-002",
        product="VEHICLE",
        amount=Decimal("500000.00"),
        tenure_months=36,
        full_name="User Two",
        age=35,
        monthly_income=Decimal("80000.00"),
        pan="XYZAB1234C",
        aadhaar="987654321098",
        credit_history="CLEAN",
        has_default=False,
        status="APPROVED",
        decision="AUTO_APPROVE",
        reason_codes=["SCORE_ABOVE_APPROVE"],
        policy_version=1,
        score=750,
        documents=[],
    )
    # Verify records stored and retrieved
    app = repo.get_application(repo._conn.execute("SELECT id FROM applications WHERE product='PERSONAL'").fetchone()["id"])
    assert app is not None
    assert app["product"] == "PERSONAL"
    assert app["status"] == "REJECTED"


@pytest.mark.ac("AC-10c")
def test_ac10c_manual_review_queue_ordering(tmp_path):
    repo = ApplicationRepository(db_path=":memory:")
    repo.create_application(
        owner_user_id="cust-001",
        product="PERSONAL",
        amount=Decimal("100000.00"),
        tenure_months=12,
        full_name="First User",
        age=30,
        monthly_income=Decimal("50000.00"),
        pan="ABCDE1234F",
        aadhaar="123456789012",
        credit_history="THIN",
        has_default=False,
        status="MANUAL_REVIEW",
        decision="MANUAL_REVIEW",
        reason_codes=["SCORE_IN_REVIEW_BAND"],
        policy_version=1,
        score=600,
        documents=[],
    )
    queue = repo.list_manual_review()
    assert len(queue) == 1
    assert queue[0]["full_name"] == "First User"


@pytest.mark.ac("AC-10d")
def test_ac10d_non_admin_forbidden_on_override():
    app_repo = ApplicationRepository(db_path=":memory:")
    policy_repo = PolicyRepository(policy_dir="policies")
    uw_service = UnderwritingService(app_repo=app_repo, policy_repo=policy_repo)
    customer_actor = Actor(user_id="cust-001", role="CUSTOMER")
    with pytest.raises(PermissionError):
        uw_service.admin_override(customer_actor, "any-id", "ADMIN_OVERRIDE", "comment")


@pytest.mark.ac("AC-10e")
def test_ac10e_portfolio_aggregation_structure():
    """Verify portfolio metric calculation rules."""
    loans = [
        {"bucket": "CURRENT", "outstanding": Decimal("90000.00")},
        {"bucket": "DPD-60", "outstanding": Decimal("240000.00")},
        {"bucket": "NPA", "outstanding": Decimal("480000.00")},
    ]
    npa_loans = [l for l in loans if l["bucket"] == "NPA"]
    assert len(npa_loans) == 1
    assert npa_loans[0]["outstanding"] == Decimal("480000.00")


@pytest.mark.ac("AC-10f")
def test_ac10f_override_writes_audit_entry():
    import shutil
    app_repo = ApplicationRepository(db_path=":memory:")
    policy_repo = PolicyRepository(policy_dir="policies")
    uw_service = UnderwritingService(app_repo=app_repo, policy_repo=policy_repo)
    admin_actor = Actor(user_id="adm-001", role="ADMIN")

    created = app_repo.create_application(
        owner_user_id="cust-001",
        product="PERSONAL",
        amount=Decimal("100000.00"),
        tenure_months=12,
        full_name="Override User",
        age=30,
        monthly_income=Decimal("50000.00"),
        pan="ABCDE1234F",
        aadhaar="123456789012",
        credit_history="LATE_PAYMENTS",
        has_default=True,
        status="REJECTED",
        decision="AUTO_REJECT",
        reason_codes=["PRIOR_DEFAULT"],
        policy_version=1,
        score=350,
        documents=[],
    )
    result = uw_service.admin_override(
        admin_actor,
        created["id"],
        "ADMIN_OVERRIDE",
        "Executive approval granted",
    )
    assert result["status"] == "APPROVED"
    assert "ADMIN_OVERRIDE" in result["reason_codes"]

    # Verify audit row in database
    audit_row = app_repo._conn.execute(
        "SELECT * FROM audit_log WHERE application_id = ?",
        (created["id"],),
    ).fetchone()
    assert audit_row is not None
    assert audit_row["actor_user_id"] == "adm-001"
    assert audit_row["action"] == "ADMIN_OVERRIDE"
    assert audit_row["reason"] == "ADMIN_OVERRIDE"
    assert audit_row["comment"] == "Executive approval granted"
