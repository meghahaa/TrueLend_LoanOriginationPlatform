# Knowledge Deposit Log & Substrate Rule Feedback

## Overview
This log documents recurring mistakes, edge cases, and architectural drifts encountered during AI-native development. Each issue is analyzed and encoded back into permanent substrate guardrails (hooks, rules, or agent instructions) to prevent recurrence.

---

## Deposit #1: Primitive Floating-Point Interest Calculation Leak
- **Symptom**: Initial draft of EMI schedule calculation used `double` for intermediate monthly rate $r_m = \text{annualRate} / 1200.0$, causing 1-cent rounding discrepancies across 36-month schedules.
- **Root Cause**: Developer agent used primitive double division instead of `BigDecimal` division with explicit `RoundingMode.HALF_UP` scale.
- **Substrate Action Encoded**:
  1. Created hook `.claude/hooks/interest-precision-check.sh` to fail any commit containing `double` or `float` in monetary calculations.
  2. Updated `CLAUDE.md` and `repayment-schedule-agent.md` with explicit `BigDecimal` rules.

---

## Deposit #2: Mutation of Approved Policy Version File
- **Symptom**: Underwriter policy edit feature attempted to overwrite existing `policy-v1.0.json` in place.
- **Root Cause**: Missing immutability constraint in file persistence service.
- **Substrate Action Encoded**:
  1. Created hook `.claude/hooks/policy-immutability-check.sh` enforcing append-only version filenames (e.g. `policy-v1.1.json`).
  2. Created skill `.claude/skills/policy-migration-validator/SKILL.md` to validate version progression.

---

## Deposit #3: Un-audited Underwriter Overrides
- **Symptom**: Admin override endpoint updated application status to `APPROVED` without logging the overriding admin user ID and reason code.
- **Root Cause**: Controller endpoint omitted mandatory audit payload mapping.
- **Substrate Action Encoded**:
  1. Updated `underwriting-agent.md` system prompt requiring audit log creation for all status overrides.
  2. Added AC-10 integration test assertion checking audit table record insertion.
