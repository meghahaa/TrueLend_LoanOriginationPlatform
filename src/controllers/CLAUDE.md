# Controllers Layer Guidelines — src/controllers/

## Responsibilities
- REST API endpoint definition.
- HTTP Request/Response DTO mapping and `@Valid` request payload validation.
- Controller-level authentication boundary enforcement and user context extraction (NFR-04).
- Correlation ID propagation via `X-Correlation-ID` header into MDC logging context (NFR-06).

## Invariants & Rules
- Controllers MUST NOT contain business logic or financial calculations.
- Underwriter and admin endpoints (e.g. override, document verification) MUST audit `userId`, `timestamp`, and `action` to audit log.
- Standard HTTP status response codes: `200 OK`, `201 Created`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.
