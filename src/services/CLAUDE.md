# Services Layer Guidelines — src/services/

## Responsibilities
- Core business services: `ProductCatalogService`, `ApplicationIntakeService`, `UnderwritingService`, `EMIScheduleService`, `RepaymentPostingService`, `DisbursementService`.
- Transaction orchestration (`@Transactional` where appropriate).
- Implementation of fixed-point EMI formulas and DPD/NPA delinquency bucket transition rules.

## Invariants & Rules
- Always use fixed-point arithmetic (`BigDecimal.setScale(2, RoundingMode.HALF_UP)`).
- Never allow an update or delete to an approved `PolicyVersion` or generated `RepaymentSchedule`.
- Emit domain events or audit logs when underwriting decisions or admin overrides occur.
