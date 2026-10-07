"""
DocumentVerificationService — orchestrates document verification and validation.
No FastAPI imports; pure service layer.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from src.domain.exceptions import InvalidDocumentStateException, DocumentsNotVerifiedException
from src.domain.models import AuditEntry, Document, DocumentStatus


class DocumentVerificationService:
    """Service to handle document review and validation for loan applications."""

    def verify_document(
        self,
        *,
        doc: Document,
        decision_status: DocumentStatus,
        reason: Optional[str] = None,
        actor_user_id: str,
        application_id: Optional[str] = None,
    ) -> Tuple[Document, AuditEntry]:
        """
        Mark an UPLOADED document as VERIFIED or REJECTED with an audit reason.
        Only UPLOADED documents can be reviewed; otherwise raises InvalidDocumentStateException.
        Reason is mandatory when decision_status is REJECTED.
        """
        if doc.status != DocumentStatus.UPLOADED:
            raise InvalidDocumentStateException(
                f"Document '{doc.doc_type}' has status '{doc.status.value}', only UPLOADED documents can be verified."
            )

        if decision_status == DocumentStatus.REJECTED:
            if not reason or not reason.strip():
                raise ValueError("Reason is mandatory when rejecting a document.")

        updated_doc = Document(
            doc_type=doc.doc_type,
            filename=doc.filename,
            status=decision_status,
            rejection_reason=reason if decision_status == DocumentStatus.REJECTED else None,
        )

        audit_entry = AuditEntry(
            actor_user_id=actor_user_id,
            action="VERIFY_DOCUMENT",
            application_id=application_id,
            doc_type=doc.doc_type,
            reason=reason,
            comment=f"Marked document {doc.doc_type} as {decision_status.value}",
        )

        return updated_doc, audit_entry

    def validate_all_required_verified(
        self,
        required_doc_types: List[str],
        documents: Dict[str, Document],
    ) -> None:
        """
        Validate that every required document exists and is VERIFIED.
        Raises DocumentsNotVerifiedException if any required document is missing or not VERIFIED.
        """
        for req_doc in required_doc_types:
            doc = documents.get(req_doc)
            if doc is None or doc.status != DocumentStatus.VERIFIED:
                raise DocumentsNotVerifiedException(
                    f"Required document '{req_doc}' is not verified (status: {doc.status.value if doc else 'MISSING'})."
                )
