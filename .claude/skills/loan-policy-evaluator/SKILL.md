---
name: loan-policy-evaluator
description: Use when implementing or testing TrueLend eligibility, credit-score stub, underwriting decision or reason codes against the versioned policy file. Provides the evaluation order, formulas and test matrix so rules are never hard-coded.
---
# Loan policy evaluator

**Source of truth:** `specs/application-intake_spec.md` (gate + score) and `specs/underwriting_spec.md` (decision). Policy values come from the active `policies/loan_policy.vNNN.json`; never hard-code thresholds.

## Evaluation order
1. Load active policy → product block (unknown product → 422 error code `UNKNOWN_PRODUCT` (an error code, not a reason code)).
2. Gate: income, age, amount, tenure → collect all violations → `PolicyViolationException(reason_codes, policy_version)`.
3. Score (integer table lookup, clamp 300–900).
4. FOIR = EMI / monthly_income (Decimal).
5. Decision: default → reject; score < reject → reject; score ≥ approve and FOIR ≤ max → approve; else manual review (+ band / FOIR reason).

## Build pattern
- Pure functions taking `(policy_product, applicant)`; return frozen dataclasses with `decision`, `reason_codes`, `score`, `policy_version`.
- Table-driven code for score bands (data, not if-chains) so tests can parametrise.

## Test matrix (each case → one test with `@pytest.mark.ac`)
Boundaries: income min−0.01 / min; age min−1 / min / max / max+1; score = reject−1 / reject / approve−1 / approve; FOIR = max / max+0.0001; `has_default` with high score; policy v002 with changed threshold; every reason code produced at least once.

## Pitfalls
Comparing money as strings; using `float` for FOIR; reading thresholds once at import (must be per-request active policy); emitting a reason code not in the enum.
