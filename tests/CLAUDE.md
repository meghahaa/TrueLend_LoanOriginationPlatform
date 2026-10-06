# Testing Guidelines & Discipline — tests/

## TDD Rules & Principles
- **Test-Driven Development (TDD) Mandatory**: Red -> Green -> Refactor. Tests MUST be written and fail before production implementation code is generated.
- **AC Tagging**: Every test verifying a functional acceptance criteria MUST be tagged with `@TestTag("AC-NN")` or `@AC("AC-NN")`.
- **100% Coverage Goal**: Minimum ratchet threshold is 80%. Every line of business logic must be double-checked by unit/integration tests.
- **No Test Modifications to Pass**: Never modify or weaken test assertions to make broken implementation code pass. Fix the implementation under test.

## Test Directory Structure
- `tests/unit/`: Fast unit tests for domain entities, policy evaluators, and math calculators.
- `tests/integration/`: Spring Boot / REST API integration tests.
- `tests/architecture/`: ArchUnit / structural tests enforcing layering rules and immutable policy constraints (NFR-08).
- `tests/e2e/`: Playwright UI automated tests.
