#!/usr/bin/env python3
"""Programmatic Claude Agent SDK usage for TrueLend: a read-only spec-conformance audit.

Asks a headless Claude agent to compare the Acceptance Criteria in a spec against the tests
and source, and report gaps. Read-only tools, hard turn and USD caps.

  python scripts/agent_sdk_runner.py specs/repayment_spec.md            # dry run: prints plan, no API call
  python scripts/agent_sdk_runner.py specs/repayment_spec.md --run      # real call (needs ANTHROPIC_API_KEY)
  python scripts/agent_sdk_runner.py specs/repayment_spec.md --run --budget 0.25 --max-turns 8

Requires: pip install claude-agent-sdk   (only for --run)
"""
import argparse
import asyncio
import pathlib
import re
import sys

SYSTEM = (
    "You are a read-only spec auditor for the TrueLend project. Never edit files. "
    "Compare Acceptance Criteria ids in the given spec with tests (grep for the ids under tests/) "
    "and the implementation under src/. Report only: (1) ids with no test, (2) ids whose test "
    "does not assert what the spec states, (3) code that contradicts the spec. Cite file:line. "
    "Be concise (max 25 lines). The spec is the source of truth."
)


def spec_ids(spec: pathlib.Path) -> list[str]:
    return sorted(set(re.findall(r"\b(?:AC|NFR)-\d{2}[a-z]?\b", spec.read_text(encoding="utf-8"))))


async def run_audit(spec: pathlib.Path, budget: float, max_turns: int) -> int:
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM,
        allowed_tools=["Read", "Grep", "Glob"],  # read-only by construction
        permission_mode="default",
        max_turns=max_turns,
        max_budget_usd=budget,
        cwd=str(pathlib.Path(__file__).resolve().parent.parent),
    )
    prompt = f"Audit {spec} (ids: {', '.join(spec_ids(spec))}). Follow your instructions."
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            cost = getattr(message, "total_cost_usd", None)
            print(f"\n[audit done] turns={message.num_turns} cost_usd={cost}", file=sys.stderr)
            return 1 if message.is_error else 0
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=pathlib.Path)
    ap.add_argument("--run", action="store_true", help="actually call the API (default: dry run)")
    ap.add_argument("--budget", type=float, default=0.30, help="hard USD cap for this run")
    ap.add_argument("--max-turns", type=int, default=8)
    args = ap.parse_args()
    if not args.spec.exists():
        print(f"spec not found: {args.spec}", file=sys.stderr)
        return 2
    ids = spec_ids(args.spec)
    print(f"spec={args.spec} ids={len(ids)} budget=${args.budget:.2f} max_turns={args.max_turns}")
    if not args.run:
        print("dry run — no API call. ids:", ", ".join(ids))
        return 0
    return asyncio.run(run_audit(args.spec, args.budget, args.max_turns))


if __name__ == "__main__":
    sys.exit(main())
