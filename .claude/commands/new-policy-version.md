---
description: Publish a new append-only policy version from a described threshold change, then validate it
argument-hint: "<change description, e.g. 'PERSONAL approve_score 720 -> 700'>"
allowed-tools: Bash, Read, Write, Grep, Glob, Task
---
Change requested: $ARGUMENTS
1. Find the highest `policies/loan_policy.vNNN.json`. Never edit it.
2. Copy it to `loan_policy.v{N+1}.json`, apply only the requested change, bump `version`, set `effective_from` to today, `created_by` to `claude-agent`, and write a precise `change_note`.
3. Invoke the `policy-validator-agent` on the diff. If it reports FAIL, fix only the new file.
4. Run `pytest -m ac -k "policy or catalog" -q`.
5. Summarise: old → new values, validator result, test result. Commit on a feature branch (`feat/policy-v{N+1}`), never on `main`.
