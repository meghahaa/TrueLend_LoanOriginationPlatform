---
name: repayment-schedule-builder
description: Generates fixed-point EMI amortization schedules and recalculates DPD delinquency buckets.
---

# Repayment Schedule Builder Skill

This skill provides step-by-step instructions for constructing fixed-point repayment schedules and managing repayment postings.

## Execution Steps

1. **Calculate Fixed-Point EMI**:
   - Monthly rate $r_m = \text{annualRate} / 1200$.
   - Calculate EMI using `BigDecimal` with scale 2 and `RoundingMode.HALF_UP`.
   - Formula: $EMI = \frac{P \times r_m \times (1 + r_m)^n}{(1 + r_m)^n - 1}$.

2. **Generate Monthly Schedule**:
   - For each month $i = 1 \dots n$:
     - Interest $I_i = \text{Balance}_{i-1} \times r_m$.
     - Principal $P_i = EMI - I_i$.
     - Balance $B_i = \text{Balance}_{i-1} - P_i$.

3. **Apply Final Installment Balancing**:
   - For month $n$: set $P_n = B_{n-1}$, set $EMI_n = P_n + I_n$, set balance $B_n = 0.00$.

4. **Verify Invariants**:
   - Check $\sum P_i == \text{Original Principal}$.
   - Check $\sum P_i + \sum I_i == \text{Total Payable}$.

5. **Repayment Posting & Delinquency Bucketing**:
   - When repayment is received, subtract from balance.
   - Recalculate Days Past Due (DPD).
   - Classify bucket: `CURRENT` (0 DPD), `DPD-30` (1-30), `DPD-60` (31-60), `DPD-90` (61-90), `NPA` (>90).
