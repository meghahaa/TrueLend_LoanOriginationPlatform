---
description: Write an environment-first post-mortem for a real failure that just occurred
argument-hint: "<short title of the incident>"
allowed-tools: Bash, Read, Write, Grep
---
Incident: $ARGUMENTS
1. Use only facts from this session (commands, errors, fixes). Do not invent details.
2. Gather environment evidence now: `python --version`, `node --version`, `pip list | head -30`, working directory, git branch, relevant ports/processes.
3. Copy `docs/postmortems/TEMPLATE.md` to `docs/postmortems/<YYYY-MM-DD>-<slug>.md` and complete every section; tick the environment checklist items that were actually checked *before* code was changed.
4. In *Prevention*, name the concrete guardrail added or proposed (CLAUDE.md line, hook, test, CI step).
5. Redact any identifiers. Commit on the current feature branch.
