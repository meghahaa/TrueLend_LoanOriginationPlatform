# src/repositories/ — persistence
SQLite via stdlib `sqlite3`; parameterised SQL only. Return domain objects, not rows.
- Money columns are TEXT holding `Decimal` strings; convert at the boundary.
- `repayment_schedule` rows and policy files are **insert-only** — no `UPDATE`/`DELETE` statements exist for them. Payment state lives in `repayment_allocations` (insert-only), never on schedule rows.
- Policy repository reads `policies/loan_policy.vNNN.json`; active = highest version; writing = create a new file, never overwrite.
- Migrations are numbered SQL files; never edit an applied one — add a new one.
- No business rules here; no imports from `services` or `api`.
