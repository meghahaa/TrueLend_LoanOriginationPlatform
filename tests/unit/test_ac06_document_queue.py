"""
AC-06 — Document Verification Queue

RED test: asserts that an uploaded document can be marked as VERIFIED
by an underwriter, updating its status to VERIFIED and recording audit details.
"""
import pytest
from decimal import Decimal


@pytest.mark.ac("AC-06")
def test_ac06_underwriter_verifies_uploaded_document():
    """An underwriter marks an UPLOADED document as VERIFIED; status becomes VERIFIED."""
    from src.domain.models import Document, DocumentStatus
    from src.services.document_verification_service import DocumentVerificationService

    doc = Document(
        doc_type="ID_PROOF",
        filename="id_card.pdf",
        status=DocumentStatus.UPLOADED,
    )
    service = DocumentVerificationService()
    result_doc, audit_entry = service.verify_document(
        doc=doc,
        decision_status=DocumentStatus.VERIFIED,
        reason="Valid government ID",
        actor_user_id="uw-001",
    )

    assert result_doc.status == DocumentStatus.VERIFIED
    assert audit_entry.actor_user_id == "uw-001"
    assert audit_entry.action == "VERIFY_DOCUMENT"
    assert audit_entry.doc_type == "ID_PROOF"
