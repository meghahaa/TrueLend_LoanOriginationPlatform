# TrueLend — Loan Origination Platform

Configurable, policy-driven loan origination (apply → underwrite → disburse → repay).
**Agents write all code. Humans edit only specs, docs, CLAUDE.md, agents, skills, commands, hooks.**

## Source of truth (highest first)
1. `specs/*_spec.md` and `specs/app_spec.md` — behaviour and Acceptance Criteria (ACs)
2. `docs/business-case.md` — domain rules and vocabulary
3. This file and the nested `CLAUDE.md` files — how to work

Specs and `docs/business-case.md` already exist: **do not regenerate, rewrite or overwrite anything under `specs/` or that doc** (skip any BRD/spec-generation step; planning reads them).
If code and spec disagree, the spec wins. If the spec looks wrong or ambiguous: **stop and report it**. Never silently change a spec and never bend code around it.

## Stack and commands
Python 3.11+, FastAPI, SQLite (stdlib `sqlite3`), pytest + pytest-cov, import-linter. Frontend: React + Vite + TypeScript, Vitest, Playwright.
- Run app: `python -m src` (seeds DB if empty; serves API + `frontend/dist`)
- Backend tests: `pytest --cov=src --cov-report=xml --cov-fail-under=80`
- Layering check: `lint-imports` (config: `.importlinter`, already provided — extend, don't rewrite)
- AC coverage: `python scripts/ac_coverage.py` (already provided; every AC/NFR id in specs must appear in a test)
- Frontend: `cd frontend && npm test` / `npm run build`; E2E: `npx playwright test`

## Layering (enforced by import-linter and `tests/architecture/`)
`api → services → repositories → domain`. `domain` imports nothing from the project and no framework/IO (`fastapi`, `sqlite3`, `os`, `datetime.now`). Details: `docs/architecture.md`.

## Non-negotiable rules
- **Money (NFR-01):** `decimal.Decimal` only, built from `str`/`int`, never `float`. 2 dp, `ROUND_HALF_UP`. Serialise as strings.
- **Append-only (NFR-02/05):** policy versions (`policies/loan_policy.vNNN.json`), repayment schedule rows and `migrations/*.sql` are insert-only. Change = new file / new rows. A hook blocks edits to existing ones.
- **No sensitive logging (NFR-03):** PAN, Aadhaar and document contents never appear in logs, exceptions or API error bodies. Mask as `XXXXXX1234` in responses.
- **Auth at controllers only (NFR-04):** role checks live in `src/api`. Services receive an `Actor(user_id, role)`. Every underwriter/admin action writes an audit row (user id, UTC timestamp, action, application id).
- **Logging (NFR-06):** JSON logs with `correlation_id` (from `X-Correlation-ID` or generated). `GET /health` → 200 in < 1 s.
- **Time:** inject a `Clock`; no direct `datetime.now()` in domain or services.
- **Synthetic data only.** No real names, PAN, Aadhaar, bank details.

## Testing and AC tagging
- TDD: write the failing test first, commit it (`test(AC-05): red …`), then implement (`feat(AC-05): green …`), then `refactor:`.
- Every test names its AC/NFR: pytest `@pytest.mark.ac("AC-05")` + name `test_ac05_<behaviour>`; Vitest/Playwright titles start with `AC-05`.
- Cover branches of each rule (see `src/domain/CLAUDE.md`). Never weaken or delete a test to get green.

## Git workflow
- Never commit to `main`. Branch `feat/<sprint>-<slug>`; open a PR/MR (GitHub: `gh pr create`; GitLab: `glab mr create`); after review merge with a **merge commit**, never squash or fast-forward (GitHub: `gh pr merge --merge`; GitLab: `glab mr merge` with project merge method = Merge commit).
- Conventional commits mention the AC ids. One concern per PR.
- Do not stage `.env`, `*.db`, `node_modules`, `coverage` artefacts except `coverage.xml`.

## Environment-first debugging
On any failure (command not found, port busy, import error, version mismatch, Windows path/shell issue): check the environment *before* touching code — versions, PATH, venv active, ports, installed deps, working directory. Fix the environment, then record it with `/post-mortem`. Do not "fix" application code to work around an environment problem.

## Cost discipline (budget is small)
Read only the files the task needs; read the relevant spec section, not every spec. Run targeted tests (`pytest -k`, `-m "ac"`) while iterating and the full suite once before a PR. Do not run Playwright outside the evaluator step. No unrequested refactors, no speculative features. Keep replies short; don't restate files you just wrote.

## Out of scope (do not build)
Real bureau, OCR, disbursement rails, collections, multi-currency, production deploy, secrets management.

## Where things live
Sprint contracts → `sprint-contracts/`; evaluator reports → `specs/reviews/`; post-mortems → `docs/postmortems/`. `AGENTS.md` is the index. Nested guidance: `src/CLAUDE.md`, `src/{domain,services,repositories,api}/CLAUDE.md`, `frontend/CLAUDE.md`, `tests/CLAUDE.md`.
