# src/api/ — controllers (FastAPI routers)
The only place that knows HTTP and auth.
- Auth: `Authorization: Bearer <demo-token>` → `Actor`. Roles `CUSTOMER`, `UNDERWRITER`, `ADMIN`. Enforce with a `require_role(...)` dependency on **every** route except `/health` and `/products`.
- Customers may only access their own applications (403 otherwise).
- Middleware: assign/propagate `X-Correlation-ID`; one JSON log line per request (method, path, status, ms, correlation_id; never bodies).
- Error mapping: `PolicyViolationException` → 422 `{code, reason_codes, policy_version}`; missing → 404; state conflict → 409; auth → 401/403. No stack traces or PII in bodies.
- Pydantic models live here; money in/out as strings. Controllers call services only — never repositories or domain directly.
- Routes and payloads follow `specs/app_spec.md` §6.
