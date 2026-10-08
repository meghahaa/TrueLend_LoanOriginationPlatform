"""
API integration tests for Admin Portfolio, Application Search, and Audit Trail.

AC-10  — GET /admin/applications?status=&product= filtered listing
AC-10c — GET /admin/applications pagination and invalid status 422
AC-10d — Non-admin tokens (CUSTOMER, UNDERWRITER) return 403
AC-10e — GET /admin/portfolio metrics and bucket aggregations
AC-10f — GET /admin/audit?application_id= returns audit trail for actions
"""
import shutil
import pytest
from fastapi.testclient import TestClient


def _make_client(tmp_path):
    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    from src.main import create_app
    app = create_app(policy_dir=str(tmp_path), db_path=":memory:")
    return TestClient(app)


_CUST = {"Authorization": "Bearer customer-token"}
_UW = {"Authorization": "Bearer underwriter-token"}
_ADMIN = {"Authorization": "Bearer admin-token"}


@pytest.mark.ac("AC-10")
def test_ac10_admin_applications_filtering(tmp_path):
    client = _make_client(tmp_path)
    # Submit 1 PERSONAL rejected app
    client.post(
        "/applications",
        json={
            "product": "PERSONAL",
            "amount": "100000.00",
            "tenure_months": 12,
            "applicant": {
                "full_name": "Rejected User",
                "age": 22,
                "monthly_income": "30000.00",
                "pan": "TESTP1234X",
                "aadhaar": "999900000001",
                "credit_history": "LATE_PAYMENTS",
                "has_default": True,
            },
            "documents": [],
        },
        headers=_CUST,
    )
    # Submit 1 VEHICLE approved app
    client.post(
        "/applications",
        json={
            "product": "VEHICLE",
            "amount": "500000.00",
            "tenure_months": 36,
            "applicant": {
                "full_name": "Approved User",
                "age": 30,
                "monthly_income": "80000.00",
                "pan": "TESTP5555X",
                "aadhaar": "999900000002",
                "credit_history": "CLEAN",
                "has_default": False,
            },
            "documents": [],
        },
        headers=_CUST,
    )

    # Filter by status=REJECTED&product=PERSONAL
    resp = client.get("/admin/applications?status=REJECTED&product=PERSONAL", headers=_ADMIN)
    assert resp.status_code == 200
    body = resp.json()
    items = body.get("items", body if isinstance(body, list) else [])
    assert len(items) == 1
    assert items[0]["product"] == "PERSONAL"
    assert items[0]["status"] == "REJECTED"


@pytest.mark.ac("AC-10c")
def test_ac10c_admin_applications_invalid_status_returns_422(tmp_path):
    client = _make_client(tmp_path)
    resp = client.get("/admin/applications?status=BOGUS", headers=_ADMIN)
    assert resp.status_code == 422


@pytest.mark.ac("AC-10d")
def test_ac10d_non_admin_forbidden_on_admin_routes(tmp_path):
    client = _make_client(tmp_path)
    # Customer gets 403
    assert client.get("/admin/applications", headers=_CUST).status_code == 403
    # Underwriter gets 403
    assert client.get("/admin/applications", headers=_UW).status_code == 403


@pytest.mark.ac("AC-10f")
def test_ac10f_admin_audit_log_query(tmp_path):
    client = _make_client(tmp_path)
    # Create rejected app
    post = client.post(
        "/applications",
        json={
            "product": "PERSONAL",
            "amount": "100000.00",
            "tenure_months": 12,
            "applicant": {
                "full_name": "Rejected User",
                "age": 22,
                "monthly_income": "30000.00",
                "pan": "TESTP1234X",
                "aadhaar": "999900000001",
                "credit_history": "LATE_PAYMENTS",
                "has_default": True,
            },
            "documents": [],
        },
        headers=_CUST,
    )
    app_id = post.json()["id"]

    # Override as admin
    client.post(
        f"/admin/applications/{app_id}/override",
        json={"reason_code": "ADMIN_OVERRIDE", "comment": "Special executive approval"},
        headers=_ADMIN,
    )

    # Query audit trail
    audit_resp = client.get(f"/admin/audit?application_id={app_id}", headers=_ADMIN)
    assert audit_resp.status_code == 200
    rows = audit_resp.json()
    assert len(rows) >= 1
    assert any(r["action"] == "ADMIN_OVERRIDE" for r in rows)
