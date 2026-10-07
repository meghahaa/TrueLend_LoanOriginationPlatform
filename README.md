# TrueLend — Configurable Loan Origination Platform

Policy-driven loan origination: **apply → underwrite → disburse → repay**. Business users change thresholds by publishing a new versioned policy file; no code change. Built end-to-end by Claude Code agents under spec supervision (see *AI-native workflow*).

## Quick start
Prerequisites: Python 3.11+, Node 20+ (all data is synthetic).
```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src                                        # migrates, seeds, builds UI if needed, serves on :8000
```
Open http://localhost:8000. Health: `GET /health`. Demo logins on the sign-in screen (tokens in `specs/app_spec.md` §2): customer, underwriter, admin.

## Seed data
3 products (Personal, Vehicle, Education) from `policies/loan_policy.v001.json` and 6 sample applications covering auto-approve, auto-reject, manual review, approved, and loans in `CURRENT`, `DPD-60` and `NPA` buckets.

## Tests
```bash
pytest --cov=src --cov-report=xml --cov-fail-under=80   # unit + API + architecture tests, writes coverage.xml
lint-imports                                             # layering contracts
python scripts/ac_coverage.py                            # every AC/NFR id in specs has a test (add --strict to flag typo'd ids)
cd frontend && npm test && npx playwright test           # UI unit + E2E (snapshots in tests/e2e/snapshots)
```

## Architecture
Layered: `src/api` → `src/services` → `src/repositories` → `src/domain`; React frontend in `frontend/`. Diagrams and rules: `docs/architecture.md`.

## Policy versions
`policies/loan_policy.vNNN.json` are append-only. Admin → Policy Editor (or `POST /admin/policies`) writes the next version; existing applications keep the version that decided them.

## AI-native workflow
| Artifact | Location |
|---|---|
| Specs (source of truth) | `specs/` |
| Business case | `docs/business-case.md` |
| Agent guidance | `CLAUDE.md` (root + `src/`, layers, `frontend/`, `tests/`), `AGENTS.md` |
| Project agents / skills / commands / hooks | `.claude/` |
| Sprint contracts / evaluator reviews | `sprint-contracts/`, `specs/reviews/` |
| TDD and post-mortems | `docs/tdd.md`, `docs/postmortems/` |
| Programmatic SDK use | `scripts/agent_sdk_runner.py` |
| Plugin manifest / MCP | `plugin.json`, `.mcp.json` (Playwright) |

Rules: agents write all production code, tests and migrations; the spec wins over code; changes merge only through pull requests (`--no-ff`); synthetic data only.
