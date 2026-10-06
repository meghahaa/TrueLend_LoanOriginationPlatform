# TrueLend — Loan Origination & Underwriting System

> **Business Case ID**: BC-AINE-003  
> **Domain**: Banking — Lending  
> **Engineering Substrate**: AI-Native Engineering Capstone with Claude Harness Engine Plugin & TrueLend Substrate Plugin

---

## Overview

TrueLend is a configurable, policy-driven loan origination and underwriting system for Horizon Bank. The platform manages the full application-to-disbursement-to-repayment lifecycle while enforcing business rules via external, versioned policy configurations without requiring application code changes.

### Key Capabilities
- **Product Catalog Management**: Dynamic configuration for Personal, Vehicle, and Education loan products (AC-01).
- **Application Intake & Checklist**: Document requirements and deterministic credit scoring based on customer financial profiles (AC-02, AC-03, AC-05).
- **Underwriting Workbench**: Automated decision engine (`AUTO_APPROVE`, `AUTO_REJECT`, `MANUAL_REVIEW`) with reason codes, document queue, and admin overrides with audit trail (AC-04, AC-06, AC-10).
- **Repayment & Disbursement Engine**: Amortization schedule calculation using fixed-point EMI formulas, disbursement recording, repayment posting, and DPD/NPA bucket recalculations (AC-07, AC-08, AC-09).
- **Architectural & Security Guardrails**: Non-floating point monetary precision, append-only policies/schedules, PII masking, and automated ArchUnit tests (NFR-01 through NFR-08).

---

## Quick Start

### Prerequisites
- JDK 17+ (or Node.js 18+ / Python 3.11+ depending on backend target)
- Node.js & npm (for frontend and Playwright UI tests)
- Claude Code CLI configured with Playwright MCP

### Single Command Execution
```bash
# Clone the repository
git clone https://gitlab.virtusa.com/truelend/TrueLend_LoanOriginationPlatform.git
cd TrueLend_LoanOriginationPlatform

# Launch backend application with seed data (3 products + sample applications)
./mvnw spring-boot:run

# Launch frontend application (in separate terminal or concurrent runner)
npm start --prefix frontend
```

### Running Test Suite
```bash
# Execute unit tests & AC-tagged tests
./mvnw test

# Execute architecture structural tests
./mvnw test -Dtest=*ArchitectureTest

# Execute Playwright E2E UI tests
npx playwright test
```

---

## Substrate & Agent Architecture

The project extends the **Claude Harness Engine** with domain-specific substrate components:

- **Agents (`.claude/agents/`)**: `underwriting-agent`, `repayment-schedule-agent`, `policy-editor-agent`, `policy-validator-agent`
- **Skills (`.claude/skills/`)**: `loan-policy-evaluator`, `repayment-schedule-builder`, `policy-migration-validator`, `archtest-author`
- **Hooks (`.claude/hooks/`)**: `policy-immutability-check.sh`, `interest-precision-check.sh`, `repayment-invariant-check.sh`
- **Commands (`.claude/commands/`)**: `validate-policy`, `check-invariants`

---

## Specification Index

- [`specs/app_spec.md`](specs/app_spec.md): Master Application Specification
- [`specs/product-catalog_spec.md`](specs/product-catalog_spec.md): Product Catalog & Policy Configuration Spec (AC-01)
- [`specs/application-intake_spec.md`](specs/application-intake_spec.md): Application Intake & Credit Scoring Spec (AC-02, AC-03, AC-05)
- [`specs/underwriting_spec.md`](specs/underwriting_spec.md): Underwriting Engine & Verification Spec (AC-04, AC-06, AC-10)
- [`specs/repayment_spec.md`](specs/repayment_spec.md): Repayment Schedule & NPA Bucketing Spec (AC-07, AC-09)
- [`specs/disbursement_spec.md`](specs/disbursement_spec.md): Disbursement Recording Spec (AC-08)

---

## Documentation Index

- [`docs/business-case.md`](docs/business-case.md): Business Case & Domain Rules Reference
- [`docs/architecture.md`](docs/architecture.md): Architecture & Sequence Diagrams
- [`docs/tdd.md`](docs/tdd.md): Red-Green-Refactor TDD Discipline & Evidence
- [`docs/knowledge-deposits.md`](docs/knowledge-deposits.md): Recurring Mistakes & Substrate Rules Deposit Log
- [`docs/post-mortem-environment-resolution.md`](docs/post-mortem-environment-resolution.md): Environment-first Debugging Log
- [`docs/fix-loops/emi-rounding-fix.md`](docs/fix-loops/emi-rounding-fix.md): Autonomous Fix Loop Trace Evidence
