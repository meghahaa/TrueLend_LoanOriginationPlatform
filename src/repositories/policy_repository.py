"""
Policy repository — reads versioned policy JSON files from disk.
Active policy = highest version found in policy_dir.
Insert-only: writing always creates a new file, never overwrites.
No business rules here.
"""
from __future__ import annotations

import glob
import json
import os
from decimal import Decimal
from typing import List, Optional

from src.domain.models import LoanPolicy, ProductPolicy
from src.domain.money import to_money


class PolicyRepository:
    """Reads and writes policy files in `policy_dir`."""

    def __init__(self, policy_dir: str = "policies") -> None:
        self._dir = policy_dir

    # ------------------------------------------------------------------ #
    # Reading                                                              #
    # ------------------------------------------------------------------ #

    def get_active_policy(self) -> LoanPolicy:
        """Return the policy with the highest version number."""
        files = self._list_policy_files()
        if not files:
            raise FileNotFoundError(
                f"No policy files found in '{self._dir}'. "
                "Expected at least loan_policy.v001.json"
            )
        # Sort by version number (pick highest, ignoring gaps — per spec edge cases)
        files.sort(key=lambda f: self._version_from_path(f))
        return self._load(files[-1])

    def list_versions(self) -> List[dict]:
        """Return metadata for all versions (sorted ascending)."""
        files = sorted(
            self._list_policy_files(),
            key=lambda f: self._version_from_path(f),
        )
        result = []
        for path in files:
            policy = self._load(path)
            result.append(
                {
                    "version": policy.version,
                    "effective_from": policy.effective_from,
                    "created_by": policy.created_by,
                    "change_note": policy.change_note,
                }
            )
        return result

    # ------------------------------------------------------------------ #
    # Writing (insert-only — never touches existing files)                #
    # ------------------------------------------------------------------ #

    def write_new_version(self, data: dict, new_version: int) -> str:
        """Write loan_policy.vNNN.json; raise FileExistsError if it exists."""
        filename = f"loan_policy.v{new_version:03d}.json"
        path = os.path.join(self._dir, filename)
        if os.path.exists(path):
            raise FileExistsError(
                f"Policy file already exists: {path} (concurrent publish?)"
            )
        with open(path, "x", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return path

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _list_policy_files(self) -> List[str]:
        pattern = os.path.join(self._dir, "loan_policy.v*.json")
        return glob.glob(pattern)

    @staticmethod
    def _version_from_path(path: str) -> int:
        """Extract numeric version from e.g. policies/loan_policy.v002.json → 2."""
        basename = os.path.basename(path)  # loan_policy.v002.json
        # Strip prefix and suffix
        inner = basename[len("loan_policy.v") : -len(".json")]
        return int(inner)

    @staticmethod
    def _load(path: str) -> LoanPolicy:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)

        products = {}
        for code, p in raw["products"].items():
            products[code] = ProductPolicy(
                product_code=code,
                display_name=p["display_name"],
                min_monthly_income=to_money(p["min_monthly_income"]),
                min_age=int(p["min_age"]),
                max_age=int(p["max_age"]),
                min_amount=to_money(p["min_amount"]),
                max_amount=to_money(p["max_amount"]),
                min_tenure_months=int(p["min_tenure_months"]),
                max_tenure_months=int(p["max_tenure_months"]),
                annual_rate_percent=to_money(p["annual_rate_percent"]),
                approve_score=int(p["approve_score"]),
                reject_score=int(p["reject_score"]),
                max_foir=to_money(p["max_foir"]),
                required_documents=list(p["required_documents"]),
            )

        return LoanPolicy(
            version=int(raw["version"]),
            effective_from=raw["effective_from"],
            created_by=raw["created_by"],
            change_note=raw["change_note"],
            products=products,
            bucket_thresholds=dict(raw.get("bucket_thresholds", {})),
        )
