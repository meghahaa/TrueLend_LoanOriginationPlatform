# Agent Catalog & Table of Contents

This document lists all available AI agents operating in the TrueLend Loan Origination & Underwriting System substrate.

## Base Harness Engine Agents

| Agent Name | Location | Description |
|---|---|---|
| **planner** | `.claude/agents/planner.md` | Decomposes specifications into implementation tasks and sprint contracts. |
| **generator** | `.claude/agents/generator.md` | Generates feature code, domain models, services, and controllers adhering to specs. |
| **evaluator** | `.claude/agents/evaluator.md` | Evaluates generated code against acceptance criteria, NFRs, and Playwright UI tests. |
| **security-reviewer** | `.claude/agents/security-reviewer.md` | Audits code for security vulnerabilities, PII leakage, and auth boundary enforcement. |
| **test-engineer** | `.claude/agents/test-engineer.md` | Writes red unit tests, integration tests, and ArchUnit architecture assertions. |
| **design-critic** | `.claude/agents/design-critic.md` | Evaluates UI layout responsiveness, accessibility, and visual structure. |
| **ui-designer** | `.claude/agents/ui-designer.md` | Generates frontend components matching design specifications. |

## Domain & Technical Custom Agents

| Agent Name | Location | Description |
|---|---|---|
| **underwriting-agent** | `.claude/agents/underwriting-agent.md` | Evaluates underwriting policy rules, reason codes, auto-approval thresholds, and override auditing. |
| **repayment-schedule-agent** | `.claude/agents/repayment-schedule-agent.md` | Generates fixed-point EMI amortization schedules, manages repayment postings, and recalculates DPD/NPA buckets. |
| **policy-editor-agent** | `.claude/agents/policy-editor-agent.md` | Manages creation, versioning, threshold configuration, and immutability of loan policy rule sets. |
| **policy-validator-agent** | `.claude/agents/policy-validator-agent.md` | Validates policy schema compliance, interest precision rules, and prevents breaking version migrations. |
