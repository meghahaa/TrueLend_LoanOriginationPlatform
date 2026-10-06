---
name: loan-policy-evaluator
description: Evaluates loan applications against versioned policy rules, computes credit scores, and returns underwriting decisions.
---

# Loan Policy Evaluator Skill

This skill provides step-by-step instructions for evaluating loan applications against versioned underwriting policies.

## Execution Steps

1. **Load Active Policy**:
   - Parse active policy version file (e.g., `src/main/resources/policies/policy-v1.0.json`).
   - Extract product-specific thresholds (`minIncome`, `minCreditScore`, `autoApproveScore`, `autoRejectScore`).

2. **Income Threshold Check**:
   - Compare applicant income against product minimum income.
   - If `income < minIncome`, throw `PolicyViolationException` with code `INCOME_BELOW_MINIMUM_THRESHOLD` (AC-05).

3. **Deterministic Credit Scoring**:
   - Compute score using formula: $600 + (\text{Income} / 1000 \times 2) + (\text{Age} \times 1.5) - (\text{Defaults} \times 150)$ clamped to $[300, 850]$ (AC-03).

4. **Underwriting Decisioning**:
   - If score >= `autoApproveScore` and defaults == 0 -> `AUTO_APPROVE` (`AUTO_APPROVE_LOW_RISK`).
   - If score < `autoRejectScore` or defaults > 1 -> `AUTO_REJECT` (`AUTO_REJECT_HIGH_RISK`).
   - Otherwise -> `MANUAL_REVIEW` (`MANUAL_REVIEW_BORDERLINE`) (AC-04).

5. **Generate Audit Record**:
   - Record decision outcome, reason code, active policy version ID, and timestamp.
