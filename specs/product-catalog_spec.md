# Product Catalog & Policy Feature Specification

## Module Context
The Product Catalog module manages the portfolio of loan products offered by Horizon Bank. Product rules (minimum income, minimum/maximum loan amount, interest rate range, tenure bounds, required document checklist) are decoupled from application logic and loaded from versioned policy files.

---

## Acceptance Criteria

### AC-01: Multi-Product Catalog with Sourced Policy Rules
**Given** the application starts up or a new policy version is loaded  
**When** the product catalog service initializes  
**Then** it must load at least 3 distinct loan products:
1. `PERSONAL_LOAN`
2. `VEHICLE_LOAN`
3. `EDUCATION_LOAN`  
**And** each product must be associated with its distinct rule set loaded from an active versioned policy file (e.g. `policy-v1.0.json`).

#### Detailed Verification Steps
- **Given** policy file `policy-v1.0.json` containing configurations for `PERSONAL_LOAN`, `VEHICLE_LOAN`, and `EDUCATION_LOAN`.
- **When** calling GET `/api/v1/products`.
- **Then** response contains list of 3 products, each matching the schema:
  - `productId`: String enum (`PERSONAL_LOAN`, `VEHICLE_LOAN`, `EDUCATION_LOAN`)
  - `displayName`: Human readable name
  - `minIncome`: Fixed-point decimal
  - `minCreditScore`: Integer
  - `interestRateAnnual`: Fixed-point percentage
  - `maxTenureMonths`: Integer
  - `requiredDocuments`: List of DocumentType enums
  - `policyVersion`: Active policy version string (e.g., `v1.0`)

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-01")`
- Test Location: `tests/domain/ProductCatalogServiceTest.java`
