# Application Intake & Credit Scoring Feature Specification

## Module Context
The Application Intake module processes loan applications submitted by customers, generates product-specific document checklists, runs deterministic credit scoring, and enforces baseline income thresholds.

---

## Acceptance Criteria

### AC-02: Loan Application & Dynamic Required-Document Checklist
**Given** an applicant submits a loan application for a selected product (`PERSONAL_LOAN`, `VEHICLE_LOAN`, or `EDUCATION_LOAN`)  
**When** the application intake endpoint POST `/api/v1/applications` is invoked  
**Then** an application record is created in status `SUBMITTED`  
**And** a required-document checklist is dynamically generated according to the product's policy rules:
- `PERSONAL_LOAN`: `["IDENTITY_PROOF", "INCOME_SLIP_3M", "BANK_STATEMENT_6M"]`
- `VEHICLE_LOAN`: `["IDENTITY_PROOF", "INCOME_SLIP_3M", "VEHICLE_QUOTATION"]`
- `EDUCATION_LOAN`: `["IDENTITY_PROOF", "ADMISSION_LETTER", "CO_SIGNER_INCOME_PROOF"]`

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-02")`
- Test Location: `tests/domain/ApplicationIntakeServiceTest.java`

---

### AC-03: Deterministic Credit-Scoring Stub
**Given** an applicant profile containing `age` (int), `monthlyIncome` (decimal), and `creditHistoryFlags` (`hasDefault`, `existingLoansCount`, `bureauScorePresent`)  
**When** the credit scoring engine evaluates the profile  
**Then** it returns a deterministic credit score between 300 and 850 computed as:
$$\text{Base Score} = 600 + (\text{Income} / 1000 \times 2) + (\text{Age} \times 1.5) - (\text{Defaults} \times 150)$$
clamped within $[300, 850]$.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-03")`
- Test Location: `tests/services/CreditScoringStubTest.java`

---

### AC-05: Policy Violation Exception on Income Below Threshold
**Given** an applicant applies for a loan product with a minimum income threshold $T$ (e.g. \$25,000 for Personal Loan)  
**When** the applicant's income is strictly less than $T$ (e.g. \$20,000)  
**Then** the application submission fails immediately  
**And** throws a `PolicyViolationException` containing error code `INCOME_BELOW_MINIMUM_THRESHOLD`, product ID, submitted income, and required threshold  
**And** the HTTP API returns 400 Bad Request with a structured error payload.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-05")`
- Test Location: `tests/domain/PolicyViolationExceptionTest.java`
