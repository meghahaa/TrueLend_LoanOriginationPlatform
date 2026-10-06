# Application Master Specification — TrueLend Loan Origination & Underwriting System

## 1. Overview & System Purpose
TrueLend is a configurable, policy-driven loan origination and underwriting system. The system enables Horizon Bank to define and launch new loan products with custom policy rules without modifying backend application source code. The end-to-end flow covers product catalog management, application submission, document requirement generation, credit scoring, underwriting decisioning, admin overrides, repayment scheduling, disbursement, and repayment posting with DPD bucket recalculation.

---

## 2. Functional Scope & Feature Modules

### 2.1 Product Catalog Module (`specs/product-catalog_spec.md`)
- Defines loan products (Personal, Vehicle, Education).
- Sourced from versioned policy files (e.g., `policy-v1.0.json`).
- Specifies product-specific minimum income, credit score thresholds, interest rate ranges, and maximum loan amounts.

### 2.2 Application Intake & Credit Scoring Module (`specs/application-intake_spec.md`)
- Allows applicants to select a product, input financial details, and submit documents.
- Dynamically generates document checklist per product type.
- Computes deterministic credit score based on applicant age, income, and credit history flags.
- Enforces policy validation throwing `PolicyViolationException` when income is below product threshold.

### 2.3 Underwriting Engine Module (`specs/underwriting_spec.md`)
- Evaluates submitted applications against active policy version rules.
- Yields decisions: `AUTO_APPROVE`, `AUTO_REJECT`, `MANUAL_REVIEW` with explicit reason codes (e.g., `INC_BELOW_MIN`, `SCORE_HIGH_PASS`).
- Underwriter document verification queue (`VERIFIED` / `REJECTED`).
- Audited admin override allowing override of `AUTO_REJECT` decisions with comments and reason codes.

### 2.4 Repayment & Amortization Module (`specs/repayment_spec.md`)
- Generates equal monthly installment (EMI) schedules using exact fixed-point standard formula.
- Guarantees invariant: `sum(principal_payments) + sum(interest_payments) == total_payable`.
- Posts incoming customer repayments, reduces outstanding principal balance, and recalculates DPD/NPA delinquency buckets (`CURRENT`, `DPD-30`, `DPD-60`, `DPD-90`, `NPA`).

### 2.5 Disbursement Module (`specs/disbursement_spec.md`)
- Processes approved applications for disbursement.
- Captures released amount and stubbed funding source metadata.

---

## 3. Master Acceptance Criteria Matrix

| ID | Feature | Specification Summary | Verification Method |
|---|---|---|---|
| **AC-01** | Product Catalog | Catalog supports >= 3 products (Personal, Vehicle, Education) with distinct rule sets from versioned policy file. | `ProductCatalogServiceTest` |
| **AC-02** | Application Intake | Customer applies for loan; required document checklist generated dynamically per product. | `ApplicationIntakeServiceTest` |
| **AC-03** | Credit Scoring | Deterministic credit scoring from age, income, and credit history flags. | `CreditScoringStubTest` |
| **AC-04** | Underwriting Decision | Underwriting returns `AUTO_APPROVE` / `AUTO_REJECT` / `MANUAL_REVIEW` with reason codes from active policy version. | `UnderwritingEngineTest` |
| **AC-05** | Policy Violation Exception | Application fails with `PolicyViolationException` when income < minimum threshold for selected product. | `PolicyViolationExceptionTest` |
| **AC-06** | Document Queue | Underwriter document queue allows marking documents `VERIFIED` / `REJECTED` with reason. | `DocumentVerificationServiceTest` |
| **AC-07** | EMI Schedule Calculation | Repayment schedule generated using EMI formula; sum of principal and interest equals total payable. | `EMICalculatorTest` |
| **AC-08** | Disbursement Recording | Disbursement records released amount and stubbed funding source. | `DisbursementServiceTest` |
| **AC-09** | Repayment Posting & Bucketing | Repayment posting reduces principal; bucket recalculated (`CURRENT`, `DPD-30`, `DPD-60`, `DPD-90`, `NPA`). | `RepaymentServiceTest` |
| **AC-10** | Admin Override Audit | Admin can list applications, filter by status/product, override `AUTO_REJECT` with audited comment/reason code. | `AdminOverrideAuditTest` |

---

## 4. Master Non-Functional Requirements (NFRs)

| ID | Requirement Title | Description | Structural Guardrail |
|---|---|---|---|
| **NFR-01** | Fixed-Point Financial Precision | All monetary values (principal, interest, EMI, balance) MUST use `BigDecimal` / `decimal` — never floating-point `double`/`float`. | Checked via `interest-precision-check.sh` & unit tests. |
| **NFR-02** | Append-Only Policies & Schedules | Approved policy versions and generated repayment schedules are append-only. No UPDATE or DELETE allowed. | DB constraints & ArchUnit assertions. |
| **NFR-03** | PII Masking & Logging Safety | Synthetic identifiers (PAN, Aadhaar) and salary documents are NEVER written to logs or stdout. | Checked via `detect-secrets.js` & log analyzer. |
| **NFR-04** | Controller Auth & Audit Trail | Auth boundary enforced at controller layer; underwriter/admin actions recorded with user ID, timestamp, and action. | Spring Security / Middleware + Audit log table. |
| **NFR-05** | Append-Only Migrations | DB schema and policy migrations must be strictly append-only. | Migration linter check. |
| **NFR-06** | Structured JSON Logging | Structured JSON logging with request correlation ID in every log entry. | MDC correlation filter + Jackson JSON encoder. |
| **NFR-07** | Fast Startup Health Endpoint | `/actuator/health` or `/health` returns HTTP 200 within 1 second of successful startup. | Health check integration test. |
| **NFR-08** | Architecture Rule Enforcement | Architectural structural constraints (layer separation, EMI invariant formulas) enforced via automated tests. | `ArchitectureRulesTest.java`. |
