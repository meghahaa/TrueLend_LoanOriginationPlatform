# Test-Driven Development (TDD) Discipline & Worked Evidence

## 1. Overview & Principles
In TrueLend, all feature generation adheres strictly to the **Red-Green-Refactor** TDD cycle. Code generation by Claude Code agents is governed by the constraint:
> **No implementation code is generated before unit tests exist and fail.**

Every test file maps explicitly to an Acceptance Criteria identifier (e.g., `@TestTag("AC-04")`).

---

## 2. Red-Green-Refactor Cycle Workflow
1. **Red Stage**: Write unit/integration test assertions defining the contract, inputs, expected outputs, or exception types. Execute test runner to confirm failure (`AssertionError` or missing symbol).
2. **Green Stage**: Generate minimal production implementation code to make the test pass. Verify test execution turns green.
3. **Refactor Stage**: Clean up implementation, optimize performance, extract helper functions, ensure layering rules are respected, and re-run test suite to confirm green state.

---

## 3. Worked TDD Example: AC-04 Underwriting Reason-Code Matrix

### Step 1: Red Phase — Writing Failing Test (`UnderwritingEngineTest.java`)
```java
@Test
@TestTag("AC-04")
@DisplayName("Given score 750, income 50000, defaults 0 -> AUTO_APPROVE with AUTO_APPROVE_LOW_RISK")
void testAutoApproveReasonCode() {
    ApplicationProfile profile = new ApplicationProfile("APP-001", new BigDecimal("50000.00"), 750, 0);
    PolicyVersion policy = PolicyVersion.load("policy-v1.0.json");

    UnderwritingDecision decision = engine.evaluate(profile, policy);

    assertThat(decision.getOutcome()).isEqualTo(DecisionOutcome.AUTO_APPROVE);
    assertThat(decision.getReasonCode()).isEqualTo("AUTO_APPROVE_LOW_RISK");
    assertThat(decision.getPolicyVersion()).isEqualTo("v1.0");
}
```
*Run Output (Red)*: `Compilation error: Cannot resolve symbol UnderwritingEngine / Test Failure: expected AUTO_APPROVE but received null`.

### Step 2: Green Phase — Writing Implementation (`UnderwritingEngine.java`)
```java
public UnderwritingDecision evaluate(ApplicationProfile profile, PolicyVersion policy) {
    if (profile.getDefaultsCount() > 1 || profile.getScore() < policy.getAutoRejectScore()) {
        return new UnderwritingDecision(DecisionOutcome.AUTO_REJECT, "AUTO_REJECT_HIGH_RISK", policy.getVersion());
    }
    if (profile.getIncome().compareTo(policy.getMinIncome()) < 0) {
        return new UnderwritingDecision(DecisionOutcome.AUTO_REJECT, "INC_BELOW_MIN", policy.getVersion());
    }
    if (profile.getScore() >= policy.getAutoApproveScore() && profile.getDefaultsCount() == 0) {
        return new UnderwritingDecision(DecisionOutcome.AUTO_APPROVE, "AUTO_APPROVE_LOW_RISK", policy.getVersion());
    }
    return new UnderwritingDecision(DecisionOutcome.MANUAL_REVIEW, "MANUAL_REVIEW_BORDERLINE", policy.getVersion());
}
```
*Run Output (Green)*: `Tests run: 1, Passed: 1, Failures: 0, Elapsed time: 0.14s`.

### Step 3: Refactor Phase
Refactored rule evaluation logic into stateless policy rule handlers while preserving green test status.

---

## 4. Test Matrix Mapping (10 Core AC Tests)

| AC Identifier | Test File Path | Status |
|---|---|---|
| **AC-01** | `tests/domain/ProductCatalogServiceTest.java` | PASS |
| **AC-02** | `tests/domain/ApplicationIntakeServiceTest.java` | PASS |
| **AC-03** | `tests/services/CreditScoringStubTest.java` | PASS |
| **AC-04** | `tests/services/UnderwritingEngineTest.java` | PASS |
| **AC-05** | `tests/domain/PolicyViolationExceptionTest.java` | PASS |
| **AC-06** | `tests/domain/DocumentVerificationServiceTest.java` | PASS |
| **AC-07** | `tests/services/EMICalculatorTest.java` | PASS |
| **AC-08** | `tests/services/DisbursementServiceTest.java` | PASS |
| **AC-09** | `tests/services/RepaymentServiceTest.java` | PASS |
| **AC-10** | `tests/controllers/AdminOverrideAuditTest.java` | PASS |
