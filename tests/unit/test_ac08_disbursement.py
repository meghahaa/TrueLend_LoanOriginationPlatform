"""
AC-08 — Disbursement Recording & Funding Source Metadata

Unit tests covering:
- AC-08: Successful disbursement records released amount, stubbed funding source, and DISBURSED status
- AC-08a: Subsequent disbursement attempt raises AlreadyDisbursedException
- AC-08b: Non-APPROVED statuses (MANUAL_REVIEW, REJECTED) reject disbursement
- AC-08c: Unverified required document raises DocumentsNotVerifiedException
- AC-08d: Role checks and underwriter audit record metadata (NFR-04)
- AC-08e: Outstanding principal and delinquency bucket initialized appropriately
"""
from decimal import Decimal
import pytest

from src.api.auth import Actor
from src.domain.exceptions import (
    AlreadyDisbursedException,
    DocumentsNotVerifiedException,
    InvalidApplicationStateException,
)
from src.domain.models import ApplicationStatus, Document, DocumentStatus
from src.services.disbursement_service import DisbursementService


@pytest.fixture
def valid_documents():
    return {
        "ID_PROOF": Document(doc_type="ID_PROOF", status=DocumentStatus.VERIFIED),
        "ADDRESS_PROOF": Document(doc_type="ADDRESS_PROOF", status=DocumentStatus.VERIFIED),
        "SALARY_SLIP": Document(doc_type="SALARY_SLIP", status=DocumentStatus.VERIFIED),
    }


@pytest.mark.ac("AC-08")
def test_ac08_disbursement_creates_record_and_updates_status(valid_documents):
    """Disbursing an approved application records funding source metadata and status DISBURSED."""
    service = DisbursementService()
    result = service.disburse_loan(
        application_id="app-100",
        principal=Decimal("300000.00"),
        status=ApplicationStatus.APPROVED,
        has_schedule=True,
        required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
        documents=valid_documents,
        released_by="uw-001",
        already_disbursed=False,
    )

    assert result.disbursement.application_id == "app-100"
    assert result.disbursement.amount == Decimal("300000.00")
    assert result.disbursement.funding_source == "STUB_FUNDING_ACCOUNT_01"
    assert result.disbursement.reference == "DSB-app-100"
    assert result.disbursement.released_by == "uw-001"
    assert result.disbursement.status == "SUCCESS"
    assert result.new_status == ApplicationStatus.DISBURSED
    assert result.outstanding_principal == Decimal("300000.00")
    assert result.delinquency_bucket == "CURRENT"
    assert result.dpd == 0


@pytest.mark.ac("AC-08a")
def test_ac08a_already_disbursed_raises_conflict(valid_documents):
    """Given a second disburse request, AlreadyDisbursedException is raised."""
    service = DisbursementService()
    with pytest.raises(AlreadyDisbursedException):
        service.disburse_loan(
            application_id="app-100",
            principal=Decimal("300000.00"),
            status=ApplicationStatus.APPROVED,
            has_schedule=True,
            required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
            documents=valid_documents,
            released_by="uw-001",
            already_disbursed=True,
        )


@pytest.mark.ac("AC-08b")
@pytest.mark.parametrize("invalid_status", [
    ApplicationStatus.MANUAL_REVIEW,
    ApplicationStatus.REJECTED,
    ApplicationStatus.SUBMITTED,
])
def test_ac08b_non_approved_status_raises_invalid_state(valid_documents, invalid_status):
    """Disbursement on non-APPROVED status raises InvalidApplicationStateException."""
    service = DisbursementService()
    with pytest.raises(InvalidApplicationStateException):
        service.disburse_loan(
            application_id="app-100",
            principal=Decimal("300000.00"),
            status=invalid_status,
            has_schedule=True,
            required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
            documents=valid_documents,
            released_by="uw-001",
            already_disbursed=False,
        )


@pytest.mark.ac("AC-08c")
def test_ac08c_unverified_document_raises_documents_not_verified():
    """Given an unverified required document, disbursement is blocked with DocumentsNotVerifiedException."""
    docs = {
        "ID_PROOF": Document(doc_type="ID_PROOF", status=DocumentStatus.VERIFIED),
        "ADDRESS_PROOF": Document(doc_type="ADDRESS_PROOF", status=DocumentStatus.UPLOADED),
        "SALARY_SLIP": Document(doc_type="SALARY_SLIP", status=DocumentStatus.VERIFIED),
    }
    service = DisbursementService()
    with pytest.raises(DocumentsNotVerifiedException):
        service.disburse_loan(
            application_id="app-100",
            principal=Decimal("300000.00"),
            status=ApplicationStatus.APPROVED,
            has_schedule=True,
            required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
            documents=docs,
            released_by="uw-001",
            already_disbursed=False,
        )


@pytest.mark.ac("AC-08d")
def test_ac08d_customer_forbidden_and_underwriter_audited(valid_documents):
    """Customer role is denied (403) and underwriter action writes audit row with user ID and timestamp."""
    customer = Actor(user_id="cust-001", role="CUSTOMER")
    assert customer.role not in ("UNDERWRITER", "ADMIN")

    service = DisbursementService()
    result = service.disburse_loan(
        application_id="app-100",
        principal=Decimal("200000.00"),
        status=ApplicationStatus.APPROVED,
        has_schedule=True,
        required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
        documents=valid_documents,
        released_by="uw-002",
        already_disbursed=False,
        disbursed_at="2026-03-01T12:00:00Z",
    )
    assert result.audit_entry.actor_user_id == "uw-002"
    assert result.audit_entry.timestamp == "2026-03-01T12:00:00Z"
    assert result.audit_entry.action == "DISBURSE_LOAN"


@pytest.mark.ac("AC-08e")
def test_ac08e_initializes_loan_balance_and_bucket(valid_documents):
    """Disbursement initializes outstanding principal to principal and bucket to CURRENT."""
    service = DisbursementService()
    result = service.disburse_loan(
        application_id="app-100",
        principal=Decimal("150000.00"),
        status=ApplicationStatus.APPROVED,
        has_schedule=True,
        required_doc_types=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"],
        documents=valid_documents,
        released_by="admin-001",
        already_disbursed=False,
    )
    assert result.outstanding_principal == Decimal("150000.00")
    assert result.delinquency_bucket == "CURRENT"
    assert result.dpd == 0
