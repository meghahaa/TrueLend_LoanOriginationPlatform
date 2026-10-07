# tests/
- `tests/unit/` rules + services (≥ 20 tests, ≥ 10 files overall across the repo); `tests/api/` TestClient integration; `tests/architecture/` structural; `tests/e2e/` Playwright.
- Register marker `ac(id)` in `pyproject.toml`; every test carries `@pytest.mark.ac("AC-NN")` or `("NFR-NN")` and name `test_ac05_…`. Every id in `specs/` must be referenced by ≥ 1 test (`python scripts/ac_coverage.py`).
- Use a fixed `FakeClock` and in-memory SQLite; no network, no sleeps.
- Test data: obviously synthetic (`PAN TESTP1234X`, Aadhaar `9999 0000 0001`).
- `tests/architecture/` must contain at least: (1) layer imports respected, (2) domain has no framework/IO imports, (3) no `float` in money modules (AST scan), (4) policy files/migrations immutable (hash check vs git-tracked baseline), (5) EMI invariant property over a grid of principal/rate/tenure, (6) no PAN/Aadhaar in log output.
- Coverage: `coverage.xml` committed from the last green run; threshold 80 %.
- Playwright: desktop + mobile viewport; `toHaveScreenshot` into `tests/e2e/snapshots/`.
