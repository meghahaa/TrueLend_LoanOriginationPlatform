# TrueLend — Configurable Loan Origination Platform

TrueLend is a policy-driven loan origination and servicing platform. It automates the full lending lifecycle: **Application Intake → Underwriting Decision → Document Verification → Loan Disbursement → Repayment & Delinquency Tracking**.

Business administrators can change underwriting thresholds, interest rates, and loan limits on the fly by publishing versioned policies without writing code or restarting the system.

---

## 🚀 Quick Start Guide (How to Run the Website)

Follow these simple steps to launch TrueLend on your computer.

### Prerequisites
Make sure you have installed:
- **Python 3.11 or higher** ([Download Python](https://www.python.org/downloads/))
- **Node.js 20 or higher** ([Download Node.js](https://nodejs.org/))

---

### Step 1: Open Your Terminal
Open **Terminal** (macOS/Linux) or **PowerShell / Command Prompt** (Windows) and navigate to the project directory:
```bash
cd TrueLend_LoanOriginationPlatform
```

---

### Step 2: Set Up Python Virtual Environment
Create and activate an isolated Python environment:

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

### Step 3: Install Python Dependencies
Install the required backend packages:
```bash
pip install -r requirements.txt
```

---

### Step 4: Install Frontend Dependencies (One-time setup)
```bash
cd frontend
npm install
npm run build
cd ..
```

---

### Step 5: Start the Platform
Run the single start command from the project root:
```bash
python -m src
```

You will see output indicating the server has started:
```text
Starting TrueLend Platform on http://0.0.0.0:8000 ...
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### Step 6: Open the Website in Your Browser
Open your web browser (Chrome, Edge, Safari, Firefox) and visit:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 👥 Demo Logins & Roles

On the login page, you can choose from ready-made demo accounts using the dropdown menu:

| Role | Demo User ID | Purpose & Capabilities |
| :--- | :--- | :--- |
| **Customer** | `demo-customer-1` (`cust-001`) | • Apply for Personal, Vehicle, or Education loans<br>• View instant credit score & auto-decision<br>• Upload required documents<br>• Track application progress & view EMI schedule<br>• Make loan repayments |
| **Customer 2** | `demo-customer-2` (`cust-002`) | • Secondary customer account to test multi-tenancy & access boundaries |
| **Underwriter** | `demo-underwriter-1` (`uw-001`) | • Access Underwriter Workbench queue<br>• Review and verify uploaded customer documents<br>• Make manual `APPROVE` or `REJECT` decisions<br>• Disburse approved loans |
| **Admin** | `demo-admin-1` (`adm-001`) | • View complete portfolio health dashboard (NPA, delinquency buckets, total overdue)<br>• Filter and search all applications<br>• Perform executive override on rejected applications<br>• Edit policy thresholds & interest rates in the Policy Editor |

---

## 🧭 Step-by-Step Walkthrough to Test the Features

### 1. Apply for a Loan (as Customer)
1. Select **Customer 1 (`cust-001`)** and click **Sign In**.
2. Go to the **Apply for Loan** tab.
3. Choose a loan product (e.g., *Personal Loan*), enter your desired amount (e.g., `200000`), tenure (e.g., `24`), and income details.
4. Click **Submit Loan Application**.
5. You will see an instant underwriting result (`APPROVED`, `MANUAL_REVIEW`, or `REJECTED`) along with your credit score and required document checklist.
6. Copy your **Application ID**.

### 2. Verify Documents & Disburse (as Underwriter)
1. Click **Logout** at the top right and sign in as **Underwriter 1 (`uw-001`)**.
2. Open the **Underwriter Workbench** tab.
3. Applications requiring document verification or manual decision appear in the queue.
4. Click on an application, review each document, and click **Verify Valid**.
5. Once all required documents are verified, click **Approve Loan** or **Disburse Loan**.

### 3. Make Repayments & View Schedule (as Customer)
1. Switch back to **Customer 1 (`cust-001`)**.
2. Open the **Repayment & Schedule** tab and enter your Application ID.
3. View the complete month-by-month EMI amortization schedule.
4. Enter a payment amount (e.g., exact EMI amount) and click **Submit Payment**.
5. Watch the outstanding principal decrease and view the payment allocation receipt.

### 4. Monitor Portfolio & Update Policies (as Admin)
1. Switch to **Admin 1 (`adm-001`)**.
2. Open **Portfolio Dashboard** to view portfolio statistics, delinquency buckets (`CURRENT`, `DPD-30`, `DPD-60`, `DPD-90`, `NPA`), and total overdue amount.
3. Open **Policy Editor** to adjust minimum credit score thresholds or annual interest rates. Enter a change note and click **Publish New Policy Version**. All future applications will immediately evaluate against the new policy version.

---

## 🧪 Running Automated Tests & Verification

For evaluators and developers, TrueLend includes comprehensive test suites:

### 1. Backend Unit, API, & Architecture Tests
```bash
# Run pytest with code coverage (minimum 80% required)
pytest --cov=src --cov-report=xml --cov-fail-under=80
```

### 2. Architecture Layering Contracts
```bash
# Verify strict 4-layer architecture boundaries (api -> services -> repositories -> domain)
lint-imports
```

### 3. Acceptance Criteria (AC) Traceability Scanner
```bash
# Verify 100% of specification requirements have automated test coverage
python scripts/ac_coverage.py
```

### 4. Frontend Component & E2E Tests
```bash
cd frontend
# Run frontend unit tests (Vitest)
npm test

# Run End-to-End browser tests (Playwright)
npx playwright test
```

---

## 🏗️ Technical Architecture

TrueLend follows a strict **Clean Architecture / Domain-Driven Design (DDD)** pattern:

```text
Frontend (React + Vite + TypeScript)
   │
   ▼  [REST API / JSON / Bearer Tokens]
src/api/            ── Controllers & Pydantic request/response models
   │
   ▼
src/services/       ── Feature orchestration, Actor authorization & audit logging
   │
   ▼
src/repositories/   ── SQLite database persistence & append-only tables
   │
   ▼
src/domain/         ── Pure business rules (credit score, EMI math with Decimal, policy gate)
```

- **Money Precision**: All monetary values use fixed-point arithmetic (`Decimal`) with exact rounding (`ROUND_HALF_UP`) — never floating point.
- **Append-Only Immutability**: Policy versions, repayment schedules, audit logs, and disbursement records are insert-only and cannot be modified or deleted.
- **Privacy & PII Protection**: Synthetic PAN and Aadhaar identifiers are masked (`XXXXXX1234`) at persistence boundaries and never written to logs.
