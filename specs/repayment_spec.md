# Repayment & Amortization Feature Specification

## Module Context
The Repayment module handles fixed-point EMI amortization schedule generation, repayment posting, principal balance updates, and daily DPD/NPA delinquency bucket recalculation.

---

## Acceptance Criteria

### AC-07: EMI Amortization Schedule Invariant Formula
**Given** an approved loan application with principal $P$, annual interest rate $r$, and tenure $n$ months  
**When** the repayment schedule is generated using the EMI formula:
$$EMI = \frac{P \times r_m \times (1 + r_m)^n}{(1 + r_m)^n - 1}$$
where $r_m = \frac{r}{12 \times 100}$  
**Then** each installment row contains `installmentNumber`, `dueDate`, `principalComponent`, `interestComponent`, `emiAmount`, and `remainingBalance` computed using `BigDecimal` (2 decimal places, `RoundingMode.HALF_UP`)  
**And** the financial invariant strictly holds:
$$\sum_{i=1}^n \text{principalComponent}_i + \sum_{i=1}^n \text{interestComponent}_i = \sum_{i=1}^n \text{emiAmount}_i = \text{Total Payable}$$
**And** $\sum_{i=1}^n \text{principalComponent}_i = P$ exactly.

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-07")`
- Test Location: `tests/services/EMICalculatorTest.java`

---

### AC-09: Repayment Posting & Delinquency Bucket Recalculation
**Given** an active loan with an outstanding principal balance and current status  
**When** a repayment payment is posted via POST `/api/v1/repayments`  
**Then** the payment reduces outstanding principal  
**And** the system recalculates Days Past Due (DPD) and updates the delinquency bucket based on schedule:
- `CURRENT`: DPD == 0
- `DPD-30`: 1 <= DPD <= 30
- `DPD-60`: 31 <= DPD <= 60
- `DPD-90`: 61 <= DPD <= 90
- `NPA`: DPD > 90 (Non-Performing Asset)

#### Code & Test Tag
- Test Identifier: `@TestTag("AC-09")`
- Test Location: `tests/services/RepaymentServiceTest.java`
