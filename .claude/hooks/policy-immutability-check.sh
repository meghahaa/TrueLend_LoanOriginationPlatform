#!/usr/bin/env bash
# Policy Immutability Hook
# Prevents modification of existing approved policy version files.

set -euo pipefail

MODIFIED_POLICIES=$(git status --porcelain | grep -E 'M.*policies/policy-v[0-9]+\.[0-9]+\.json$' || true)

if [ -n "$MODIFIED_POLICIES" ]; then
    echo "[ERROR] Policy Immutability Violation: Existing policy files are append-only and cannot be modified!"
    echo "$MODIFIED_POLICIES"
    echo "To update policies, create a new policy version file (e.g., policy-v1.1.json)."
    exit 1
fi

echo "[HOOK PASS] Policy immutability verified."
exit 0
