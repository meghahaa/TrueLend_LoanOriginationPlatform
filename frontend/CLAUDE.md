# frontend/ — React + Vite + TypeScript
Small, plain-CSS UI that exercises the API. Views: Apply, Track, Repay (customer); Underwriter Workbench; Policy Editor; Admin Dashboard.
- Role picker on a login screen selects a demo token (see `specs/app_spec.md` §2). Token kept in memory.
- API client in `src/api.ts`; money handled as strings, formatted for display only (no `parseFloat` arithmetic).
- Responsive: mobile-first CSS, at least one breakpoint (≤ 640 px stacks tables as cards). Playwright covers mobile and desktop viewports.
- Stable `data-testid` on interactive elements; use them in tests.
- Vitest component tests for formatting/validation helpers; Playwright E2E in `tests/e2e/`, snapshots in `tests/e2e/snapshots/`.
- Keep it lean: no UI library, no state library, no animation.
- Playwright config: `frontend/playwright.config.ts` — `testDir: ../tests/e2e`, `snapshotDir: ../tests/e2e/snapshots`, `webServer: { command: "python -m src", cwd: "..", url: "http://localhost:8000/health" }`, projects: desktop + mobile (Pixel 5).
