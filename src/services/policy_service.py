"""
PolicyService — use case for reading and publishing policy versions.
No FastAPI imports; receives repo by injection.
"""
from __future__ import annotations

import copy
import json
import logging
from typing import List

from src.domain.policy_validator import validate_policy_document, PolicyValidationError
from src.repositories.policy_repository import PolicyRepository

_log = logging.getLogger(__name__)


class PolicyService:
    def __init__(self, policy_repo: PolicyRepository) -> None:
        self._repo = policy_repo

    def list_versions(self) -> List[dict]:
        return self._repo.list_versions()

    def publish_new_version(self, partial_update: dict, change_note: str, created_by: str) -> int:
        """
        Merge partial_update onto the active policy, validate, and write a new version file.
        Returns the new version number.
        Raises PolicyValidationError (→ 422) if invalid.
        Raises FileExistsError (→ 409) on concurrent publish.
        """
        active = self._repo.get_active_policy()
        new_version = active.version + 1

        # Build a raw dict from the active policy to merge into
        # Re-read the raw file to preserve exact structure
        import glob, os
        files = sorted(
            glob.glob(os.path.join(self._repo._dir, "loan_policy.v*.json")),
            key=lambda f: int(os.path.basename(f)[len("loan_policy.v"):-len(".json")]),
        )
        with open(files[-1], encoding="utf-8") as fh:
            base = json.load(fh)

        # Deep merge: only product thresholds + top-level fields
        merged = copy.deepcopy(base)
        merged["version"] = new_version
        merged["change_note"] = change_note
        merged["created_by"] = created_by

        # Merge product overrides
        if "products" in partial_update:
            for code, overrides in partial_update["products"].items():
                if code in merged["products"]:
                    merged["products"][code].update(overrides)
                else:
                    merged["products"][code] = overrides

        # Validate before writing
        validate_policy_document(merged)

        # Write (insert-only)
        path = self._repo.write_new_version(merged, new_version)
        _log.info("New policy version %d written: %s by %s", new_version, path, created_by)
        return new_version
