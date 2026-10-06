# Architecture Specification & Technical Design — TrueLend

> **System**: TrueLend Loan Origination & Underwriting System  
> **Pattern**: Layered Clean Architecture (Controllers -> Services -> Domain & Policy Engine)

---

## 1. High-Level Architectural Context & Layering

```mermaid
flowchart TD
    subgraph Client Layer
        ReactUI["React / Web UI (Customer & Underwriter)"]
        RESTClient["External REST API Clients"]
    end

    subgraph Controller Layer ["Controller Layer (src/controllers)"]
        AppController["ApplicationIntakeController"]
        UnderwritingController["UnderwritingController"]
        ProductController["ProductCatalogController"]
        RepaymentController["RepaymentController"]
        AdminController["AdminOverrideController"]
    end

    subgraph Service Layer ["Service Layer (src/services)"]
        AppService["ApplicationService"]
        UWEngine["UnderwritingEngineService"]
        EMICalc["EMIScheduleService"]
        RepayService["RepaymentService"]
        CreditScorer["CreditScoringStub"]
    end

    subgraph Domain Layer ["Domain & Policy Engine (src/domain)"]
        PolicyEngine["PolicyRulesEngine"]
        PolicyVersion["PolicyVersion (Immutable JSON)"]
        LoanApp["LoanApplication Entity"]
        EMISchedule["RepaymentSchedule ValueObject"]
        AuditLog["AuditRecord Entity"]
    end

    subgraph Database Layer
        H2DB[(H2 / RDBMS Database)]
    end

    ReactUI --> AppController
    ReactUI --> UnderwritingController
    ReactUI --> ProductController
    ReactUI --> RepaymentController
    ReactUI --> AdminController

    AppController --> AppService
    UnderwritingController --> UWEngine
    ProductController --> AppService
    RepaymentController --> RepayService
    AdminController --> UWEngine

    AppService --> CreditScorer
    UWEngine --> PolicyEngine
    PolicyEngine --> PolicyVersion
    EMICalc --> EMISchedule
    RepayService --> EMISchedule
    AppService --> LoanApp
    UWEngine --> AuditLog

    AppService --> H2DB
    UWEngine --> H2DB
    RepayService --> H2DB
```

---

## 2. Underwriting Sequence Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    actor Underwriter
    participant API as ApplicationIntakeController
    participant Intake as ApplicationService
    participant Scorer as CreditScoringStub
    participant UW as UnderwritingEngineService
    participant Policy as PolicyRulesEngine
    participant DB as Repository / DB

    Customer->>API: POST /api/v1/applications (Income, Age, ProductId)
    API->>Intake: submitApplication(dto)
    Intake->>Policy: validateIncomeThreshold(income, productId)
    alt Income < Min Threshold
        Policy-->>Intake: Throw PolicyViolationException (AC-05)
        Intake-->>API: 400 Bad Request Payload
    else Income >= Min Threshold
        Intake->>Scorer: calculateScore(profile) (AC-03)
        Scorer-->>Intake: Score (e.g., 720)
        Intake->>UW: evaluateApplication(appId)
        UW->>Policy: evaluateRules(score, income, defaults, policyVersion)
        Policy-->>UW: Decision (AUTO_APPROVE / AUTO_REJECT / MANUAL_REVIEW) (AC-04)
        UW->>DB: Save Application & Decision Audit
        UW-->>API: ApplicationResponse DTO
        API-->>Customer: 201 Created (Status & Reason Code)
    end

    opt Underwriter Document Verification (AC-06)
        Underwriter->>API: POST /api/v1/applications/{id}/documents/verify
        API->>Intake: verifyDocument(docId, VERIFIED/REJECTED)
        Intake->>DB: Update Document Checklist Status
    end
```

---

## 3. Structural Layering Constraints (ArchUnit Enforced)
1. **Domain Independence**: Classes in `src/domain/` MUST NOT depend on `src/controllers/`, Spring MVC, or UI layers.
2. **Controller Scope**: Controllers MUST ONLY invoke Service interface methods and return DTOs.
3. **Fixed-Point Financial Standard**: Monetary calculations MUST ONLY use `BigDecimal`. `double` and `float` types are forbidden in domain money fields.
4. **Immutability of Policy & Schedules**: Repayment schedules and Policy Versions are append-only. Entities mapped to DB tables `policy_versions` and `repayment_schedules` must not expose `UPDATE` or `DELETE` mutation endpoints.
