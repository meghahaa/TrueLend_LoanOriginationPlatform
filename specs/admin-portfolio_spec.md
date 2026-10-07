# Feature Spec — Admin: Application List, Portfolio, Audit
Covers the list/filter part of AC-10 and the Admin Dashboard (override itself is in `underwriting_spec.md`).

## Behaviour
- `GET /admin/applications?status=&product=&page=&page_size=` (ADMIN): filters combine with AND; invalid enum value → 422; default page_size 20 (max 100); newest first. Items show id, product, amount, status, decision, bucket, policy_version, masked identifiers.
- `GET /admin/portfolio` (ADMIN): per product `{count, disbursed_amount, outstanding_principal}`; per bucket `{count, outstanding_principal}`; `npa_count`, `npa_outstanding`; `total_overdue` = Σ(unpaid instalment amounts with due date < today) across disbursed loans. Money as strings.
- `GET /admin/audit?application_id=` (ADMIN): audit rows newest first (`user_id`, `role`, `timestamp`, `action`, `application_id`, `reason_code`, `comment`). Audit rows are insert-only.

## Acceptance Criteria
- **AC-10** Given seeded applications, when an admin lists with `status=REJECTED&product=PERSONAL`, then only matching applications return.
- **AC-10c** Given no filters, then all applications return paginated, newest first; given `status=BOGUS`, then 422.
- **AC-10d** Given a customer or underwriter token, list/portfolio/audit return 403.
- **AC-10e** Given the seed data, the portfolio shows the three seeded disbursed loans bucketed `CURRENT`, `DPD-60`, `NPA`, `npa_count = 1`, and `total_overdue` equals the sum of overdue instalments computed independently in the test.
- **AC-10f** After an override (see underwriting spec), `GET /admin/audit` contains the override row with user id, timestamp, reason code and comment.
