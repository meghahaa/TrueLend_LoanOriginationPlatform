# Feature Spec — Product Catalog & Policy Versioning
Covers AC-01 and the policy editor. Source: `policies/loan_policy.vNNN.json` (seed: v001). Parent: `app_spec.md`.

## Behaviour
- The catalog lists every product in the active policy with display name, rate, amount/tenure/age ranges, minimum income and required documents. Nothing product-specific is hard-coded; adding a product to a new policy file makes it appear.
- **Policy document** shape = `policies/loan_policy.v001.json` (money as strings). Validated by `src/domain/policy_validator.py`: min < max for age/amount/tenure; `reject_score < approve_score`; 300 ≤ scores ≤ 900; rate > 0; `max_foir` in (0, 1]; non-empty `required_documents`; `bucket_thresholds` strictly increasing; money fields parse as non-negative `Decimal`.
- **Policy editor** (`POST /admin/policies`, ADMIN): body = full or partial product thresholds + `change_note`. Service merges onto the active policy, validates, and writes `loan_policy.v{N+1}.json` (never touches existing files). Returns the new version. Invalid → 422 with validator messages; nothing written.
- Existing applications keep the `policy_version` they were decided under.
- `GET /admin/policies` lists versions (version, effective_from, created_by, change_note).

## Acceptance Criteria
- **AC-01** Given the active policy contains PERSONAL, VEHICLE and EDUCATION, when `GET /products` is called, then three products return, each with its own thresholds and required documents, and the response includes the `policy_version`.
- **AC-01a** Given a new policy file `v002` adds a fourth product and no code changes, when the catalog is loaded, then four products return (config-driven).
- **AC-01b** Given policies v001 and v002 exist, when the active policy is resolved, then v002 is returned.
- **AC-01c** Given an admin submits valid edited thresholds, when `POST /admin/policies` is called, then `loan_policy.v002.json` exists, v001 is byte-identical to before, and the response contains version 2.
- **AC-01d** Given edited thresholds that violate validation (e.g. min_age ≥ max_age), when submitted, then 422 and no file is created.
- **AC-01e** Given a customer token, when `POST /admin/policies` is called, then 403.
- **NFR-02 / NFR-05** A test attempts to overwrite an existing policy file via the repository and must fail; baseline hashes of `policies/loan_policy.v001.json` and `migrations/*` are asserted.

## Edge cases
Gaps in version numbers → still pick the highest; malformed JSON → startup fails with a clear message (no PII); concurrent publish → second writer fails (file exists), returns 409.
