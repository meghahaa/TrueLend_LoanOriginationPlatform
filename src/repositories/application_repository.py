"""
ApplicationRepository — SQLite persistence for loan applications, schedules, disbursements, repayments, and audit.
Uses stdlib sqlite3, parameterised SQL only.
Money stored as TEXT (Decimal strings). Returns domain objects/dicts.
No business rules here.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.domain.emi_calculator import RepaymentSchedule, ScheduleRow
from src.domain.models import DisbursementRecord
from src.domain.repayment_allocation import RepaymentAllocation


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id                    TEXT PRIMARY KEY,
    owner_user_id         TEXT NOT NULL,
    product               TEXT NOT NULL,
    amount                TEXT NOT NULL,
    tenure_months         INTEGER NOT NULL,
    full_name             TEXT NOT NULL,
    age                   INTEGER NOT NULL,
    monthly_income        TEXT NOT NULL,
    pan_masked            TEXT NOT NULL,
    aadhaar_masked        TEXT NOT NULL,
    credit_history        TEXT NOT NULL,
    has_default           INTEGER NOT NULL,
    status                TEXT NOT NULL,
    decision              TEXT,
    reason_codes          TEXT NOT NULL DEFAULT '[]',
    policy_version        INTEGER NOT NULL,
    score                 INTEGER NOT NULL,
    outstanding_principal TEXT,
    delinquency_bucket    TEXT,
    dpd                   INTEGER DEFAULT 0,
    disbursed_at          TEXT,
    created_at            TEXT NOT NULL DEFAULT (datetime('now','utc'))
);

CREATE TABLE IF NOT EXISTS application_documents (
    id               TEXT PRIMARY KEY,
    application_id   TEXT NOT NULL REFERENCES applications(id),
    doc_type         TEXT NOT NULL,
    filename         TEXT,
    status           TEXT NOT NULL DEFAULT 'MISSING',
    rejection_reason TEXT
);

CREATE TABLE IF NOT EXISTS repayment_schedules (
    id                 TEXT PRIMARY KEY,
    application_id     TEXT NOT NULL REFERENCES applications(id),
    installment_number INTEGER NOT NULL,
    due_date           TEXT NOT NULL,
    opening_balance    TEXT NOT NULL,
    principal_component TEXT NOT NULL,
    interest_component TEXT NOT NULL,
    emi_amount         TEXT NOT NULL,
    remaining_balance  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS disbursements (
    id             TEXT PRIMARY KEY,
    application_id TEXT NOT NULL REFERENCES applications(id),
    amount         TEXT NOT NULL,
    funding_source TEXT NOT NULL,
    reference      TEXT NOT NULL,
    disbursed_at   TEXT NOT NULL,
    released_by    TEXT NOT NULL,
    status         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repayments (
    id             TEXT PRIMARY KEY,
    application_id TEXT NOT NULL REFERENCES applications(id),
    amount_paid    TEXT NOT NULL,
    paid_on        TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now','utc'))
);

CREATE TABLE IF NOT EXISTS repayment_allocations (
    id                  TEXT PRIMARY KEY,
    repayment_id        TEXT NOT NULL REFERENCES repayments(id),
    application_id      TEXT NOT NULL REFERENCES applications(id),
    installment_number  INTEGER NOT NULL,
    principal_allocated TEXT NOT NULL,
    interest_allocated  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id               TEXT PRIMARY KEY,
    actor_user_id    TEXT NOT NULL,
    role             TEXT,
    action           TEXT NOT NULL,
    application_id   TEXT,
    doc_type         TEXT,
    reason           TEXT,
    comment          TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
"""


def _mask(value: str) -> str:
    """Mask PAN/Aadhaar: last 4 chars visible, rest X."""
    if len(value) <= 4:
        return "XXXXXX" + value
    return "XXXXXX" + value[-4:]


class ApplicationRepository:
    def __init__(self, db_path: str = "truelend.db") -> None:
        self._db_path = db_path
        self._conn = _get_conn(db_path)
        self._migrate()

    def _migrate(self) -> None:
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._apply_column_migrations()

    def _apply_column_migrations(self) -> None:
        """Idempotently add any new columns that may be missing (safe on existing DBs)."""
        # Map: table -> list of (column_name, definition)
        migrations = {
            "applications": [
                ("outstanding_principal", "TEXT"),
                ("delinquency_bucket", "TEXT"),
                ("dpd", "INTEGER DEFAULT 0"),
                ("disbursed_at", "TEXT"),
            ],
            "audit_log": [
                ("role", "TEXT"),
            ],
        }
        for table, columns in migrations.items():
            existing = {
                row[1]
                for row in self._conn.execute(f"PRAGMA table_info({table})")
            }
            for col_name, col_def in columns:
                if col_name not in existing:
                    self._conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                    )
        self._conn.commit()


    # ------------------------------------------------------------------ #
    # Applications                                                         #
    # ------------------------------------------------------------------ #

    def create_application(
        self,
        *,
        owner_user_id: str,
        product: str,
        amount: Decimal,
        tenure_months: int,
        full_name: str,
        age: int,
        monthly_income: Decimal,
        pan: str,
        aadhaar: str,
        credit_history: str,
        has_default: bool,
        status: str,
        decision: Optional[str],
        reason_codes: List[str],
        policy_version: int,
        score: int,
        documents: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        app_id = str(uuid.uuid4())

        self._conn.execute(
            """
            INSERT INTO applications
              (id, owner_user_id, product, amount, tenure_months,
               full_name, age, monthly_income, pan_masked, aadhaar_masked,
               credit_history, has_default, status, decision,
               reason_codes, policy_version, score)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                app_id,
                owner_user_id,
                product,
                str(amount),
                tenure_months,
                full_name,
                age,
                str(monthly_income),
                _mask(pan),
                _mask(aadhaar),
                credit_history,
                1 if has_default else 0,
                status,
                decision,
                json.dumps(reason_codes),
                policy_version,
                score,
            ),
        )

        for doc in documents:
            self._conn.execute(
                """
                INSERT INTO application_documents (id, application_id, doc_type, filename, status)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(uuid.uuid4()),
                    app_id,
                    doc["doc_type"],
                    doc.get("filename"),
                    doc["status"],
                ),
            )

        self._conn.commit()
        return self.get_application(app_id)  # type: ignore[return-value]

    def get_application(self, app_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
        if row is None:
            return None

        docs = self._conn.execute(
            "SELECT doc_type, filename, status, rejection_reason FROM application_documents WHERE application_id = ?",
            (app_id,),
        ).fetchall()

        return {
            "id": row["id"],
            "owner_user_id": row["owner_user_id"],
            "product": row["product"],
            "amount": row["amount"],
            "tenure_months": row["tenure_months"],
            "full_name": row["full_name"],
            "age": row["age"],
            "monthly_income": row["monthly_income"],
            "pan_masked": row["pan_masked"],
            "aadhaar_masked": row["aadhaar_masked"],
            "credit_history": row["credit_history"],
            "has_default": bool(row["has_default"]),
            "status": row["status"],
            "decision": row["decision"],
            "reason_codes": json.loads(row["reason_codes"]),
            "policy_version": row["policy_version"],
            "score": row["score"],
            "outstanding_principal": row["outstanding_principal"],
            "delinquency_bucket": row["delinquency_bucket"],
            "dpd": row["dpd"],
            "disbursed_at": row["disbursed_at"],
            "documents": [
                {
                    "doc_type": d["doc_type"],
                    "filename": d["filename"],
                    "status": d["status"],
                    "rejection_reason": d["rejection_reason"],
                }
                for d in docs
            ],
        }

    def update_document_status(
        self,
        *,
        application_id: str,
        doc_type: str,
        filename: Optional[str],
        status: str,
        rejection_reason: Optional[str] = None,
    ) -> None:
        existing = self._conn.execute(
            "SELECT id FROM application_documents WHERE application_id=? AND doc_type=?",
            (application_id, doc_type),
        ).fetchone()

        if existing:
            self._conn.execute(
                """UPDATE application_documents
                   SET status=?, filename=COALESCE(?,filename), rejection_reason=?
                   WHERE application_id=? AND doc_type=?""",
                (status, filename, rejection_reason, application_id, doc_type),
            )
        else:
            self._conn.execute(
                """INSERT INTO application_documents (id, application_id, doc_type, filename, status, rejection_reason)
                   VALUES (?,?,?,?,?,?)""",
                (str(uuid.uuid4()), application_id, doc_type, filename, status, rejection_reason),
            )
        self._conn.commit()

    def update_application_status(
        self,
        *,
        app_id: str,
        status: str,
        decision: Optional[str] = None,
        reason_codes: Optional[List[str]] = None,
        outstanding_principal: Optional[str] = None,
        delinquency_bucket: Optional[str] = None,
        dpd: Optional[int] = None,
        disbursed_at: Optional[str] = None,
    ) -> None:
        fields = ["status = ?"]
        values: List[Any] = [status]

        if decision is not None:
            fields.append("decision = ?")
            values.append(decision)
        if reason_codes is not None:
            fields.append("reason_codes = ?")
            values.append(json.dumps(reason_codes))
        if outstanding_principal is not None:
            fields.append("outstanding_principal = ?")
            values.append(outstanding_principal)
        if delinquency_bucket is not None:
            fields.append("delinquency_bucket = ?")
            values.append(delinquency_bucket)
        if dpd is not None:
            fields.append("dpd = ?")
            values.append(dpd)
        if disbursed_at is not None:
            fields.append("disbursed_at = ?")
            values.append(disbursed_at)

        values.append(app_id)
        sql = f"UPDATE applications SET {', '.join(fields)} WHERE id = ?"
        self._conn.execute(sql, tuple(values))
        self._conn.commit()

    def list_manual_review(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """SELECT id FROM applications
               WHERE status = 'MANUAL_REVIEW'
               ORDER BY created_at ASC"""
        ).fetchall()
        result = []
        for row in rows:
            app = self.get_application(row["id"])
            if app:
                result.append(app)
        return result

    def list_applications(
        self,
        *,
        status: Optional[str] = None,
        product: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = []
        params: List[Any] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if product:
            conditions.append("product = ?")
            params.append(product)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total_row = self._conn.execute(
            f"SELECT COUNT(*) as cnt FROM applications {where_clause}", tuple(params)
        ).fetchone()
        total = total_row["cnt"] if total_row else 0

        offset = (page - 1) * page_size
        params.extend([page_size, offset])

        rows = self._conn.execute(
            f"""SELECT id FROM applications {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?""",
            tuple(params),
        ).fetchall()

        items = []
        for r in rows:
            app = self.get_application(r["id"])
            if app:
                items.append(app)
        return items, total

    def list_disbursed_applications(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id FROM applications WHERE status = 'DISBURSED'"
        ).fetchall()
        result = []
        for r in rows:
            app = self.get_application(r["id"])
            if app:
                result.append(app)
        return result

    # ------------------------------------------------------------------ #
    # Repayment Schedules (Insert-Only)                                   #
    # ------------------------------------------------------------------ #

    def save_schedule(self, application_id: str, schedule: RepaymentSchedule) -> None:
        # Check if already exists — schedule rows are insert-only
        existing = self._conn.execute(
            "SELECT id FROM repayment_schedules WHERE application_id = ? LIMIT 1",
            (application_id,),
        ).fetchone()
        if existing:
            raise FileExistsError(f"Repayment schedule already exists for application {application_id}")

        for row in schedule.rows:
            self._conn.execute(
                """
                INSERT INTO repayment_schedules
                  (id, application_id, installment_number, due_date,
                   opening_balance, principal_component, interest_component,
                   emi_amount, remaining_balance)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(uuid.uuid4()),
                    application_id,
                    row.installment_number,
                    row.due_date.isoformat(),
                    str(row.opening_balance),
                    str(row.principal_component),
                    str(row.interest_component),
                    str(row.emi_amount),
                    str(row.remaining_balance),
                ),
            )
        self._conn.commit()

    def get_schedule(self, application_id: str) -> Optional[RepaymentSchedule]:
        rows = self._conn.execute(
            """SELECT * FROM repayment_schedules
               WHERE application_id = ?
               ORDER BY installment_number ASC""",
            (application_id,),
        ).fetchall()
        if not rows:
            return None

        schedule_rows: List[ScheduleRow] = []
        total_principal = Decimal("0.00")
        total_interest = Decimal("0.00")

        for r in rows:
            p_comp = Decimal(r["principal_component"])
            i_comp = Decimal(r["interest_component"])
            total_principal += p_comp
            total_interest += i_comp
            schedule_rows.append(
                ScheduleRow(
                    installment_number=r["installment_number"],
                    due_date=date.fromisoformat(r["due_date"]),
                    opening_balance=Decimal(r["opening_balance"]),
                    principal_component=p_comp,
                    interest_component=i_comp,
                    emi_amount=Decimal(r["emi_amount"]),
                    remaining_balance=Decimal(r["remaining_balance"]),
                )
            )

        emi_amount = schedule_rows[0].emi_amount if schedule_rows else Decimal("0.00")
        total_payable = total_principal + total_interest

        return RepaymentSchedule(
            emi_amount=emi_amount,
            total_principal=total_principal,
            total_interest=total_interest,
            total_payable=total_payable,
            rows=schedule_rows,
        )

    # ------------------------------------------------------------------ #
    # Disbursements (Insert-Only)                                         #
    # ------------------------------------------------------------------ #

    def save_disbursement(self, record: DisbursementRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO disbursements
              (id, application_id, amount, funding_source, reference, disbursed_at, released_by, status)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                record.disbursement_id,
                record.application_id,
                str(record.amount),
                record.funding_source,
                record.reference,
                record.disbursed_at,
                record.released_by,
                record.status,
            ),
        )
        self._conn.commit()

    def get_disbursement(self, application_id: str) -> Optional[DisbursementRecord]:
        row = self._conn.execute(
            "SELECT * FROM disbursements WHERE application_id = ?", (application_id,)
        ).fetchone()
        if row is None:
            return None
        return DisbursementRecord(
            disbursement_id=row["id"],
            application_id=row["application_id"],
            amount=Decimal(row["amount"]),
            funding_source=row["funding_source"],
            reference=row["reference"],
            disbursed_at=row["disbursed_at"],
            released_by=row["released_by"],
            status=row["status"],
        )

    # ------------------------------------------------------------------ #
    # Repayments and Allocations (Insert-Only)                            #
    # ------------------------------------------------------------------ #

    def save_repayment_with_allocations(
        self,
        *,
        application_id: str,
        amount_paid: Decimal,
        paid_on: date,
        allocations: List[RepaymentAllocation],
        outstanding_principal: Decimal,
        delinquency_bucket: str,
        dpd: int,
    ) -> str:
        repayment_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO repayments (id, application_id, amount_paid, paid_on)
            VALUES (?,?,?,?)
            """,
            (repayment_id, application_id, str(amount_paid), paid_on.isoformat()),
        )

        for alloc in allocations:
            self._conn.execute(
                """
                INSERT INTO repayment_allocations
                  (id, repayment_id, application_id, installment_number, principal_allocated, interest_allocated)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    str(uuid.uuid4()),
                    repayment_id,
                    application_id,
                    alloc.installment_number,
                    str(alloc.principal_allocated),
                    str(alloc.interest_allocated),
                ),
            )

        self._conn.execute(
            """
            UPDATE applications
            SET outstanding_principal = ?, delinquency_bucket = ?, dpd = ?
            WHERE id = ?
            """,
            (str(outstanding_principal), delinquency_bucket, dpd, application_id),
        )
        self._conn.commit()
        return repayment_id

    def get_allocations(self, application_id: str) -> List[RepaymentAllocation]:
        rows = self._conn.execute(
            """
            SELECT installment_number, principal_allocated, interest_allocated
            FROM repayment_allocations
            WHERE application_id = ?
            ORDER BY id ASC
            """,
            (application_id,),
        ).fetchall()
        return [
            RepaymentAllocation(
                installment_number=r["installment_number"],
                principal_allocated=Decimal(r["principal_allocated"]),
                interest_allocated=Decimal(r["interest_allocated"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------ #
    # Audit log                                                            #
    # ------------------------------------------------------------------ #

    def write_audit(
        self,
        *,
        actor_user_id: str,
        action: str,
        role: Optional[str] = None,
        application_id: Optional[str] = None,
        doc_type: Optional[str] = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        self._conn.execute(
            """INSERT INTO audit_log (id, actor_user_id, role, action, application_id, doc_type, reason, comment)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                actor_user_id,
                role,
                action,
                application_id,
                doc_type,
                reason,
                comment,
            ),
        )
        self._conn.commit()

    def get_audit_log(self, application_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if application_id:
            rows = self._conn.execute(
                """SELECT * FROM audit_log WHERE application_id = ? ORDER BY created_at DESC""",
                (application_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT * FROM audit_log ORDER BY created_at DESC"""
            ).fetchall()

        return [
            {
                "id": r["id"],
                "user_id": r["actor_user_id"],
                "role": r["role"] or "",
                "action": r["action"],
                "application_id": r["application_id"],
                "doc_type": r["doc_type"],
                "reason_code": r["reason"],
                "comment": r["comment"],
                "timestamp": r["created_at"],
            }
            for r in rows
        ]
