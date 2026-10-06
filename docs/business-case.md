# Business Case: TrueLend Loan Origination & Underwriting System

> **Business Case ID**: BC-AINE-003  
> **Domain**: Banking — Lending  
> **Target Audience**: Reviewer Plugin, Underwriting Operations, Product Managers

---

## 1. Executive Summary & Problem Statement
Horizon Bank currently faces high time-to-market and developer dependency when launching or adjusting consumer loan products. Modifying credit score cutoffs, income floors, interest rate structures, or document requirements historically required hardcoded backend changes, manual deployment cycles, and extensive regression testing.

**TrueLend** solves this by delivering an AI-native, policy-driven loan origination and underwriting system. Policy definitions (minimum income, credit score thresholds, interest rate bands, document checklists) are externalized into immutable, versioned policy documents. The platform processes loan applications end-to-end—from customer intake and credit scoring to automated underwriting, admin overrides, disbursement, EMI repayment scheduling, and DPD delinquency bucketing—without requiring source code alterations when underwriting policies evolve.

---

## 2. Target Users & Stakeholders
1. **Borrower / Customer**: Applies for loans, uploads required documents, tracks application decisions, views amortization schedules, and posts repayments.
2. **Underwriter**: Reviews flagged applications (`MANUAL_REVIEW`), inspects uploaded documents in the verification queue, marks documents `VERIFIED` or `REJECTED`, and approves/rejects applications.
3. **Credit Risk Admin**: Edits and versions loan underwriting policies, manages product parameters, and performs audited overrides on `AUTO_REJECT` decisions.
4. **Operations & Finance Manager**: Tracks portfolio health, delinquency buckets (`CURRENT`, `DPD-30`, `DPD-60`, `DPD-90`, `NPA`), and disbursement records.

---

## 3. Key Business Rules & Domain Concepts
- **Product Catalog Configuration (AC-01)**: Products (`PERSONAL_LOAN`, `VEHICLE_LOAN`, `EDUCATION_LOAN`) source their parameters directly from versioned JSON policy definitions.
- **Dynamic Document Checklist (AC-02)**: Requirements automatically vary by product type (e.g. vehicle quotation required for vehicle loan, admission letter for education loan).
- **Deterministic Credit Scoring (AC-03)**: Calculated reproducibly using applicant age, income, and credit flags without external black-box dependency in the core engine.
- **Automated Policy Decisioning (AC-04 & AC-05)**: Standardized decision paths (`AUTO_APPROVE`, `AUTO_REJECT`, `MANUAL_REVIEW`) linked to policy version IDs and explicit reason codes (`INC_BELOW_MIN`, `SCORE_HIGH_PASS`). Incomes below product thresholds throw `PolicyViolationException`.
- **Underwriter Document Queue (AC-06)**: Document verification audit trail requiring 100% document verification before final approval.
- **Fixed-Point Amortization Math (AC-07 & NFR-01)**: Standard EMI formula enforced using `BigDecimal` math, maintaining total payable invariants:
$$\sum \text{Principal} + \sum \text{Interest} = \text{Total Payable}$$
- **Disbursement Metadata (AC-08)**: Immutable release records linked to funding pools.
- **Repayment & DPD Bucketing (AC-09)**: Principal reduction and daily delinquency classification:
  - `CURRENT` (0 DPD)
  - `DPD-30` (1-30 DPD)
  - `DPD-60` (31-60 DPD)
  - `DPD-90` (61-90 DPD)
  - `NPA` (>90 DPD)
- **Audited Admin Overrides (AC-10)**: Strict governance allowing overrides of `AUTO_REJECT` with enforced audit metadata (user ID, timestamp, reason code, comment).

---

## 4. Business Success Metrics
- **Time to Launch Product**: Reduced from weeks to minutes via JSON policy specification.
- **Automated Underwriting Straight-Through Processing (STP)**: Target >= 70% auto-decisioning.
- **Auditability**: 100% compliance with zero silent decision changes or un-audited overrides.
- **Financial Precision**: 0 rounding loss; 100% fixed-point compliance across all repayment posting runs.
