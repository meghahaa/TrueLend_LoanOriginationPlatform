"""
AC-06 — Document Verification Queue

Tests covering document verification actions, validation, mandatory rejection reason,
and state enforcement.
"""
import pytest

from src.domain.exceptions import DocumentsNotVerifiedException, InvalidDocumentStateException
from src.domain.models import Document, DocumentStatus
from src.services.document_verification_service import DocumentVerificationService


@pytest.mark.ac("AC-06")
def test_ac06_underwriter_verifies_uploaded_document():
    """An underwriter marks an UPLOADED document as VERIFIED; status becomes VERIFIED."""
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
        application_id="app-123",
    )

    assert result_doc.status == DocumentStatus.VERIFIED
    assert audit_entry.actor_user_id == "uw-001"
    assert audit_entry.action == "VERIFY_DOCUMENT"
    assert audit_entry.doc_type == "ID_PROOF"
    assert audit_entry.application_id == "app-123"


@pytest.mark.ac("AC-06a")
def test_ac06a_underwriter_rejects_document_with_reason():
    """Underwriter marks document as REJECTED with reason; rejection_reason stored."""
    doc = Document(
        doc_type="SALARY_SLIP",
        filename="slip_blur.pdf",
        status=DocumentStatus.UPLOADED,
    )
    service = DocumentVerificationService()
    result_doc, audit_entry = service.verify_document(
        doc=doc,
        decision_status=DocumentStatus.REJECTED,
        reason="Document is blurry and unreadable",
        actor_user_id="uw-001",
    )

    assert result_doc.status == DocumentStatus.REJECTED
    assert result_doc.rejection_reason == "Document is blurry and unreadable"
    assert audit_entry.reason == "Document is blurry and unreadable"


@pytest.mark.ac("AC-06a")
def test_ac06a_underwriter_rejects_without_reason_fails():
    """Rejecting a document without a reason raises ValueError."""
    doc = Document(
        doc_type="SALARY_SLIP",
        filename="slip_blur.pdf",
        status=DocumentStatus.UPLOADED,
    )
    service = DocumentVerificationService()
    with pytest.raises(ValueError, match="mandatory"):
        service.verify_document(
            doc=doc,
            decision_status=DocumentStatus.REJECTED,
            reason="",
            actor_user_id="uw-001",
        )


@pytest.mark.ac("AC-06b")
def test_ac06b_verifying_missing_document_raises_invalid_state():
    """Verifying a MISSING document raises InvalidDocumentStateException."""
    doc = Document(
        doc_type="ADDRESS_PROOF",
        filename=None,
        status=DocumentStatus.MISSING,
    )
    service = DocumentVerificationService()
    with pytest.raises(InvalidDocumentStateException):
        service.verify_document(
            doc=doc,
            decision_status=DocumentStatus.VERIFIED,
            reason="Trying to verify missing",
            actor_user_id="uw-001",
        )


@pytest.mark.ac("AC-06b")
def test_ac06b_verifying_already_verified_document_raises_invalid_state():
    """Verifying an already VERIFIED document raises InvalidDocumentStateException."""
    doc = Document(
        doc_type="ADDRESS_PROOF",
        filename="address.pdf",
        status=DocumentStatus.VERIFIED,
    )
    service = DocumentVerificationService()
    with pytest.raises(InvalidDocumentStateException):
        service.verify_document(
            doc=doc,
            decision_status=DocumentStatus.VERIFIED,
            reason="Already verified",
            actor_user_id="uw-001",
        )


@pytest.mark.ac("AC-06d")
def test_ac06d_unverified_required_document_blocks_approval():
    """Manual approval check raises DocumentsNotVerifiedException when any required doc is not VERIFIED."""
    service = DocumentVerificationService()
    required = ["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"]
    docs = {
        "ID_PROOF": Document(doc_type="ID_PROOF", status=DocumentStatus.VERIFIED),
        "ADDRESS_PROOF": Document(doc_type="ADDRESS_PROOF", status=DocumentStatus.UPLOADED),
        "SALARY_SLIP": Document(doc_type="SALARY_SLIP", status=DocumentStatus.VERIFIED),
    }
    with pytest.raises(DocumentsNotVerifiedException):
        service.validate_all_required_verified(required, docs)


@pytest.mark.ac("AC-06d")
def test_ac06d_all_verified_required_documents_pass():
    """When all required documents are VERIFIED, validation succeeds."""
    service = DocumentVerificationService()
    required = ["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP"]
    docs = {
        "ID_PROOF": Document(doc_type="ID_PROOF", status=DocumentStatus.VERIFIED),
        "ADDRESS_PROOF": Document(doc_type="ADDRESS_PROOF", status=DocumentStatus.VERIFIED),
        "SALARY_SLIP": Document(doc_type="SALARY_SLIP", status=DocumentStatus.VERIFIED),
    }
    # Should not raise
    service.validate_all_required_verified(required, docs)
