---
name: repayment-schedule-builder
description: Use when implementing EMI, amortisation schedule, repayment allocation, outstanding principal or DPD buckets in TrueLend. Gives the exact Decimal algorithm, invariants and reference values.
---
# Repayment schedule builder

**Source of truth:** `specs/repayment_spec.md`.

## Algorithm (Decimal, precision ≥ 28)
```
r = annual_rate_percent / 12 / 100
EMI = quantize(P*r*(1+r)**n / ((1+r)**n - 1))      # r == 0 → quantize(P/n)
for k in 1..n:
    interest = quantize(balance * r)
    principal = EMI - interest          # k == n: principal = balance
    amount    = EMI                     # k == n: principal + interest
    balance  -= principal
```
`quantize` = 2 dp, `ROUND_HALF_UP`. Build `Decimal` from `str`/`int`; never from `float`.

## Invariants (assert in code paths and tests)
Σprincipal == P · final balance == 0.00 · Σprincipal + Σinterest == Σamount == total_payable · every amount ≥ 0.

## Reference values
300000 @12.50 %/36 → EMI 10036.09, last 10035.97, total 361299.12 · 120000 @12 %/12 → 10661.85, last 10661.91, total 127942.26 · 100000 @0 %/10 → 10000.00 · 1000000 @9.5 %/84 → 16343.98, total 1372894.56.

## Allocation and buckets
Oldest unpaid instalment first, interest before principal; state derived from insert-only `repayment_allocations`. DPD = days since due date of the oldest unpaid instalment; thresholds from policy `bucket_thresholds`.

## Test matrix
Reference loans; grid (50k–4M × 0–15 % × 12–120 m) invariant; month-end due-date clamp; partial payment below interest; multi-instalment payment; DPD boundaries 29/30/59/60/89/90/179/180; overpayment; full payoff.

## Pitfalls
`round()`/`float` anywhere; rounding the total instead of each instalment; forgetting the last-instalment adjustment; updating schedule rows to mark paid.
