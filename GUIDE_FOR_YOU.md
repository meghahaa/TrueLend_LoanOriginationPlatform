# GUIDE FOR YOU — do NOT commit this file
Everything below is for you, the supervising engineer. Agents never need it.

---
## 1. What goes in CLAUDE.md vs what is only for you
`CLAUDE.md` is loaded on **every turn**, so each line costs money. Only content that changes how code is written belongs there.

| Brief section | In agent context? | Where it went |
|---|---|---|
| 3.1 Problem | Domain meaning only | `docs/business-case.md` (own words, as required); one-line purpose in root CLAUDE.md |
| 3.2 Your role | **No** — it describes you | Agent-facing equivalent: "agents write all code, humans edit specs/substrate" |
| 3.3 Expected solution / evidence trail | **No** | You. Checklist in §6 |
| 3.4 Rules (no-hand-coding, spec-is-truth, PR-only, synthetic data) | **Yes** | Root CLAUDE.md, rewritten as imperatives |
| 4 Technology stack options | **No** (a choice, not a rule) | Choice made (§2); run/test commands in CLAUDE.md |
| 5.1 AC-01…AC-10 | Only the spec being worked on | `specs/*_spec.md` (Given-When-Then, 61 ids) — **not** CLAUDE.md |
| 5.2 NFR-01…08 | **Yes**, compressed | Root CLAUDE.md "Non-negotiable rules"; full table in `app_spec.md` §5 |
| 6.1/6.2 Functional scope | Via specs | `app_spec.md` §6 API, feature specs, business case |
| 6.3 Out of scope | **Yes**, one line (stops gold-plating) | Root CLAUDE.md |
| 7 Marks, counts (≥3000 lines, ≥20 tests, ≥10 test files…) | **No, deliberately** | Putting numeric targets in agent context invites padding. Quality gates (coverage 80 %, AC traceability, arch tests) enforce what matters; you check the counts in §6 |
| 8 Deliverables list | **No** | §6 checklist |

> Your paste lost the table layout; I inferred NFR numbering as 01 money · 02 append-only schedules/policies · 03 no PII in logs · 04 controller auth + audit · 05 append-only migrations · 06 JSON logs + correlation id · 07 health < 1 s · 08 arch rules as tests. Tell me if your original differs.
> **Your paste also stops mid-sentence at deliverable 9 and omits the "Good-to-Have" items** that separate Merit from Distinction. Paste them and I'll add them — they matter for 85+.

---
## 2. Decisions I made (change before you start if you disagree)
- **Stack:** Python 3.11 + FastAPI + stdlib SQLite; React + Vite + TypeScript; pytest/pytest-cov; import-linter; Vitest; Playwright. *Why:* `Decimal` makes NFR-01 natural; fewest dependencies = least generated code = cheapest; one command (`python -m src`) works on Windows without `make`.
- **Layout:** literal `src/domain|services|repositories|api` so graders searching `src/domain/` find it.
- **Hooks are Node `.js`** to match the harness's own hooks (brief examples show `.sh`; any language is fine).
- **Plugin manifest at repo root** (`plugin.json`, as the brief says). Claude Code's native loader expects `.claude-plugin/plugin.json`; if you want it loadable as a real plugin, copy it there too and run `claude plugin validate .` (if your version has it). I couldn't verify the `skills` key against your CLI version.
- **Both CI files ship and are kept in parity:** `.gitlab-ci.yml` (Virtusa's preferred grader) and `.github/workflows/ci.yml`. Whichever host holds your repo runs its own file; the other is inert. Both skip jobs until `requirements.txt` / `frontend/package-lock.json` exist, so the substrate-only PR (#1) stays green.
- **Claude review is label-gated** (`claude-review` label) so CI never burns credits unprompted. On GitHub it uses the official Claude Code Action. **GitLab has no equivalent action**, so the GitLab job installs the `claude` CLI and runs it headless — my best understanding of the CLI, **not run on a real GitLab runner**. Treat it as needing one trial run.
- **Provided up-front (config/tooling, not production code):** `.importlinter`, `scripts/ac_coverage.py`, five empty `src/**/__init__.py` markers. They exist so `lint-imports` and the AC check pass from day one (import-linter errors if a layer package is missing). If you'd rather stay purist about "agents write everything", delete the five `__init__.py` files and have the S1 agent create them first — nothing else changes.

## 3. Honest limits
- I have **only seen file names** of the harness, not its contents. Check `.claude/settings.json` (how hooks are registered), `.claude/skills/auto|build|evaluate/SKILL.md` and `README.md` before Sprint 1 — your prompts must use the harness's real command names.
- I can't create the **evidence** (PRs, sprint contracts, evaluator reports, red/green history, coverage.xml, snapshots, the post-mortem). It only exists if you run the process. I did not fabricate any; `docs/postmortems/TEMPLATE.md` + `/post-mortem` are for a **real** incident (you will almost certainly hit one on Windows — record it).
- No guarantee of 85+. The pack covers most of the 40-mark "specs" block and the docs; the rest depends on execution and on PR/test counts.
- Tested here: all 3 hooks (incl. Windows paths); the SDK script (dry run + real-package imports); `ac_coverage.py` against the real specs (full/partial coverage, `AC-05` not covering `AC-05a`, strict mode, missing tests dir); `.importlinter` with the real `import-linter` (clean skeleton, valid layered code, and 4 deliberate violations all caught — this found and fixed a bug where valid `api → services → repositories` code was flagged); both CI files parse and have command parity; JSON/YAML validity; spec ID consistency. **Not** tested: anything needing your harness, either CI platform actually running, or the app itself.

---
## 4. Setup (PowerShell, one-time)
1. Prereqs: Python 3.11+, Node 20+, Git, GitHub CLI (`gh auth login`), Claude Code logged in with the API key that holds your $10.
2. New repo `truelend`; first commit contains only a `.gitkeep` (a root commit is unavoidable). Push, then protect `main` (no direct pushes; changes via PR/MR only):
   - **GitHub:** branch protection → require PR. Add secret `ANTHROPIC_API_KEY`. CLI: `gh`.
   - **GitLab:** Settings → Merge requests → **Merge method = Merge commit** (this is what makes merges `--no-ff`; fast-forward/squash would erase the PR history the rubric counts) and enable *Pipelines must succeed*; protect `main` (Maintainers merge, no direct push). Settings → CI/CD → Variables: add masked `ANTHROPIC_API_KEY` (optional `GITLAB_API_TOKEN` to post the review as an MR note). CLI: `glab auth login`.
3. Install the Claude Harness Engine exactly as its README says; keep its `.claude/` content.
4. Copy this pack in **without overwriting the harness's files**:
   - New files copy straight in: everything except `CLAUDE.md`, `README.md`, `.claude/settings.truelend.snippet.json`, `GUIDE_FOR_YOU.md`.
   - Root `CLAUDE.md`: open the harness's original first. If it holds harness operating rules, append the useful ones (short!) under a `## Harness` heading in mine.
   - Open `.claude/settings.json`; merge the `hooks` arrays from the snippet into the existing ones (don't replace).
   - Merge `.mcp.json` if the harness already has one.
5. **Cost guard (do this):** open each harness agent in `.claude/agents/`; if it has no `model:` line, add `model: sonnet` (and `haiku` for `design-critic`/`security-reviewer` if you accept lighter reviews). Un-pinned agents may inherit an expensive model.
6. Branch `chore/substrate` → commit → open PR/MR → merge with a merge commit. That's PR #1. Before pushing, sanity-check locally: `pip install import-linter` then `lint-imports` should say *3 kept, 0 broken*.
7. `claude` → `/model sonnet`. Check `/cost` after every step.

---
## 5. Run order and prompts
Replace command names with the harness's real ones where they differ. Keep sessions short; `/clear` between sprints (CLAUDE.md reloads for free).

**S1 — skeleton + AC-01…05** (≈ $2.5)
> Run the harness scaffold for the stack in CLAUDE.md. Specs already exist — do not regenerate them. Plan Sprint S1 from `specs/app_spec.md` §8 and write the sprint contract to `sprint-contracts/`. Work on branch `feat/s1-intake`. `.importlinter`, `scripts/ac_coverage.py` and the `src/**/__init__.py` markers already exist — extend, do not regenerate. First: pyproject (marker `ac`, coverage 80 %), requirements.txt (must include import-linter, pytest-cov), `src/` skeleton, migration 001, `/health`, JSON logging + correlation id, `python -m src`, and the six `tests/architecture/` tests. Confirm `lint-imports` and `python scripts/ac_coverage.py` run before writing feature code. Then AC-01…AC-05 test-first with separate red/green commits, delegating scoring/decision to `underwriting-agent`. Run `policy-validator-agent` before the PR. Evaluator report → `specs/reviews/`. Open the PR; stop for my merge.

**S2 — AC-06…10 + money** (≈ $2.5)
> Sprint S2 per `app_spec.md` §8 on `feat/s2-lifecycle`. Use `repayment-schedule-agent` for EMI/allocation/DPD/EOD/disbursement and `underwriting-agent` for verification/manual decision/override/audit. Test-first, red/green commits, `/ac-coverage` clean, evaluator report to `specs/reviews/`, PR.

**S3 — UI + Playwright** (≈ $2.5; the full evaluator-with-Playwright-MCP cycle goes here)
> Sprint S3 on `feat/s3-ui`: the six views in `frontend/CLAUDE.md`, responsive, `data-testid`s, Vitest helpers, Playwright desktop+mobile with `toHaveScreenshot` into `tests/e2e/snapshots/`, seed data per `app_spec.md` §7, README quick-start verified from a clean clone. Evaluator uses Playwright MCP; cap retries at 1. PR.

**Finish** (≈ $1–2 reserve): run `python scripts/agent_sdk_runner.py specs/underwriting_spec.md --run --budget 0.25` once (evidence of SDK use); `/post-mortem` for a real incident; add `claude-review` label to one PR (CI Claude Action evidence).

**Budget notes (my estimates, not measured):** Claude Code cost is dominated by repeated context, not output; reading whole specs repeatedly is the main leak. Hard stops: after each step run `/sprint-cost`; if > $3 used in a sprint with ACs left, cut UI polish first, then optional agent runs, never tests/specs. `--max-budget-usd` on `claude -p` runs and the SDK runner's `--budget` enforce caps.

---
## 6. Rubric self-audit (run before submitting)
| Rubric item | Source | Check |
|---|---|---|
| 7.1 specs + AC sections | pack | `ls specs` (7 files) |
| Layered CLAUDE.md + AGENTS.md TOC | pack | 8 CLAUDE.md files (`git ls-files "*CLAUDE.md"`) |
| ≥2 skills / ≥2 commands / ≥1 hook / ≥2 agents | pack (3/4/3/3) | `ls .claude/skills .claude/commands .claude/hooks .claude/agents` |
| Agent SDK in `scripts/` | pack | file exists + one real `--run` |
| `plugin.json` + `.mcp.json` Playwright | pack | present; evaluator actually used it (S3 report) |
| Post-mortem under `docs/` | **you**: real incident | `ls docs/postmortems` shows a dated file |
| 7.2 business-case, ≥4 rule files, frontend, ACs | pack + agents | `ls src/domain` ≥ 4 rule files (spec requires 9) |
| 7.3 arch tests ≥3, import-linter, `docs/tdd.md`, ≥10 test files red→green | pack + agents | `git log --oneline --grep=red`; count `git ls-files "tests/*test*"` |
| 7.4 architecture.md + Mermaid, ≥3000 LOC, snapshots, AC-tagged tests, ≥20 unit tests, coverage artefact | pack + agents | `python scripts/ac_coverage.py`; `coverage.xml` committed; `(git ls-files '*.py','*.ts','*.tsx' \| % { (gc $_).Count } \| measure -sum).Sum` |
| 7.5 CI + Claude Action + ≥3 PR merges, 0 direct commits | pack + you | `.gitlab-ci.yml` / `.github/workflows/ci.yml` green on the last merge; at least one PR/MR labelled `claude-review` with its job log kept; `git log --merges --oneline` ≥ 3 (S0–S3 gives 4); `git log --no-merges --first-parent main` should show only the root commit |
| Layering enforced | pack | `lint-imports` → all contracts kept; `tests/architecture/` repeats them as pytest tests |
| Sprint contracts & reviews committed | harness + you | `ls sprint-contracts specs/reviews` |

Also: `git ls-files | findstr /i "\.env \.db"` must be empty; no real PAN/Aadhaar anywhere.
