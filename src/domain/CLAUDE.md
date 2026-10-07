# src/domain/ — pure business rules
No imports from other `src.*` layers, no `fastapi`, `sqlite3`, file/network IO, `datetime.now()`, `float`.
Dataclasses / enums / pure functions only. Raise domain exceptions from `exceptions.py`.

Required rule files (each with unit tests covering every branch):
- `money.py` — `quantize(Decimal)`, `to_money(str|int)`; ROUND_HALF_UP, 2 dp
- `credit_score.py` — deterministic stub (formula in `specs/application-intake_spec.md`)
- `eligibility_rules.py` — income/age/amount/tenure checks → `PolicyViolationException`
- `underwriting_decision.py` — AUTO_APPROVE / AUTO_REJECT / MANUAL_REVIEW + reason codes
- `emi_calculator.py` — EMI + schedule generation; invariants in `specs/repayment_spec.md`
- `repayment_allocation.py` — oldest-first, interest-before-principal
- `dpd_bucket.py` — DPD → bucket using thresholds from the policy
- `policy_validator.py` — validates a policy document (ranges, ordering, required docs)
- `exceptions.py` — `PolicyViolationException(reason_codes, policy_version)` etc.
Reason codes are an enum here and the only codes any layer may emit.
