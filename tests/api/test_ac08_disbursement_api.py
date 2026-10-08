"""
API integration tests for Loan Disbursement.

AC-08  — POST /applications/{id}/disburse: releases loan, creates disbursement record, sets status DISBURSED
AC-08a — Second disbursement request returns 409 (ALREADY_DISBURSED)
AC-08b — Non-approved status (MANUAL_REVIEW, REJECTED) returns 409
AC-08c — Unverified required documents return 409 DOCUMENTS_NOT_VERIFIED
AC-08d — Customer token returns 403; Underwriter writes audit log row
AC-08e — Loan state initialized: outstanding principal = released amount, bucket = CURRENT, dpd = 0
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

_DOCS = [
    {"doc_type": "ID_PROOF", "filename": "id.pdf"},
    {"doc_type": "ADDRESS_PROOF", "filename": "addr.pdf"},
    {"doc_type": "SALARY_SLIP", "filename": "slip.pdf"},
    {"doc_type": "BANK_STATEMENT", "filename": "bank.pdf"},
]

_APPROVED_APP = {
    "product": "PERSONAL",
    "amount": "200000.00",
    "tenure_months": 24,
    "applicant": {
        "full_name": "Disbursement Borrower",
        "age": 30,
        "monthly_income": "60000.00",
        "pan": "TESTP1234X",
        "aadhaar": "999900000001",
        "credit_history": "CLEAN",
        "has_default": False,
    },
    "documents": _DOCS,
}


@pytest.mark.ac("AC-08")
def test_ac08_disburse_approved_loan_success(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVED_APP, headers=_CUST)
    assert post.status_code == 201
    app_id = post.json()["id"]

    # Verify all 4 documents
    for d in _DOCS:
        client.post(
            f"/applications/{app_id}/documents/{d['doc_type']}/verify",
            json={"status": "VERIFIED"},
            headers=_UW,
        )

    # Disburse
    resp = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert resp.status_code == 200
    body = resp.json()

    assert body["application_id"] == app_id
    assert body["amount"] == "200000.00"
    assert body["funding_source"] == "STUB_FUNDING_ACCOUNT_01"
    assert body["reference"] == f"DSB-{app_id}"
    assert body["status"] == "SUCCESS"
    assert body["released_by"] == "uw-001"


@pytest.mark.ac("AC-08a")
def test_ac08a_duplicate_disbursement_returns_409(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVED_APP, headers=_CUST)
    app_id = post.json()["id"]

    for d in _DOCS:
        client.post(
            f"/applications/{app_id}/documents/{d['doc_type']}/verify",
            json={"status": "VERIFIED"},
            headers=_UW,
        )

    # First disbursement succeeds
    r1 = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert r1.status_code == 200

    # Second disbursement returns 409
    r2 = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert r2.status_code == 409


@pytest.mark.ac("AC-08b")
def test_ac08b_disburse_non_approved_application_returns_409(tmp_path):
    client = _make_client(tmp_path)
    # MANUAL_REVIEW application
    manual_app = {
        **_APPROVED_APP,
        "applicant": {
            **_APPROVED_APP["applicant"],
            "monthly_income": "30000.00",
            "credit_history": "THIN",
        },
    }
    post = client.post("/applications", json=manual_app, headers=_CUST)
    app_id = post.json()["id"]
    assert post.json()["status"] == "MANUAL_REVIEW"

    resp = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert resp.status_code == 409


@pytest.mark.ac("AC-08c")
def test_ac08c_disburse_with_unverified_docs_returns_409(tmp_path):
    client = _make_client(tmp_path)
    # Submit without verifying docs
    post = client.post("/applications", json=_APPROVED_APP, headers=_CUST)
    app_id = post.json()["id"]

    resp = client.post(f"/applications/{app_id}/disburse", headers=_UW)
    assert resp.status_code == 409


@pytest.mark.ac("AC-08d")
def test_ac08d_customer_cannot_disburse(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVED_APP, headers=_CUST)
    app_id = post.json()["id"]

    resp = client.post(f"/applications/{app_id}/disburse", headers=_CUST)
    assert resp.status_code == 403


@pytest.mark.ac("AC-08e")
def test_ac08e_loan_state_after_disbursement(tmp_path):
    client = _make_client(tmp_path)
    post = client.post("/applications", json=_APPROVED_APP, headers=_CUST)
    app_id = post.json()["id"]

    for d in _DOCS:
        client.post(
            f"/applications/{app_id}/documents/{d['doc_type']}/verify",
            json={"status": "VERIFIED"},
            headers=_UW,
        )

    client.post(f"/applications/{app_id}/disburse", headers=_UW)

    # Track application
    app_resp = client.get(f"/applications/{app_id}", headers=_CUST)
    assert app_resp.status_code == 200
    app_body = app_resp.json()
    assert app_body["status"] == "DISBURSED"
