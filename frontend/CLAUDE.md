# Frontend Guidelines — frontend/

## Responsibilities
- User interfaces for Customer Application Intake, Underwriter Workbench, and Admin Portfolio Dashboard.
- Responsive CSS/HTML layout supporting desktop and mobile viewports.
- Form validation and integration with backend REST API endpoints.

## Playwright & UI Validation
- Every major page view must be covered by a Playwright E2E test.
- Visual component snapshots stored under `frontend/tests/snapshots/`.
- Key views:
  1. Product catalog list & document upload form.
  2. Underwriter document verification queue and decision modal.
  3. Admin override screen with audit comment entry.
  4. Repayment schedule viewer and payment posting simulator.
