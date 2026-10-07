# TrueLend — Root Spec (app_spec.md)
Status: authoritative. Feature specs: `product-catalog`, `application-intake`, `underwriting`, `repayment`, `disbursement`, `admin-portfolio` (`specs/<name>_spec.md`).
Business context: `docs/business-case.md`. Design: `docs/architecture.md`.

## 1. Purpose and scope
A policy-driven loan origination platform: a customer applies for a Personal, Vehicle or Education loan; rules from a versioned policy file drive underwriting; approved loans get an EMI schedule, a stubbed disbursement, and repayments that update outstanding principal and a delinquency bucket. Business users change thresholds by publishing a new policy version — no code change.

Out of scope: real bureau/OCR/payment rails, collections, FX, production deployment/secrets.

## 2. Actors and auth (demo)
| Token | User id | Role |
|---|---|---|
| `demo-customer-1` | `cust-001` | CUSTOMER |
| `demo-customer-2` | `cust-002` | CUSTOMER |
| `demo-underwriter-1` | `uw-001` | UNDERWRITER |
| `demo-admin-1` | `adm-001` | ADMIN |
Header: `Authorization: Bearer <token>`. Missing/unknown → 401; wrong role/owner → 403. Public: `GET /health`, `GET /products`.

## 3. Stack and run
Python 3.11+ / FastAPI / SQLite; React + Vite + TS frontend. `python -m src` is the single run command: applies migrations, seeds if empty, builds `frontend/dist` if missing and `npm` exists, serves API + UI on `:8000`. README must contain a quick-start.

## 4. Enums and shared definitions
- Product: `PERSONAL`, `VEHICLE`, `EDUCATION`
- Decision: `AUTO_APPROVE`, `AUTO_REJECT`, `MANUAL_REVIEW`
- Application status: `SUBMITTED`(transient), `MANUAL_REVIEW`, `APPROVED`, `REJECTED`, `DISBURSED`
- Document status: `MISSING`, `UPLOADED`, `VERIFIED`, `REJECTED`
- Credit history: `CLEAN`, `THIN`, `LATE_PAYMENTS`; flag `has_default` (bool)
- Bucket: `CURRENT`, `DPD-30`, `DPD-60`, `DPD-90`, `NPA`
- Reason codes (only these): `INCOME_BELOW_MIN`, `AGE_OUT_OF_RANGE`, `AMOUNT_OUT_OF_RANGE`, `TENURE_OUT_OF_RANGE`, `SCORE_ABOVE_APPROVE`, `SCORE_BELOW_REJECT`, `SCORE_IN_REVIEW_BAND`, `FOIR_EXCEEDED`, `PRIOR_DEFAULT`, `MANUAL_APPROVED`, `MANUAL_REJECTED`, `ADMIN_OVERRIDE`
- Money: `Decimal`, 2 dp, ROUND_HALF_UP, strings on the wire. Currency INR (single, implicit).
- Active policy = highest `policies/loan_policy.vNNN.json`. Every decision stores its `policy_version`.

## 5. Non-functional requirements (each needs a test tagged with its id)
| ID | Requirement | Verified by |
|---|---|---|
| NFR-01 | Money is fixed-point `Decimal`, never `float` | AST scan test in `tests/architecture/` + unit tests |
| NFR-02 | Approved policy versions and repayment schedules are append-only | repo has no UPDATE/DELETE on them; hash-baseline test |
| NFR-03 | Synthetic PAN/Aadhaar and salary documents never logged | log-capture test |
| NFR-04 | Auth enforced at controller layer; underwriter/admin actions audited (user id + timestamp) | API tests; import test (services don't import api) |
| NFR-05 | DB and policy migrations are append-only | hash-baseline test of `migrations/` and `policies/` |
| NFR-06 | Structured JSON logs with correlation id | log-capture test |
| NFR-07 | `/health` returns 200 within 1 s of startup | API test with timing assertion |
| NFR-08 | Architecture rules are automated tests (policy immutable, EMI invariant, layering) | `tests/architecture/` |

## 6. API summary
| Method & path | Role | Feature |
|---|---|---|
| `GET /health` | public | NFR-07 |
| `GET /products` | public | product-catalog |
| `POST /applications` | CUSTOMER | application-intake |
| `GET /applications/{id}` | owner/staff | application-intake |
| `POST /applications/{id}/documents` | owner | application-intake |
| `GET /underwriter/queue` | UNDERWRITER, ADMIN | underwriting |
| `POST /applications/{id}/documents/{doc_type}/verify` | UNDERWRITER, ADMIN | underwriting |
| `POST /applications/{id}/decision` | UNDERWRITER, ADMIN | underwriting |
| `POST /admin/applications/{id}/override` | ADMIN | underwriting |
| `GET /applications/{id}/schedule` | owner/staff | repayment |
| `POST /applications/{id}/repayments` | owner/staff | repayment |
| `POST /admin/jobs/eod-buckets` | ADMIN | repayment |
| `POST /applications/{id}/disburse` | UNDERWRITER, ADMIN | disbursement |
| `GET /admin/applications?status=&product=` | ADMIN | admin-portfolio |
| `GET /admin/portfolio` | ADMIN | admin-portfolio |
| `GET /admin/audit` | ADMIN | admin-portfolio |
| `GET /admin/policies`, `POST /admin/policies` | ADMIN | product-catalog |
Error shape: `{"code": "...", "message": "...", "reason_codes": [...], "policy_version": 1}` (reason fields only when relevant).

## 7. Seed data (synthetic, created at first start)
3 products from the active policy plus customers `cust-001`, `cust-002` and 6 applications: (1) PERSONAL AUTO_APPROVE → disbursed, 2 on-time payments, `CURRENT`; (2) VEHICLE disbursed, no payments, first due 75 days ago → `DPD-60`; (3) PERSONAL disbursed, first due 200 days ago → `NPA`; (4) EDUCATION `MANUAL_REVIEW` with documents `UPLOADED`; (5) PERSONAL `AUTO_REJECT` (override demo); (6) VEHICLE `APPROVED`, not yet disbursed. Seeded disbursed loans (1–3) have all required documents `VERIFIED` (disbursement precondition). Dates are computed relative to today. PAN `TESTP1234X`-style, Aadhaar `9999 0000 000N`.

## 8. Sprint plan (guidance for planner)
| Sprint | Scope | ACs |
|---|---|---|
| S1 | project skeleton, migrations, logging/health/auth, policy repo, catalog, scoring, intake, decision | AC-01..05, NFR-03..08 |
| S2 | document verification, manual decision, override+audit, EMI schedule, disbursement, repayment, buckets, EOD, portfolio | AC-06..10, NFR-01,02 |
| S3 | React UI (Apply/Track/Repay/Workbench/Policy Editor/Dashboard), Playwright + snapshots, seed, README | UI for all journeys |

## 9. Definition of Done (per sprint)
Tests green with ≥ 80 % coverage, `lint-imports` clean, `scripts/ac_coverage.py` shows no missing ids, hooks passed, evaluator report in `specs/reviews/`, sprint contract in `sprint-contracts/`, merged by PR.
