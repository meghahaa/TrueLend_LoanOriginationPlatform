# AGENTS.md — Table of Contents
Index only. Rules live in the linked files.

## Specs (source of truth)
- `specs/app_spec.md` — root spec, enums, API summary, seed data, sprint plan
- `specs/product-catalog_spec.md` — AC-01, policy versioning, policy editor
- `specs/application-intake_spec.md` — AC-02, AC-03, AC-05
- `specs/underwriting_spec.md` — AC-04, AC-06, AC-10
- `specs/repayment_spec.md` — AC-07, AC-09, EOD job
- `specs/disbursement_spec.md` — AC-08
- `specs/admin-portfolio_spec.md` — admin list, dashboard, audit

## Domain and design docs
- `docs/business-case.md` · `docs/architecture.md` · `docs/tdd.md` · `docs/postmortems/`

## Guidance (CLAUDE.md hierarchy)
- `CLAUDE.md` · `src/CLAUDE.md` · `src/domain/CLAUDE.md` · `src/services/CLAUDE.md` · `src/repositories/CLAUDE.md` · `src/api/CLAUDE.md` · `frontend/CLAUDE.md` · `tests/CLAUDE.md`

## Project substrate (`.claude/`)
- Agents: `underwriting-agent`, `repayment-schedule-agent`, `policy-validator-agent` (plus harness agents)
- Skills: `loan-policy-evaluator`, `repayment-schedule-builder`, `spec-to-test-generator` (plus harness skills)
- Commands: `/ac-coverage`, `/new-policy-version`, `/post-mortem`, `/sprint-cost`
- Hooks: `policy-immutability-check.js`, `money-precision-check.js`, `pii-log-check.js` (plus harness hooks)

## Other
- `.importlinter` layering contracts · `scripts/ac_coverage.py` AC traceability · `.github/workflows/ci.yml` + `.gitlab-ci.yml` (kept in parity) · `policies/` versioned policy files · `scripts/agent_sdk_runner.py` · `plugin.json` · `.mcp.json` · `sprint-contracts/` · `specs/reviews/`
