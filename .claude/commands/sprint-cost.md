---
description: Budget checkpoint — summarise spend, what is done, and what to cut if money is short
allowed-tools: Bash, Read, Grep
---
1. Run `/cost` output as reported by the session (ask the user to paste it if unavailable; do not guess numbers).
2. List ACs done vs remaining by running `python scripts/ac_coverage.py` if present.
3. Recommend, in order: finish current PR → defer UI polish → skip optional agents → shrink remaining sprint scope. Name the minimum set of ACs still required for the rubric.
4. Keep the reply under 12 lines.
