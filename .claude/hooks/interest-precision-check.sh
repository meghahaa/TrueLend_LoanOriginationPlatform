#!/usr/bin/env bash
# Interest Precision Hook (NFR-01)
# Scans Java/Python files for double or float declarations in monetary logic.

set -euo pipefail

FLOAT_LEAKS=$(grep -rnE '(double|float)\s+(amount|principal|interest|emi|balance|income|rate)' src/ 2>/dev/null || true)

if [ -n "$FLOAT_LEAKS" ]; then
    echo "[ERROR] NFR-01 Fixed-Point Precision Violation: Monetary fields must use BigDecimal / Decimal!"
    echo "$FLOAT_LEAKS"
    exit 1
fi

echo "[HOOK PASS] Interest precision check passed (no float/double primitive leaks)."
exit 0
