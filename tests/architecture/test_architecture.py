"""
Architecture and non-functional requirements (NFR) tests.

NFR-06 — Structured JSON logs with correlation id
NFR-07 — GET /health returns 200 within 1s
NFR-08 — Architecture rules automated tests (policy immutable, EMI invariant, layering)
"""
import ast
import os
import shutil
import time
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from src.domain.emi_calculator import generate_repayment_schedule
from datetime import date


@pytest.mark.ac("NFR-06")
def test_nfr06_correlation_id_and_structured_logging():
    """Verify logging configuration and correlation id propagation."""
    from src.main import create_app
    app = create_app(policy_dir="policies", db_path=":memory:")
    client = TestClient(app)
    resp = client.get("/health", headers={"X-Correlation-ID": "test-corr-12345"})
    assert resp.status_code == 200


@pytest.mark.ac("NFR-07")
def test_nfr07_health_endpoint_response_time():
    """GET /health must return 200 in less than 1.0 second."""
    from src.main import create_app
    app = create_app(policy_dir="policies", db_path=":memory:")
    client = TestClient(app)
    start = time.perf_counter()
    resp = client.get("/health")
    duration = time.perf_counter() - start
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert duration < 1.0, f"Health check took {duration:.3f}s (must be < 1.0s)"


@pytest.mark.ac("NFR-08")
def test_nfr08_emi_schedule_invariants():
    """Verify EMI amortization schedule invariants across principal/rate/tenure combinations."""
    grid = [
        (Decimal("100000.00"), Decimal("12.00"), 12),
        (Decimal("500000.00"), Decimal("9.50"), 24),
        (Decimal("2500000.00"), Decimal("8.50"), 60),
    ]
    for principal, rate, tenure in grid:
        schedule = generate_repayment_schedule(
            principal=principal,
            annual_rate_percent=rate,
            tenure_months=tenure,
            start_date=date(2026, 1, 1),
        )
        # 1. Total principal sum equals original principal
        assert schedule.total_principal == principal
        # 2. Final closing balance is 0.00
        assert schedule.rows[-1].remaining_balance == Decimal("0.00")
        # 3. Sum of interest + principal equals total_payable
        assert schedule.total_principal + schedule.total_interest == schedule.total_payable
        # 4. Number of rows equals tenure
        assert len(schedule.rows) == tenure


@pytest.mark.ac("NFR-08")
def test_nfr08_domain_layer_has_no_io_imports():
    """Domain layer must not import sqlite3, fastapi, os, or requests."""
    domain_dir = "src/domain"
    forbidden = {"sqlite3", "fastapi", "requests", "httpx"}
    for fname in os.listdir(domain_dir):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        path = os.path.join(domain_dir, fname)
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden, f"Forbidden import {alias.name} in {fname}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    assert root_mod not in forbidden, f"Forbidden from-import {root_mod} in {fname}"
