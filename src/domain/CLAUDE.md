# Domain Layer Guidelines — src/domain/

## Responsibilities
- Core domain entities: `LoanProduct`, `LoanApplication`, `PolicyVersion`, `RepaymentSchedule`, `RepaymentInstallment`, `DisbursementRecord`.
- Business policy validators: `PolicyValidator`, `EligibilityRulesEngine`.
- Enums: `ProductType`, `ApplicationStatus`, `DecisionOutcome`, `DelinquencyBucket`, `DocumentType`.

## Invariants & Rules
- Domain objects must be immutable where possible or use clear state mutation methods.
- Policy versions and repayment schedules are strictly append-only (NFR-02).
- Zero external framework dependencies in pure domain entities (no Spring annotations inside core math/policy models).
- All domain validation errors throw `PolicyViolationException` or sub-classes.
