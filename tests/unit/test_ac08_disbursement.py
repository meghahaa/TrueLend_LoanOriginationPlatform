"""
AC-08 — Disbursement Recording & Funding Source Metadata

RED test: asserts that an APPROVED application with verified documents
can be disbursed, creating a disbursement record with funding source metadata
and transitioning application status to DISBURSED.
"""
from datetime import datetime, timezone
from decimal import Decimal
import pytest

from src.domain.models import ApplicationStatus, Document, DocumentStatus


@pytest.mark.ac("AC-08")
def test_ac08_disbursement_creates_record_and_updates_status():
    """Disbursing an approved application records funding source metadata and status DISBURSED."""
    from src.services.disbursement_service import DisbursementService

    service = DisbursementService()
    docs = {
        "ID_PROOF": Document(doc_type="ID_PROOF", status=DocumentStatus.VERIFIED),
        "ADDRESS_PROOF": Document(doc_type="ADDRESS_PROOF", status=DocumentStatus.VERIFIED),
    }

    result = service.disburse_loan(
        application_id="app-100",
        principal=Decimal("250000.00"),
        status=ApplicationStatus.APPROVED,
        has_schedule=True,
        required_doc_types=["ID_PROOF", "ADDRESS_PROOF"],
        documents=docs,
        released_by="uw-001",
        already_disbursed=False,
    )

    assert result.disbursement.application_id == "app-100"
    assert result.disbursement.amount == Decimal("250000.00")
    assert result.disbursement.funding_source == "STUB_FUNDING_ACCOUNT_01"
    assert result.disbursement.reference == "DSB-app-100"
    assert result.disbursement.released_by == "uw-001"
    assert result.new_status == ApplicationStatus.DISBURSED
    assert result.outstanding_principal == Decimal("250000.00")
    assert result.delinquency_bucket == "CURRENT"
    assert result.dpd == 0
