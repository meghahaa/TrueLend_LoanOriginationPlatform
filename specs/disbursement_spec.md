# Feature Spec — Disbursement (stubbed rails)
Covers AC-08. No real payment rails; the funding source is a fixed stub.

## Behaviour
`POST /applications/{id}/disburse` (UNDERWRITER or ADMIN). Preconditions: status `APPROVED`; a schedule exists; **every required document is `VERIFIED`** (else 409 `DOCUMENTS_NOT_VERIFIED`). Effect: insert one `disbursements` row `{application_id, amount (= approved principal), funding_source: "STUB_FUNDING_ACCOUNT_01", reference: "DSB-<application id>", disbursed_at (Clock), released_by}`; status → `DISBURSED`; loan state initialised (outstanding principal = P, bucket `CURRENT`, dpd 0). Audited. One disbursement per application: repeat → 409 `ALREADY_DISBURSED`, no second row. Response returns the disbursement record. No stub call may perform network IO.

## Acceptance Criteria
- **AC-08** Given an `APPROVED` application with all documents verified, when disbursed, then a record stores the released amount equal to the principal and funding source `STUB_FUNDING_ACCOUNT_01`; status `DISBURSED`.
- **AC-08a** Given a second disburse request, then 409 and exactly one disbursement row exists.
- **AC-08b** Given status `MANUAL_REVIEW` or `REJECTED`, then 409.
- **AC-08c** Given an unverified required document, then 409 `DOCUMENTS_NOT_VERIFIED` and nothing is written.
- **AC-08d** Given a CUSTOMER token, then 403; given UNDERWRITER, the audit row has that user id and timestamp (NFR-04).
- **AC-08e** After disbursement the loan's outstanding principal equals the released amount and bucket is `CURRENT`.
