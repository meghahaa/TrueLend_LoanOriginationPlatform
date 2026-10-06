# Check Invariants Command

Run financial precision and invariant assertions across the repayment engine and domain models.

```bash
python3 scripts/run_agent.py --task check-invariants
```

## Description
This command runs static code analysis and specialized invariant tests to verify:
1. All monetary fields use `BigDecimal`.
2. EMI schedule total principal equals original loan principal.
3. No float/double primitive leaks exist in financial calculation paths.
