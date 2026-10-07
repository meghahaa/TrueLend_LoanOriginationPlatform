---
name: spec-to-test-generator
description: Use to turn Acceptance Criteria in specs/*.md into AC-tagged failing tests (pytest or Vitest/Playwright) and to find ACs without tests. Keeps the AC-to-test traceability the project is graded on.
---
# Spec → test generator

## Steps
1. Read only the target spec's *Acceptance Criteria* section (ids like `AC-05a`, `NFR-02`).
2. For each id write one test: Given → fixtures/arrange, When → act, Then → assert. Name `test_ac05a_<behaviour>`; add `@pytest.mark.ac("AC-05a")`. Frontend: title starts `AC-05a`.
3. Prefer parametrised tests for boundary tables. Use `FakeClock`, in-memory SQLite, synthetic data.
4. Run the new tests and confirm they **fail for the expected reason** (red) before any implementation. Commit as `test(AC-05a): red …`.
5. After implementation run `python scripts/ac_coverage.py`; it must list no missing ids.

## Template
```python
@pytest.mark.ac("AC-05")
def test_ac05_income_below_minimum_raises_policy_violation(policy_v1):
    with pytest.raises(PolicyViolationException) as exc:
        check_eligibility(policy_v1.products["PERSONAL"], income=Decimal("24999.99"), age=30, amount=Decimal("100000"), tenure=24)
    assert "INCOME_BELOW_MIN" in exc.value.reason_codes
```

## Rules
One AC → at least one test; never assert on implementation details the spec doesn't state; never edit the spec to match a test.
