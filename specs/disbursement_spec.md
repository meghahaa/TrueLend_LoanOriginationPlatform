# Disbursement Feature Specification

## Module Context
The Disbursement module manages releasing approved loan funds to borrower accounts, recording disbursement records, and logging stubbed banking payment rail metadata.

---

## Acceptance Criteria

### AC-08: Disbursement Recording & Funding Source Metadata
**Given** an approved loan application ready for disbursement  
**When** disbursement is triggered via POST `/api/v1/disbursements`  
**Then** the disbursement record is written capturing:
- `disbursementId`: UUID
- `applicationId`: String
- `releasedAmount`: Fixed-point decimal equal to approved principal
- `fundingSource`: Stubbed funding source descriptor (e.g., `HORIZON_BANK_TREASURY_POOL_01`)
- `disbursementTimestamp`: ISO 8601 UTC timestamp
- `disbursementStatus`: `SUCCESS`
**And** the application status transitions to `DISBURSED`.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-08")`
- Test Location: `tests/services/DisbursementServiceTest.java`
