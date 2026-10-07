# TrueLend — Business Case
This is the domain document read by reviewers and agents. Behaviour is specified in `specs/`; this file explains *why* and defines the vocabulary. All data in the project is synthetic.

## 1. Problem
A retail bank launches loan products slowly because eligibility, pricing and risk thresholds are buried in application code: every change to a minimum income or a score cut-off needs a developer, a release and a regression cycle. Underwriters also work from inconsistent checklists, borderline cases get decided differently from person to person, and nobody can later prove *which* rules were in force when a loan was approved. Money maths done carelessly (floating point, ad-hoc rounding) produces schedules that do not add up, and overrides of automated rejections are not reliably recorded.

TrueLend is a configurable origination platform that carries a loan from application to disbursement to repayment, with underwriting rules supplied by a versioned policy file that business users can change without touching code.

## 2. Target users
| User | Needs |
|---|---|
| **Customer** (salaried applicant, student with co-applicant) | Pick a product, know which documents to provide, see status and the *reason* for a decision, view the schedule, pay and see what is still owed |
| **Underwriter** | A single queue, per-document verification with reasons, clear automated recommendation with reason codes, ability to approve/reject borderline cases |
| **Credit/product manager** (admin) | Change thresholds per product safely, see portfolio health, override an automated rejection with accountability |
| **Risk & audit** | Immutable history: which policy version decided, who acted, when |

## 3. Value proposition
- **Speed to market:** a new product or threshold is a new policy version, not a software release.
- **Consistency:** the same inputs always yield the same decision and score; reason codes make decisions explainable to customers and auditors.
- **Control:** every override and underwriter action carries a user id, timestamp and reason; approved policies and schedules can never be rewritten.
- **Accuracy:** fixed-point money; repayment schedules whose principal and interest provably add up to the total payable.
- **Visibility:** delinquency buckets and NPA exposure at a glance.

## 4. Success metrics (targets for the prototype)
| Metric | Target |
|---|---|
| Decisions that are reproducible from (inputs, policy version) | 100 % |
| Applications auto-decided without human touch (seed profile mix) | ≥ 60 % |
| Schedules where Σprincipal + Σinterest = total payable | 100 % (property-tested) |
| New threshold live without code change | publish policy vNNN → next application uses it |
| Underwriter/admin actions with audit row | 100 % |
| Sensitive identifiers appearing in logs | 0 |
| `GET /health` after startup | 200 in < 1 s |
| Acceptance criteria with ≥ 1 passing test | 100 % |

## 5. Domain rules
**Products (seed policy v001)** — Personal, Vehicle, Education; each with income floor, age range, amount range, tenure range, annual rate, approve/reject score cut-offs, maximum FOIR, and a required-document list. Exact values: `policies/loan_policy.v001.json`.
**Lifecycle:** application → policy gate → score → decision (auto approve / auto reject / manual review) → document verification → approval → schedule → disbursement → repayments → bucket tracking.
**Policy gate:** an application below the income floor (or outside age/amount/tenure ranges) is refused outright with a `PolicyViolationException`; it never becomes an application.
**Credit score (stub):** deterministic function of age band, income band and credit-history flags, 300–900. A real bureau is out of scope.
**FOIR (Fixed Obligation to Income Ratio):** monthly EMI ÷ monthly income; capped per product.
**EMI:** `P·r·(1+r)ⁿ / ((1+r)ⁿ − 1)` with monthly rate `r = annual % / 12 / 100`; interest each month on the opening balance; final instalment absorbs rounding so the balance ends at exactly zero.
**Repayment allocation:** oldest unpaid instalment first; interest before principal.
**Delinquency (DPD = days past due on the oldest unpaid instalment):** CURRENT < 30, DPD-30, DPD-60, DPD-90, NPA ≥ 180 (synthetic thresholds held in policy). NPA = Non-Performing Asset.
**Override:** only an admin can reverse an automated rejection, and only with a reason code and comment; the original decision stays on record.
**Immutability:** published policy versions and generated schedules are append-only. Applications remember the policy version that decided them.
**Data handling:** synthetic PAN/Aadhaar and document contents are never logged; responses mask identifiers.

## 6. Scope
In: product catalog, application intake, document checklist/verification, scoring, underwriting decision, policy editor, schedule, stubbed disbursement, repayment posting, EOD bucket job, admin list/override/portfolio, audit.
Out: real bureau, OCR, payment rails, collections/recovery, multi-currency, production deployment, secrets management.

## 7. Assumptions and risks
- Single currency (INR), single bank, demo-token auth stands in for real identity.
- Bucket and score thresholds are illustrative, not regulatory guidance.
- Risk: rules that exist only in code drift from policy → mitigated by spec-is-truth and architecture tests.
- Risk: rounding drift in schedules → mitigated by fixed-point maths and the invariant test grid.
