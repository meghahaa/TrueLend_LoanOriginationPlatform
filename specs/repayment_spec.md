# Feature Spec — Repayment Schedule, Posting, Buckets, EOD
Covers AC-07, AC-09, NFR-01, NFR-02. Rules: `emi_calculator.py`, `repayment_allocation.py`, `dpd_bucket.py`.

## EMI and schedule (AC-07)
`r = annual_rate_percent / 12 / 100`; `EMI = P·r·(1+r)^n / ((1+r)^n − 1)`; if `r = 0`, `EMI = P / n`. All `Decimal` (context precision ≥ 28); round to 2 dp ROUND_HALF_UP **only** where stated.
Per instalment k: `interest_k = round(opening_balance·r)`; `principal_k = EMI − interest_k`; last instalment: `principal_n = opening_balance`, `amount_n = principal_n + interest_n` (absorbs rounding). Due dates monthly, first = approval date + 1 month (clamp to month end).
**Invariants:** Σprincipal = P exactly; closing balance of the last row = 0.00; Σprincipal + Σinterest = Σinstalment amounts = `total_payable` (stored on the loan).
Reference: P=300000, 12.50 %, 36 m → EMI 10036.09, last instalment 10035.97, total payable 361299.12, interest 61299.12. P=120000, 12 %, 12 m → EMI 10661.85, last 10661.91, total 127942.26. P=100000, 0 %, 10 m → EMI 10000.00, total 100000.00. P=1000000, 9.5 %, 84 m → EMI 16343.98, total 1372894.56.
Schedule rows are insert-only (generated once per loan; regeneration attempt → error). Payment state is stored in `repayment_allocations`.

## Posting (AC-09)
`POST /applications/{id}/repayments` `{amount, paid_on}` (owner or staff; loan must be `DISBURSED`, else 409). Amount > 0 (else 422) and ≤ total remaining due (else 422 `AMOUNT_EXCEEDS_OUTSTANDING`). Waterfall: oldest unpaid instalment first, interest before principal, then next instalment. Insert one `repayments` row and allocation rows; **outstanding principal** = P − Σprincipal allocated. Bucket recalculated immediately. Response: `{outstanding_principal, total_remaining_due, bucket, dpd, allocations}`. Fully repaid → outstanding 0.00, bucket `CURRENT`.

## DPD and buckets
`dpd` = days between `as_of` and the due date of the oldest instalment not fully paid, 0 if none overdue (`as_of ≤ due`). Thresholds from the policy `bucket_thresholds`: dpd < 30 → `CURRENT`; 30–59 → `DPD-30`; 60–89 → `DPD-60`; 90–179 → `DPD-90`; ≥ 180 → `NPA`. (Synthetic thresholds; changing them is a policy change.)

## End-of-day job
`POST /admin/jobs/eod-buckets` `{as_of?}` (ADMIN; default = clock today). Recalculates dpd and bucket for every `DISBURSED` loan; idempotent; returns counts per bucket. Also runnable as `python -m src.jobs.eod`.

## Acceptance Criteria
- **AC-07** Given an approved loan P=300000, 12.50 %, 36 m, when the schedule is generated, then 36 rows, EMI 10036.09, Σprincipal+Σinterest = 361299.12 = `total_payable`, Σprincipal = 300000.00, final balance 0.00.
- **AC-07a** Reference loans above (12 m / 0 % / 84 m) match the stated EMI and totals.
- **AC-07b** Invariant holds over a grid (principal 50k–4M, rate 0–15 %, tenure 12–120); no instalment is negative.
- **AC-07c** Given 0 % rate, EMI = P/n and total interest 0.00.
- **AC-07d** Given a schedule already exists, regenerating raises an error and no rows change (NFR-02).
- **AC-07e** Given approval on Jan 31, the first due date is Feb 28/29 (month-end clamp).
- **AC-09** Given outstanding 300000.00 and a payment of exactly one EMI, then outstanding principal falls by that instalment's principal and bucket is recalculated.
- **AC-09a** Partial payment smaller than the interest portion: only interest is allocated; principal unchanged.
- **AC-09b** Payment covering two instalments plus part of a third allocates oldest-first, interest before principal.
- **AC-09c** Given first due date 75 days before `as_of` with no payments, bucket `DPD-60`; 200 days → `NPA`; 29 → `CURRENT`; 30 → `DPD-30`; 90 → `DPD-90` (boundary tests).
- **AC-09d** Paying the overdue instalments brings the bucket back to `CURRENT`.
- **AC-09e** Zero/negative amount → 422; above remaining due → 422; not `DISBURSED` → 409; another customer's loan → 403.
- **AC-09f** EOD job updates every disbursed loan's bucket and is idempotent (second run changes nothing).
- **NFR-01** No `float` in money modules (AST scan); EMI computed with `Decimal`.
- **NFR-02** No UPDATE/DELETE path exists for schedule rows (repository test).
