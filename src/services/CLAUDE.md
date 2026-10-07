# src/services/ — use cases
Orchestrate domain rules + repositories. One service per feature: `ProductCatalogService`, `ApplicationService`, `UnderwritingService`, `RepaymentService`, `DisbursementService`, `PortfolioService`, `PolicyService`.
- Take `Actor` and plain DTOs; never import FastAPI or `Request`.
- One transaction per use case: the whole operation succeeds or none of it does.
- Emit an audit record for every underwriter/admin action (`user_id`, UTC time from `Clock`, action, application id, reason code, comment).
- Always stamp decisions with the active `policy_version`.
- Log with `logging.getLogger(__name__)`; log ids and codes only, never PAN/Aadhaar/document content.
