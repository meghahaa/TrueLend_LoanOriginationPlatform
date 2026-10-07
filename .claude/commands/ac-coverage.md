---
description: Check that every AC/NFR id in specs/ has at least one tagged test and report gaps
allowed-tools: Bash, Read, Grep, Glob
---
1. `scripts/ac_coverage.py` ships with the repo (stdlib only). Do not rewrite it; if it is missing, restore it from git history and tell the user.
2. Run `python scripts/ac_coverage.py`.
3. Report: `covered/total`, the missing ids grouped by spec, and for each missing id the spec line it comes from. Do not write tests unless `$ARGUMENTS` contains `fix`; if it does, use the `spec-to-test-generator` skill for the missing ids only.
