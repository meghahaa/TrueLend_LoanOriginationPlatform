# Source Code Guidelines — src/

## Architecture Rules
- Backend source code resides under `src/main/java` (or python/node equivalent).
- Must adhere strictly to 3-tier layering: `controllers` -> `services` -> `domain` & `repositories`.
- Forbidden: Domain models importing controllers or UI components.
- Forbidden: Controllers performing direct business calculation or database SQL execution.

## Coding Standards
- All money calculations MUST use `BigDecimal` with explicit scale (2) and rounding (`HALF_UP`).
- No floating-point `double` or `float` for currency.
- All public service and controller methods MUST log entry and exit with structured correlation IDs.
- Handle exceptions via custom domain exceptions (e.g. `PolicyViolationException`, `ApplicationNotFoundException`).
