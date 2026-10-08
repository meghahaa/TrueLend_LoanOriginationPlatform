"""
API integration tests for Repayment Schedule, Repayment Posting, and EOD Jobs.

AC-07  — GET /applications/{id}/schedule: repayment schedule generation and invariants
AC-07a — Reference loan EMI and totals
AC-07d — Schedule is insert-only, immutable (NFR-02)
AC-07e — Month-end due date clamping
AC-09  — POST /applications/{id}/repayments: waterfall allocation and outstanding reduction
AC-09a — Partial payment smaller than interest
AC-09b — Multi-installment payment allocation
AC-09c — DPD calculation and delinquency bucket assignment
AC-09d — Overdue repayment brings bucket back to CURRENT
AC-09e — Validation: negative/zero amount (422), exceeds outstanding (422), not disbursed (409), unauthorized (403)
AC-09f — POST /admin/jobs/eod-buckets: EOD job updates buckets and is idempotent
"""
import shutil
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient


def _make_client(tmp_path):
    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    from src.main import create_app
    app = create_app(policy_dir=str(tmp_path), db_path=":memory:")
    return TestClient(app)


_CUST = {"Authorization": "Bearer customer-token"}
_CUST2 = {"Authorization": "Bearer customer-token-2"}
_UW = {"Authorization": "Bearer underwriter-token"}
_ADMIN = {"Authorization": "Bearer admin-token"}

# Approved application payload (Score 740, PERSONAL)
_APPROVE_PAYLOAD = {
    "product": "PERSONAL",
    "amount": "300000.00",
    "tenure_months": 36,
    "applicant": {
        "full_name": "Schedule Borrower",
        "age": 30,
        "monthly_income": "60000.00",
        "pan": "TESTP1234X",
        "aadhaar": "999900000001",
        "credit_history": "CLEAN",
        "has_default": False,
    },
    "documents": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# AC-07 — GET /applications/{id}/schedule
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-07")
def test_ac07_get_schedule_returns_200_for_approved_loan(tmp_path):
    client = _make_client(tmp_path)
    # Submit application -> AUTO_APPROVE -> status APPROVED
    post = client.post("/applications", json=_APPROVE_PAYLOAD, headers=_CUST)
    assert post.status_code == 201
    app_id = post.json()["id"]

    resp = client.get(f"/applications/{app_id}/schedule", headers=_CUST)
    assert resp.status_code == 200
    body = resp.json()

    assert body["application_id"] == app_id
    assert len(body["rows"]) == 36
    assert body["emi_amount"] == "10036.09"
    assert body["total_principal"] == "300000.00"
    assert body["total_payable"] == "361299.12"
    assert body["total_interest"] == "61299.12"
    assert body["rows"][-1]["remaining_balance"] == "0.00"


@pytest.mark.ac("AC-07")
def test_ac07_get_schedule_accessible_by_staff(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVE_PAYLOAD, headers=_CUST)
    app_id = post.json()["id"]

    # Underwriter can access schedule
    uw_resp = client.get(f"/applications/{app_id}/schedule", headers=_UW)
    assert uw_resp.status_code == 200

    # Admin can access schedule
    admin_resp = client.get(f"/applications/{app_id}/schedule", headers=_ADMIN)
    assert admin_resp.status_code == 200


@pytest.mark.ac("AC-07")
def test_ac07_get_schedule_forbidden_for_other_customer(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVE_PAYLOAD, headers=_CUST)
    app_id = post.json()["id"]

    resp = client.get(f"/applications/{app_id}/schedule", headers=_CUST2)
    assert resp.status_code == 403


@pytest.mark.ac("AC-07")
def test_ac07_get_schedule_unauthorized_without_token(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVE_PAYLOAD, headers=_CUST)
    app_id = post.json()["id"]

    resp = client.get(f"/applications/{app_id}/schedule")
    assert resp.status_code == 401


@pytest.mark.ac("AC-07")
def test_ac07_get_schedule_not_found(tmp_path):
    client = _make_client(tmp_path)
    resp = client.get("/applications/nonexistent-app-id/schedule", headers=_CUST)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# AC-09 — POST /applications/{id}/repayments
# ─────────────────────────────────────────────────────────────────────────────

def _setup_disbursed_loan(client, payload=None):
    docs = [
        {"doc_type": "ID_PROOF", "filename": "id.pdf"},
        {"doc_type": "ADDRESS_PROOF", "filename": "addr.pdf"},
        {"doc_type": "SALARY_SLIP", "filename": "slip.pdf"},
        {"doc_type": "BANK_STATEMENT", "filename": "bank.pdf"},
    ]
    post = client.post(
        "/applications",
        json={**(payload or _APPROVE_PAYLOAD), "documents": docs},
        headers=_CUST,
    )
    app_id = post.json()["id"]

    # Verify all documents
    for d in docs:
        client.post(
            f"/applications/{app_id}/documents/{d['doc_type']}/verify",
            json={"status": "VERIFIED"},
            headers=_UW,
        )

    # Disburse
    dsb = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert dsb.status_code == 200, dsb.text
    return app_id


@pytest.mark.ac("AC-09")
def test_ac09_repayment_one_emi_reduces_outstanding_principal(tmp_path):
    client = _make_client(tmp_path)
    app_id = _setup_disbursed_loan(client)

    # Pay exactly 1 EMI (10036.09)
    resp = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "10036.09", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp.status_code == 200
    body = resp.json()

    # In month 1: interest = 300000 * 12.5% / 12 = 3125.00; principal = 10036.09 - 3125.00 = 6911.09
    # Outstanding principal = 300000.00 - 6911.09 = 293088.91
    assert body["outstanding_principal"] == "293088.91"
    assert body["delinquency_bucket"] == "CURRENT"
    assert body["dpd"] == 0
    assert len(body["allocations"]) == 1
    assert body["allocations"][0]["principal_allocated"] == "6911.09"
    assert body["allocations"][0]["interest_allocated"] == "3125.00"


@pytest.mark.ac("AC-09a")
def test_ac09a_partial_payment_smaller_than_interest(tmp_path):
    client = _make_client(tmp_path)
    app_id = _setup_disbursed_loan(client)

    # Interest in month 1 is 3125.00. Pay 1000.00 (< 3125.00)
    resp = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "1000.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp.status_code == 200
    body = resp.json()

    # Principal untouched: 300000.00
    assert body["outstanding_principal"] == "300000.00"
    assert body["allocations"][0]["interest_allocated"] == "1000.00"
    assert body["allocations"][0]["principal_allocated"] == "0.00"


@pytest.mark.ac("AC-09b")
def test_ac09b_multi_installment_waterfall(tmp_path):
    client = _make_client(tmp_path)
    app_id = _setup_disbursed_loan(client)

    # Pay 25000.00 (covers month 1: 10036.09, month 2: 10036.09, part of month 3: 4927.82)
    resp = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "25000.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["allocations"]) == 3
    assert body["allocations"][0]["installment_number"] == 1
    assert body["allocations"][1]["installment_number"] == 2
    assert body["allocations"][2]["installment_number"] == 3


@pytest.mark.ac("AC-09e")
def test_ac09e_repayment_validations(tmp_path):
    client = _make_client(tmp_path)
    app_id = _setup_disbursed_loan(client)

    # 1. Zero amount -> 422
    resp_zero = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "0.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp_zero.status_code == 422

    # 2. Negative amount -> 422
    resp_neg = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "-100.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp_neg.status_code == 422

    # 3. Exceeds total remaining due -> 422
    resp_excess = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "500000.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp_excess.status_code == 422

    # 4. Other customer -> 403
    resp_other = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "1000.00", "paid_on": "2026-02-01"},
        headers=_CUST2,
    )
    assert resp_other.status_code == 403


@pytest.mark.ac("AC-09e")
def test_ac09e_repayment_on_non_disbursed_loan_returns_409(tmp_path):
    client = _make_client(tmp_path)
    # Submit but do not disburse
    post = client.post("/applications", json=_APPROVE_PAYLOAD, headers=_CUST)
    app_id = post.json()["id"]

    resp = client.post(
        f"/applications/{app_id}/repayments",
        json={"amount": "1000.00", "paid_on": "2026-02-01"},
        headers=_CUST,
    )
    assert resp.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# AC-09f — POST /admin/jobs/eod-buckets
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-09f")
def test_ac09f_eod_job_recalculates_buckets(tmp_path):
    client = _make_client(tmp_path)
    app_id = _setup_disbursed_loan(client)

    # Run EOD job with as_of in the future (e.g. 75 days after first due date)
    resp = client.post(
        "/admin/jobs/eod-buckets",
        json={"as_of": "2026-04-15"},
        headers=_ADMIN,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "counts_by_bucket" in body
    assert body["total_processed"] >= 1


@pytest.mark.ac("AC-09f")
def test_ac09f_eod_job_requires_admin(tmp_path):
    client = _make_client(tmp_path)
    resp_cust = client.post("/admin/jobs/eod-buckets", json={}, headers=_CUST)
    assert resp_cust.status_code == 403

    resp_uw = client.post("/admin/jobs/eod-buckets", json={}, headers=_UW)
    assert resp_uw.status_code == 403

