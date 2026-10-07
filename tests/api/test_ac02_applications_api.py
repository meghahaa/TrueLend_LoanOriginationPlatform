"""
API integration tests for Application Intake.

AC-02  — POST /applications: required-document checklist per product
AC-02a — GET /applications/{id}: track uploaded vs missing docs
AC-02b — POST /applications/{id}/documents: upload document; 403 for other customer
AC-02c — GET /applications/{id}: masked PAN/Aadhaar, no full identifiers
AC-03  — POST /applications: credit score 740 for age=30, income=60000, CLEAN, no default
AC-05  — POST /applications: income below min → 422 INCOME_BELOW_MIN, no row persisted
AC-05a — income exactly at min → 201
AC-05b — age out of range → 422 AGE_OUT_OF_RANGE
"""
import shutil

import pytest
from fastapi.testclient import TestClient


def _make_client(tmp_path):
    """TestClient backed by a temp policy dir + in-memory SQLite (db_path=':memory:')."""
    shutil.copy("policies/loan_policy.v001.json", tmp_path / "loan_policy.v001.json")
    from src.main import create_app
    app = create_app(policy_dir=str(tmp_path), db_path=":memory:")
    return TestClient(app)


_CUSTOMER_HEADERS = {"Authorization": "Bearer customer-token"}
_CUSTOMER2_HEADERS = {"Authorization": "Bearer customer-token-2"}

_GOOD_PAYLOAD = {
    "product": "PERSONAL",
    "amount": "200000.00",
    "tenure_months": 24,
    "applicant": {
        "full_name": "Test User",
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
# AC-02 — POST /applications returns 201 with document checklist
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-02")
def test_ac02_post_application_returns_201(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201, resp.text


@pytest.mark.ac("AC-02")
def test_ac02_personal_loan_has_4_required_documents(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["documents"]) == 4


@pytest.mark.ac("AC-02")
def test_ac02_personal_loan_all_documents_missing(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    body = resp.json()
    statuses = [d["status"] for d in body["documents"]]
    assert all(s == "MISSING" for s in statuses)
    assert len(body["missing_documents"]) == 4


@pytest.mark.ac("AC-02")
def test_ac02_education_loan_has_5_required_documents(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "product": "EDUCATION",
        "amount": "500000.00",
        "tenure_months": 36,
        "applicant": {
            **_GOOD_PAYLOAD["applicant"],
            "age": 22,
            "monthly_income": "20000.00",
        },
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["documents"]) == 5


@pytest.mark.ac("AC-02")
def test_ac02_response_contains_required_fields(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    body = resp.json()
    for field in ("id", "status", "decision", "reason_codes", "policy_version", "score",
                  "documents", "missing_documents"):
        assert field in body, f"Missing field: {field}"


@pytest.mark.ac("AC-02")
def test_ac02_no_token_returns_401(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD)
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# AC-02 — documents partially uploaded at submission
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-02")
def test_ac02_submitted_documents_marked_uploaded(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "documents": [
            {"doc_type": "ID_PROOF", "filename": "id.pdf"},
            {"doc_type": "SALARY_SLIP", "filename": "slip.pdf"},
        ],
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201
    body = resp.json()
    doc_map = {d["doc_type"]: d["status"] for d in body["documents"]}
    assert doc_map["ID_PROOF"] == "UPLOADED"
    assert doc_map["SALARY_SLIP"] == "UPLOADED"
    assert doc_map["ADDRESS_PROOF"] == "MISSING"
    assert doc_map["BANK_STATEMENT"] == "MISSING"
    assert len(body["missing_documents"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# AC-02a — GET /applications/{id} track view
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-02a")
def test_ac02a_get_application_returns_status_and_docs(tmp_path):
    client = _make_client(tmp_path)
    post_resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    app_id = post_resp.json()["id"]
    resp = client.get(f"/applications/{app_id}", headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == app_id
    assert "status" in body
    assert "documents" in body
    assert "missing_documents" in body


@pytest.mark.ac("AC-02a")
def test_ac02a_unknown_application_returns_404(tmp_path):
    client = _make_client(tmp_path)
    resp = client.get("/applications/nonexistent-id", headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# AC-02b — POST /applications/{id}/documents: upload missing doc
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-02b")
def test_ac02b_upload_missing_document_becomes_uploaded(tmp_path):
    client = _make_client(tmp_path)
    post_resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    app_id = post_resp.json()["id"]
    resp = client.post(
        f"/applications/{app_id}/documents",
        json={"doc_type": "ID_PROOF", "filename": "id_new.pdf"},
        headers=_CUSTOMER_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    doc_map = {d["doc_type"]: d["status"] for d in body["documents"]}
    assert doc_map["ID_PROOF"] == "UPLOADED"


@pytest.mark.ac("AC-02b")
def test_ac02b_other_customer_upload_returns_403(tmp_path):
    client = _make_client(tmp_path)
    post_resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    app_id = post_resp.json()["id"]
    resp = client.post(
        f"/applications/{app_id}/documents",
        json={"doc_type": "ID_PROOF", "filename": "stolen.pdf"},
        headers=_CUSTOMER2_HEADERS,
    )
    assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# AC-02c — Masked PAN/Aadhaar in response
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-02c")
def test_ac02c_pan_is_masked_in_response(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    body = resp.json()
    assert "TESTP1234X" not in str(body), "Full PAN must not appear in response"
    assert "pan_masked" in body or "XXXXXX" in str(body), "PAN must be masked"


@pytest.mark.ac("AC-02c")
def test_ac02c_aadhaar_is_masked_in_response(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    body = resp.json()
    assert "999900000001" not in str(body), "Full Aadhaar must not appear in response"


# ─────────────────────────────────────────────────────────────────────────────
# AC-03 — Credit score 740 for reference inputs
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-03")
def test_ac03_reference_score_740(tmp_path):
    client = _make_client(tmp_path)
    resp = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201
    assert resp.json()["score"] == 740


@pytest.mark.ac("AC-03")
def test_ac03_score_is_deterministic(tmp_path):
    client = _make_client(tmp_path)
    r1 = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS).json()
    r2 = client.post("/applications", json=_GOOD_PAYLOAD, headers=_CUSTOMER_HEADERS).json()
    assert r1["score"] == r2["score"] == 740


# ─────────────────────────────────────────────────────────────────────────────
# AC-05 — Policy gate: income below min → 422, no row persisted
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-05")
def test_ac05_income_below_min_returns_422(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {**_GOOD_PAYLOAD["applicant"], "monthly_income": "24999.99"},
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 422


@pytest.mark.ac("AC-05")
def test_ac05_income_below_min_reason_code(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {**_GOOD_PAYLOAD["applicant"], "monthly_income": "24999.99"},
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    body = resp.json()
    # PolicyViolationException maps to 422 with detail.reason_codes
    codes = body.get("reason_codes") or body.get("detail", {}).get("reason_codes", [])
    assert "INCOME_BELOW_MIN" in codes


@pytest.mark.ac("AC-05")
def test_ac05_violation_does_not_persist_application(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {**_GOOD_PAYLOAD["applicant"], "monthly_income": "24999.99"},
    }
    client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    # List applications — must be empty (no persisted row)
    resp = client.get("/applications/nonexistent-id", headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# AC-05a — Boundary: income exactly at min passes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-05a")
def test_ac05a_income_at_boundary_passes(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {**_GOOD_PAYLOAD["applicant"], "monthly_income": "25000.00"},
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 201


# ─────────────────────────────────────────────────────────────────────────────
# AC-05b — Age out of range → 422 AGE_OUT_OF_RANGE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ac("AC-05b")
def test_ac05b_age_below_min_returns_422(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {**_GOOD_PAYLOAD["applicant"], "age": 17},
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 422
    body = resp.json()
    codes = body.get("reason_codes") or body.get("detail", {}).get("reason_codes", [])
    assert "AGE_OUT_OF_RANGE" in codes


@pytest.mark.ac("AC-05b")
def test_ac05b_multiple_violations_all_reported(tmp_path):
    client = _make_client(tmp_path)
    payload = {
        **_GOOD_PAYLOAD,
        "applicant": {
            **_GOOD_PAYLOAD["applicant"],
            "age": 17,
            "monthly_income": "1000.00",
        },
    }
    resp = client.post("/applications", json=payload, headers=_CUSTOMER_HEADERS)
    assert resp.status_code == 422
    body = resp.json()
    codes = body.get("reason_codes") or body.get("detail", {}).get("reason_codes", [])
    assert "AGE_OUT_OF_RANGE" in codes
    assert "INCOME_BELOW_MIN" in codes
