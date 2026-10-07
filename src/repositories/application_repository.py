"""
ApplicationRepository — SQLite persistence for loan applications.
Uses stdlib sqlite3, parameterised SQL only.
Money stored as TEXT (Decimal strings). Returns domain-ish dicts/dataclasses.
No business rules here.
"""
from __future__ import annotations

import sqlite3
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id               TEXT PRIMARY KEY,
    owner_user_id    TEXT NOT NULL,
    product          TEXT NOT NULL,
    amount           TEXT NOT NULL,
    tenure_months    INTEGER NOT NULL,
    full_name        TEXT NOT NULL,
    age              INTEGER NOT NULL,
    monthly_income   TEXT NOT NULL,
    pan_masked       TEXT NOT NULL,
    aadhaar_masked   TEXT NOT NULL,
    credit_history   TEXT NOT NULL,
    has_default      INTEGER NOT NULL,
    status           TEXT NOT NULL,
    decision         TEXT,
    reason_codes     TEXT NOT NULL DEFAULT '[]',
    policy_version   INTEGER NOT NULL,
    score            INTEGER NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (datetime('now','utc'))
);

CREATE TABLE IF NOT EXISTS application_documents (
    id               TEXT PRIMARY KEY,
    application_id   TEXT NOT NULL REFERENCES applications(id),
    doc_type         TEXT NOT NULL,
    filename         TEXT,
    status           TEXT NOT NULL DEFAULT 'MISSING',
    rejection_reason TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id               TEXT PRIMARY KEY,
    actor_user_id    TEXT NOT NULL,
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
        documents: List[Dict[str, str]],  # [{"doc_type": ..., "filename": ..., "status": ...}]
    ) -> Dict[str, Any]:
        app_id = str(uuid.uuid4())
        import json

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
        import json

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
        # Upsert: update if exists, insert if not
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
    ) -> None:
        import json

        if reason_codes is not None:
            self._conn.execute(
                "UPDATE applications SET status=?, decision=?, reason_codes=? WHERE id=?",
                (status, decision, json.dumps(reason_codes), app_id),
            )
        elif decision is not None:
            self._conn.execute(
                "UPDATE applications SET status=?, decision=? WHERE id=?",
                (status, decision, app_id),
            )
        else:
            self._conn.execute(
                "UPDATE applications SET status=? WHERE id=?",
                (status, app_id),
            )
        self._conn.commit()

    def list_manual_review(self) -> List[Dict[str, Any]]:
        """List applications in MANUAL_REVIEW status, oldest first."""
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

    # ------------------------------------------------------------------ #
    # Audit log                                                            #
    # ------------------------------------------------------------------ #

    def write_audit(
        self,
        *,
        actor_user_id: str,
        action: str,
        application_id: Optional[str] = None,
        doc_type: Optional[str] = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        self._conn.execute(
            """INSERT INTO audit_log (id, actor_user_id, action, application_id, doc_type, reason, comment)
               VALUES (?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                actor_user_id,
                action,
                application_id,
                doc_type,
                reason,
                comment,
            ),
        )
        self._conn.commit()
