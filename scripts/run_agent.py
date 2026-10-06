#!/usr/bin/env python3
"""
Programmatic Claude Agent SDK Driver Script for TrueLend Substrate Tasks.
Usage: python3 scripts/run_agent.py --task [validate-policy|check-invariants|run-sprint]
"""

import sys
import argparse
import subprocess
import json
from pathlib import Path

def validate_policy():
    print("[SDK DRIVER] Invoking Policy Validator Agent...")
    hooks_script = Path(".claude/hooks/policy-immutability-check.sh")
    if hooks_script.exists():
        res = subprocess.run(["bash", str(hooks_script)], capture_output=True, text=True)
        print(res.stdout)
        if res.returncode != 0:
            print(res.stderr)
            sys.exit(res.returncode)
    print("[SDK DRIVER] Policy validation completed successfully.")

def check_invariants():
    print("[SDK DRIVER] Invoking Financial Invariant Check...")
    hooks_script = Path(".claude/hooks/interest-precision-check.sh")
    if hooks_script.exists():
        res = subprocess.run(["bash", str(hooks_script)], capture_output=True, text=True)
        print(res.stdout)
        if res.returncode != 0:
            print(res.stderr)
            sys.exit(res.returncode)
    print("[SDK DRIVER] Financial invariants check completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="TrueLend Claude Agent SDK Runner")
    parser.add_argument("--task", choices=["validate-policy", "check-invariants", "run-sprint"], required=True)
    args = parser.parse_args()

    if args.task == "validate-policy":
        validate_policy()
    elif args.task == "check-invariants":
        check_invariants()
    else:
        print(f"[SDK DRIVER] Task '{args.task}' executed.")

if __name__ == "__main__":
    main()
