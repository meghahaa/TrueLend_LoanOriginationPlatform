# Environment Post-Mortem & Resolution Log

> **Incident ID**: ENV-INC-2026-0417  
> **Title**: Playwright E2E UI Test Runner Sandbox & MCP Execution Failure  
> **Severity**: Moderate (CI/CD Test Block)  
> **Resolution Category**: Environment-First Configuration Fix

---

## 1. Symptom & Initial Detection
During sprint evaluation, the `evaluator` agent executed Playwright E2E tests for the Underwriting Workbench. The test suite failed with:
```
Error: browserType.launch: Executable doesn't exist at /home/user/.cache/ms-playwright/chromium-1091/chrome-linux/chrome
```
Initial hypothesis was that test code selectors were invalid or front-end service had crashed.

---

## 2. Root Cause Analysis (Environment-First Investigation)
Rather than altering test code or UI components:
1. Inspected Playwright binary cache path in execution environment.
2. Discovered Playwright browser binaries were not pre-downloaded in headless runner container.
3. Node environment lacked environment variable `PLAYWRIGHT_BROWSERS_PATH=0` forcing local relative binary resolution.

---

## 3. Resolution Steps
1. Executed `npx playwright install --with-deps chromium` to populate browser binaries.
2. Updated `.mcp.json` to include `"PLAYWRIGHT_BROWSERS_PATH": "0"` under Playwright MCP environment configuration.
3. Added pre-build setup step in CI pipeline `.gitlab-ci.yml`.

---

## 4. Empirical Verification
Re-ran Playwright test suite:
```
  10 passing (4.2s)
  Snapshots matched: 10/10
```
Resolved completely via environment configuration without modifying production or test source code.
