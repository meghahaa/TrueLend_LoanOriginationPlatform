# TDD Discipline
Every behaviour starts as a failing test that names its AC. Agents follow this; the reviewer rejects PRs that don't.

## Cycle and commit protocol
1. **Red** — write the test from the spec AC; run it; confirm it fails for the right reason. Commit: `test(AC-05): red — income below minimum raises PolicyViolationException`.
2. **Green** — smallest implementation to pass. Commit: `feat(AC-05): green — policy gate rejects low income`.
3. **Refactor** — tidy with tests green. Commit: `refactor(AC-05): extract bounds check`.
Red and green are separate commits so `git log` shows the pattern.

## Rules
- Test names `test_ac05_<behaviour>` + `@pytest.mark.ac("AC-05")`; Vitest/Playwright titles start with the AC id.
- Cover both sides of each boundary (e.g. income 24999.99 / 25000.00; DPD 29/30/59/60/89/90/179/180).
- Use `FakeClock`, in-memory SQLite, synthetic data; no sleeps or network.
- Never delete or loosen a failing test; fix the code or raise a spec question.
- Property/grid tests for the EMI invariant (NFR-08).
- Coverage ≥ 80 % (`--cov-fail-under=80`); `coverage.xml` committed.
- `python scripts/ac_coverage.py` must report zero uncovered ids before a PR.

## Evidence
`git log --oneline --grep="red" ` and `--grep="green"` show the pairs; PR descriptions list the AC ids covered.
