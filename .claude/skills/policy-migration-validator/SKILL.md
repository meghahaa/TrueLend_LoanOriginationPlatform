---
name: policy-migration-validator
description: Validates loan policy schema compliance, version immutability, and backward compatibility.
---

# Policy Migration Validator Skill

This skill provides validation workflows for policy version updates and DB migrations.

## Execution Steps

1. **Verify Immutability**:
   - Ensure existing policy files under `src/main/resources/policies/` have not been edited.
   - Verify new policy files introduce a new version number (e.g. `policy-v1.1.json`).

2. **Validate Schema & Bounds**:
   - Check all required fields (`minIncome`, `minCreditScore`, `interestRate`, `requiredDocuments`).
   - Validate numeric bounds (`interestRate > 0`, `minCreditScore >= 300`).

3. **Check Backward Compatibility**:
   - Confirm active loans referencing older policy versions (`v1.0`) retain their historical policy context.
