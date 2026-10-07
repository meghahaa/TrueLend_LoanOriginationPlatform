# Feature Spec — Underwriting, Document Verification, Override
Covers AC-04, AC-06, AC-10 (override part). Rules live in `src/domain/underwriting_decision.py`; thresholds come only from the active policy.

## Automated decision (AC-04) — evaluated after the policy gate and score
`FOIR = EMI(amount, policy rate, tenure) / monthly_income` (Decimal, 4 dp compare to `max_foir`).
1. `has_default` → `AUTO_REJECT`, reason `PRIOR_DEFAULT` (add `SCORE_BELOW_REJECT` too if it also applies).
2. `score < reject_score` → `AUTO_REJECT`, `SCORE_BELOW_REJECT`.
3. `score ≥ approve_score` and `FOIR ≤ max_foir` → `AUTO_APPROVE`, `SCORE_ABOVE_APPROVE`.
4. otherwise → `MANUAL_REVIEW`: add `SCORE_IN_REVIEW_BAND` if `reject_score ≤ score < approve_score`; add `FOIR_EXCEEDED` if `FOIR > max_foir`.
Result stored with `policy_version`, `score`, `reason_codes`. Status mapping: AUTO_APPROVE → `APPROVED` (schedule generated, see repayment spec); AUTO_REJECT → `REJECTED`; MANUAL_REVIEW → `MANUAL_REVIEW`.

## Document verification queue (AC-06)
`GET /underwriter/queue` lists applications in `MANUAL_REVIEW` or with any `UPLOADED` document, oldest first. `POST …/documents/{doc_type}/verify` body `{status: VERIFIED|REJECTED, reason}`; reason mandatory for REJECTED. Only `UPLOADED` documents can be verified (409 otherwise). A `REJECTED` document lets the customer re-upload (→ `UPLOADED`). Each action is audited.

## Manual decision
`POST /applications/{id}/decision` `{action: APPROVE|REJECT, reason_code, comment}` only from `MANUAL_REVIEW`. APPROVE requires all required documents `VERIFIED` (else 409 `DOCUMENTS_NOT_VERIFIED`) → `APPROVED` + schedule, reason `MANUAL_APPROVED`. REJECT → `REJECTED`, reason `MANUAL_REJECTED`. Audited.

## Admin override of AUTO_REJECT (AC-10)
`POST /admin/applications/{id}/override` `{reason_code, comment}` (both mandatory, non-blank). Only for applications whose decision is `AUTO_REJECT` and status `REJECTED`; result: status `APPROVED`, schedule generated, override record keeps original decision, original reason codes and the new `ADMIN_OVERRIDE` code. Audited (admin id, UTC timestamp, reason, comment). Does not apply to manual rejections (409).

## Acceptance Criteria
- **AC-04** Given PERSONAL score 740, FOIR ≤ 0.50, no default, when decided, then `AUTO_APPROVE` with `SCORE_ABOVE_APPROVE` and the active `policy_version`.
- **AC-04a** Given score below `reject_score`, then `AUTO_REJECT` + `SCORE_BELOW_REJECT`; given `has_default`, then `AUTO_REJECT` + `PRIOR_DEFAULT`.
- **AC-04b** Given score between reject and approve, then `MANUAL_REVIEW` + `SCORE_IN_REVIEW_BAND`; given score ≥ approve but FOIR above max, then `MANUAL_REVIEW` + `FOIR_EXCEEDED`.
- **AC-04c** Given policy v002 changed `approve_score`, when a new application is decided, then v002 thresholds and version are used while an older application still shows v001.
- **AC-04d** Boundary: score exactly `approve_score` approves; exactly `reject_score` is not rejected by score.
- **AC-06** Given an `UPLOADED` document, when the underwriter marks it VERIFIED, then its status is VERIFIED and an audit row exists.
- **AC-06a** Given REJECTED without a reason, then 422; with a reason, then status REJECTED and the customer sees the reason.
- **AC-06b** Given a `MISSING` or already `VERIFIED` document, then verify returns 409.
- **AC-06c** Given a CUSTOMER token, the queue and verify endpoints return 403.
- **AC-06d** Manual APPROVE with an unverified required document → 409 `DOCUMENTS_NOT_VERIFIED`; with all VERIFIED → `APPROVED` + schedule.
- **AC-10a** Given an `AUTO_REJECT` application, when an admin overrides with comment and reason code, then status `APPROVED`, schedule exists, and the audit shows user id, timestamp, reason and comment.
- **AC-10b** Override without a comment or reason code → 422; by an UNDERWRITER or CUSTOMER → 403; on an `AUTO_APPROVE`/manual-rejected application → 409.
- **NFR-04** Every underwriter/admin action in this spec writes exactly one audit row with `user_id` and UTC `timestamp`.
