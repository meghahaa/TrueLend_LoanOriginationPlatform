#!/usr/bin/env python3
"""AC/NFR traceability scanner for TrueLend (stdlib only).

Every id like AC-05, AC-05a or NFR-03 mentioned in specs/*_spec.md must appear in at least one test.
Recognised in tests: "AC-05a" (markers, titles, strings) and "test_ac05a_..." (function names).

  python scripts/ac_coverage.py            # exit 0 = all covered, 1 = gaps, 2 = setup problem
  python scripts/ac_coverage.py --strict   # also fail on test ids that no spec defines (typos)
  python scripts/ac_coverage.py --json     # machine-readable output
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_ID = re.compile(r"\b(?:AC|NFR)-\d{2}[a-z]?\b")
TEST_ID = re.compile(r"(?<![A-Za-z0-9])(AC|NFR|ac|nfr)[-_]?(\d{2})([a-z]?)(?![A-Za-z0-9])")
TEST_EXT = {".py", ".ts", ".tsx", ".js", ".jsx"}
SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "venv", "snapshots", "dist", ".git", ".pytest_cache"}
FRONTEND_TEST = re.compile(r"\.(test|spec)\.[jt]sx?$")


def spec_ids(spec_dir: Path) -> dict[str, list[str]]:
    found: dict[str, set[str]] = defaultdict(set)
    for f in sorted(spec_dir.glob("*_spec.md")):  # top level only: skips specs/reviews/
        for i in SPEC_ID.findall(f.read_text(encoding="utf-8")):
            found[i].add(f.name)
    return {k: sorted(v) for k, v in found.items()}


def iter_test_files(root: Path):
    # tests/: every source file. frontend/src: only *.test.* / *.spec.* files.
    for base, only_tests in ((root / "tests", False), (root / "frontend" / "src", True)):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in TEST_EXT or SKIP_DIRS & set(p.parts):
                continue
            if only_tests and not FRONTEND_TEST.search(p.name):
                continue
            yield p


def test_ids(root: Path) -> dict[str, list[str]]:
    found: dict[str, set[str]] = defaultdict(set)
    for p in iter_test_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for prefix, num, suffix in TEST_ID.findall(text):
            found[f"{prefix.upper()}-{num}{suffix}"].add(str(p.relative_to(root)).replace("\\", "/"))
    return {k: sorted(v) for k, v in found.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--strict", action="store_true", help="fail on test ids not defined in any spec")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    spec_dir = args.root / "specs"
    specs = spec_ids(spec_dir) if spec_dir.exists() else {}
    if not specs:
        print(f"ERROR: no AC/NFR ids found in {spec_dir}/*_spec.md", file=sys.stderr)
        return 2
    tests = test_ids(args.root)

    missing = sorted(i for i in specs if i not in tests)
    unknown = sorted(i for i in tests if i not in specs)
    covered = len(specs) - len(missing)

    if args.json:
        print(json.dumps({"total": len(specs), "covered": covered, "missing": missing, "unknown_in_tests": unknown}, indent=2))
    else:
        print(f"AC traceability: {covered}/{len(specs)} ids covered by tests")
        by_spec: dict[str, list[str]] = defaultdict(list)
        for i in missing:
            for s in specs[i]:
                by_spec[s].append(i)
        for s in sorted(by_spec):
            print(f"  {s}: missing {', '.join(by_spec[s])}")
        if unknown:
            print(f"  WARNING ids in tests but in no spec (typo?): {', '.join(unknown)}")
        if not missing:
            print("  all spec ids have at least one test")

    if missing or (args.strict and unknown):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
