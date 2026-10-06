# Underwriting Workbench Feature Specification

## Module Context
The Underwriting module provides automated policy decisioning, document verification queue management, and audited admin override capabilities for underwriter operations.

---

## Acceptance Criteria

### AC-04: Automated Underwriting Decisioning & Reason Codes
**Given** a submitted loan application with complete credit score and income data  
**When** the underwriting engine evaluates the application against the active policy version  
**Then** it returns one of three decisions:
- `AUTO_APPROVE`: Score >= autoApprovalThreshold AND Income >= minIncome AND Defaults == 0. Reason Code: `AUTO_APPROVE_LOW_RISK`.
- `AUTO_REJECT`: Score < autoRejectThreshold OR Defaults > 1 OR Income < absoluteFloor. Reason Code: `AUTO_REJECT_HIGH_RISK` or `INC_BELOW_MIN`.
- `MANUAL_REVIEW`: Score between reject and approve thresholds. Reason Code: `MANUAL_REVIEW_BORDERLINE`.
**And** the decision references the exact policy version (e.g., `v1.0`).

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-04")`
- Test Location: `tests/services/UnderwritingEngineTest.java`

---

### AC-06: Document Verification Queue
**Given** an underwriter accesses the document verification queue for an application  
**When** reviewing each uploaded document  
**Then** the underwriter can mark each document as `VERIFIED` or `REJECTED` with an audit reason  
**And** an application can only transition to `APPROVED` state if ALL required documents are marked `VERIFIED`.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-06")`
- Test Location: `tests/domain/DocumentVerificationServiceTest.java`

---

### AC-10: Admin Override & Audit Trail
**Given** an application with status `AUTO_REJECT`  
**When** an authorized administrator executes an override via POST `/api/v1/applications/{id}/override`  
**Then** the application status transitions to `MANUAL_OVERRIDE_APPROVED`  
**And** an audit record is created capturing: `adminUserId`, `timestamp`, `originalDecision`, `overrideReasonCode`, and `comments`.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-10")`
- Test Location: `tests/controllers/AdminOverrideAuditTest.java`
