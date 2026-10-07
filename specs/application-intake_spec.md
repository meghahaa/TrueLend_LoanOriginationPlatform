# Feature Spec — Application Intake, Credit Score, Policy Gate
Covers AC-02, AC-03, AC-05. Policy source: active policy (`product-catalog_spec.md`).

## Request (`POST /applications`, CUSTOMER)
`product`, `amount`, `tenure_months`, applicant `{full_name, age:int, monthly_income, pan, aadhaar, credit_history, has_default}`, optional `documents:[{doc_type, filename}]` (stubbed upload: filename recorded, **content never stored**).
Response 201: `{id, status, decision, reason_codes, policy_version, score, documents:[{doc_type,status}], missing_documents:[…]}`; PAN/Aadhaar masked (`XXXXXX1234`).

## Required-document checklist (AC-02)
Created at submission from the product's `required_documents`. Doc present in the request → `UPLOADED`; otherwise `MISSING`. `POST /applications/{id}/documents` uploads a missing/rejected doc (→ `UPLOADED`). Track view (`GET /applications/{id}`) shows status, missing documents, decision, reason codes.

## Policy gate (AC-05) — runs first
Check in order, collecting all violations: income < `min_monthly_income` → `INCOME_BELOW_MIN`; age outside [min,max] → `AGE_OUT_OF_RANGE`; amount outside range → `AMOUNT_OUT_OF_RANGE`; tenure outside range → `TENURE_OUT_OF_RANGE`. Any violation → raise `PolicyViolationException(reason_codes, policy_version)` → HTTP 422; **no application is persisted** and nothing sensitive is logged (log codes + policy version only). Boundary values equal to the minimum pass.

## Credit score stub (AC-03) — deterministic, pure function
`score = clamp(300 + age_pts + income_pts + history_pts − default_pen, 300, 900)`
- age_pts: 18–20 → 20; 21–25 → 40; 26–35 → 80; 36–50 → 100; 51–65 → 60; > 65 → 20
- income_pts (monthly): < 25000 → 40; 25000–49999.99 → 100; 50000–99999.99 → 160; ≥ 100000 → 220
- history_pts: CLEAN → 200; THIN → 80; LATE_PAYMENTS → 0
- default_pen: `has_default` → 100, else 0
Same inputs always give the same score; integer arithmetic only. Reference values: age 30, income 60000, CLEAN, no default → 740; age 22, income 20000, LATE_PAYMENTS, default → 300 (clamped from 280).

## Acceptance Criteria
- **AC-02** Given a PERSONAL application, when submitted, then the response lists the 4 PERSONAL required documents; for EDUCATION it lists its 5 (checklists differ per product).
- **AC-02a** Given documents uploaded for 2 of 4, when the application is tracked, then 2 are `UPLOADED` and 2 appear in `missing_documents`.
- **AC-02b** Given a missing document, when the owner uploads it, then its status becomes `UPLOADED`; given another customer's token, then 403.
- **AC-02c** Given a submitted application, when the owner tracks it, then status, decision, reason codes and masked PAN/Aadhaar are returned (no full identifiers).
- **AC-03** Given age 30, income 60000, CLEAN, no default, when scored, then 740, and repeated calls return the same value.
- **AC-03a** Given each age band, income band and history flag, when scored, then each contribution matches the tables above (parametrised test).
- **AC-03b** Given inputs whose raw sum is below 300 or above 900, then the score is clamped to 300 / 900.
- **AC-05** Given PERSONAL with income 24999.99 (min 25000.00), when submitted, then `PolicyViolationException` with `INCOME_BELOW_MIN` and policy version; HTTP 422; no application row.
- **AC-05a** Given income exactly 25000.00, then no income violation.
- **AC-05b** Given age 17 / amount above max / tenure below min, then `AGE_OUT_OF_RANGE` / `AMOUNT_OUT_OF_RANGE` / `TENURE_OUT_OF_RANGE`; multiple violations are all reported.
- **AC-05c** Given a violation, then captured logs contain reason codes but not the PAN or Aadhaar (NFR-03).
