# src/ — backend module
Python package `src`. Entry: `src/__main__.py` (`python -m src`), app factory `src/main.py`.
- Layers: `api/` → `services/` → `repositories/` → `domain/`. Never import upward or skip `services` from `api`.
- Config via env with safe defaults (`TRUELEND_DB`, `TRUELEND_POLICY_DIR`, port 8000). No secrets.
- Wiring (dependency injection) happens only in `src/main.py`.
- Migrations: `migrations/NNN_name.sql`, append-only, applied in order at startup, tracked in `schema_migrations`.
- Startup: apply migrations → seed if empty (`src/seed.py`, synthetic data per `specs/app_spec.md` §7) → serve.
- Pin dependencies in `requirements.txt` (fastapi, uvicorn, pydantic, pytest, pytest-cov, httpx, import-linter).
