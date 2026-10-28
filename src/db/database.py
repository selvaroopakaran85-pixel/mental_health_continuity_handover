"""
SQLite Database Persistence Layer for Mental Health Continuity System.
Replaces in-memory JSON with SQLite storage, relational schemas, versioned migrations,
un-alterable emergency audit logging, and RBAC authentication support.
"""

import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from src.models.data_models import (
    ClientProfile,
    ConsentMatrix,
    SessionNote,
    Goal,
    PendingAction,
    RoleEnum,
    ConsentCategory,
)

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "mental_health.db")
)
SYNTHETIC_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_clients.json")
)
LONGITUDINAL_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "longitudinal_ehr_dataset.json")
)


class DatabaseManager:
    """
    SQLite Database Manager providing relational persistence, schema migrations,
    CRUD operations, and un-alterable emergency break-glass audit logging.
    """

    MIGRATIONS = [
        (
            1,
            "v1_initial_core_schema",
            """
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                preferred_name TEXT NOT NULL,
                pronouns TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS consent_matrices (
                client_id TEXT PRIMARY KEY,
                share_trauma_history INTEGER NOT NULL,
                share_medical_diagnosis INTEGER NOT NULL,
                share_social_determinants INTEGER NOT NULL,
                share_substance_history INTEGER NOT NULL,
                share_third_party INTEGER NOT NULL,
                allowed_roles TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS session_notes (
                session_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                date TEXT,
                author_role TEXT NOT NULL,
                author_name TEXT DEFAULT 'Staff Clinician',
                summary TEXT NOT NULL,
                sensitive_categories TEXT NOT NULL,
                risk_level TEXT DEFAULT 'low',
                quality_score REAL DEFAULT 1.0,
                FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                assigned_role TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pending_actions (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                assigned_role TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
            );
            """,
        ),
        (
            2,
            "v2_emergency_break_glass_audit",
            """
            CREATE TABLE IF NOT EXISTS emergency_audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                client_id TEXT NOT NULL,
                duty_clinician_id TEXT NOT NULL,
                emergency_reason TEXT NOT NULL,
                supervisor_code TEXT NOT NULL,
                actions_accessed TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients (client_id)
            );
            """,
        ),
        (
            3,
            "v3_rbac_clinician_users",
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL
            );

            INSERT OR IGNORE INTO users VALUES
                ('U-01', 'Sarah Miller, LPC', 'counsellor', 'Psychological Services'),
                ('U-02', 'Mark Davis, MSW', 'social_worker', 'Social & Housing Support'),
                ('U-03', 'Nurse Kelly, RN', 'duty_team', '24/7 Triage & Crisis Response'),
                ('U-04', 'Dr. Smith, MD', 'medical_clinician', 'Psychiatric & Medical Care');
            """,
        ),
        (
            4,
            "v4_longitudinal_indices_and_author_columns",
            """
            CREATE INDEX IF NOT EXISTS idx_session_notes_client_date 
                ON session_notes (client_id, date);
            CREATE INDEX IF NOT EXISTS idx_goals_client_status 
                ON goals (client_id, status);
            CREATE INDEX IF NOT EXISTS idx_actions_client_role 
                ON pending_actions (client_id, assigned_role);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_client 
                ON emergency_audit_logs (client_id);
            """,
        ),
    ]

    def __init__(self, db_path: str = DB_PATH, auto_seed: bool = True):
        self.db_path = db_path
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_migrations_table()
        self.apply_migrations()
        if auto_seed and self.db_path != ":memory:":
            self._auto_seed_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            return self._mem_conn
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_migrations_table(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def apply_migrations(self):
        """Applies pending schema migrations in numerical order."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_migrations")
            applied_versions = {row[0] for row in cursor.fetchall()}

            for version, name, sql_script in self.MIGRATIONS:
                if version not in applied_versions:
                    cursor.executescript(sql_script)
                    cursor.execute(
                        "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                        (version, name),
                    )
            conn.commit()

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Returns the list of applied database migrations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version ASC")
            return [dict(row) for row in cursor.fetchall()]

    def _auto_seed_if_empty(self):
        """Auto-seeds database from synthetic and longitudinal datasets if empty."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients")
            count = cursor.fetchone()[0]

        if count == 0:
            if os.path.exists(SYNTHETIC_DATA_PATH):
                self.seed_from_json(SYNTHETIC_DATA_PATH)
            if os.path.exists(LONGITUDINAL_DATA_PATH):
                self.seed_from_json(LONGITUDINAL_DATA_PATH)

    def seed_from_json(self, json_path: str):
        """Seeds SQLite database from synthetic or longitudinal clients JSON file."""
        if not os.path.exists(json_path):
            return
        with open(json_path, "r", encoding="utf-8") as f:
            raw_clients = json.load(f)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for c_dict in raw_clients:
                client = ClientProfile(**c_dict)
                cursor.execute(
                    "INSERT OR REPLACE INTO clients VALUES (?, ?, ?)",
                    (client.client_id, client.preferred_name, client.pronouns),
                )
                cm = client.consent_matrix
                allowed_json = json.dumps([r.value for r in cm.allowed_roles])
                cursor.execute(
                    "INSERT OR REPLACE INTO consent_matrices VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        client.client_id,
                        int(cm.share_trauma_history),
                        int(cm.share_medical_diagnosis),
                        int(cm.share_social_determinants),
                        int(cm.share_substance_history),
                        int(cm.share_third_party),
                        allowed_json,
                    ),
                )
                for note in client.session_notes:
                    sens_json = json.dumps([s.value for s in note.sensitive_categories])
                    cursor.execute(
                        "INSERT OR REPLACE INTO session_notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            note.session_id,
                            client.client_id,
                            note.date,
                            note.author_role.value,
                            getattr(note, "author_name", "Staff Clinician"),
                            note.summary,
                            sens_json,
                            note.risk_level,
                            note.quality_score,
                        ),
                    )
                for goal in client.active_goals:
                    cursor.execute(
                        "INSERT OR REPLACE INTO goals VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            goal.id,
                            client.client_id,
                            goal.title,
                            goal.category,
                            goal.status,
                            goal.priority,
                            goal.assigned_role.value,
                        ),
                    )
                for action in client.pending_actions:
                    cursor.execute(
                        "INSERT OR REPLACE INTO pending_actions VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            action.id,
                            client.client_id,
                            action.assigned_role.value,
                            action.description,
                            action.due_date,
                            action.status,
                        ),
                    )
            conn.commit()

    def list_client_ids(self) -> List[str]:
        """Returns sorted list of all client IDs stored in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT client_id FROM clients ORDER BY client_id ASC")
            return [row[0] for row in cursor.fetchall()]

    def get_client_profile(self, client_id: str) -> Optional[ClientProfile]:
        """Loads a ClientProfile object from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
            c_row = cursor.fetchone()
            if not c_row:
                return None

            cursor.execute("SELECT * FROM consent_matrices WHERE client_id = ?", (client_id,))
            cm_row = cursor.fetchone()
            if cm_row:
                allowed_roles = [RoleEnum(r) for r in json.loads(cm_row["allowed_roles"])]
                consent_matrix = ConsentMatrix(
                    share_trauma_history=bool(cm_row["share_trauma_history"]),
                    share_medical_diagnosis=bool(cm_row["share_medical_diagnosis"]),
                    share_social_determinants=bool(cm_row["share_social_determinants"]),
                    share_substance_history=bool(cm_row["share_substance_history"]),
                    share_third_party=bool(cm_row["share_third_party"]),
                    allowed_roles=allowed_roles,
                )
            else:
                consent_matrix = ConsentMatrix()

            cursor.execute(
                "SELECT * FROM session_notes WHERE client_id = ? ORDER BY date ASC, session_id ASC",
                (client_id,),
            )
            note_rows = cursor.fetchall()
            session_notes = []
            for nr in note_rows:
                cats = [ConsentCategory(c) for c in json.loads(nr["sensitive_categories"])]
                session_notes.append(
                    SessionNote(
                        session_id=nr["session_id"],
                        date=nr["date"],
                        author_role=RoleEnum(nr["author_role"]),
                        author_name=nr["author_name"] if "author_name" in nr.keys() else "Staff Clinician",
                        summary=nr["summary"],
                        sensitive_categories=cats,
                        risk_level=nr["risk_level"],
                        quality_score=nr["quality_score"],
                    )
                )

            cursor.execute("SELECT * FROM goals WHERE client_id = ?", (client_id,))
            goal_rows = cursor.fetchall()
            goals = [
                Goal(
                    id=gr["id"],
                    title=gr["title"],
                    category=gr["category"],
                    status=gr["status"],
                    priority=gr["priority"],
                    assigned_role=RoleEnum(gr["assigned_role"]),
                )
                for gr in goal_rows
            ]

            cursor.execute("SELECT * FROM pending_actions WHERE client_id = ?", (client_id,))
            action_rows = cursor.fetchall()
            actions = [
                PendingAction(
                    id=ar["id"],
                    assigned_role=RoleEnum(ar["assigned_role"]),
                    description=ar["description"],
                    due_date=ar["due_date"],
                    status=ar["status"],
                )
                for ar in action_rows
            ]

            return ClientProfile(
                client_id=c_row["client_id"],
                preferred_name=c_row["preferred_name"],
                pronouns=c_row["pronouns"],
                consent_matrix=consent_matrix,
                active_goals=goals,
                pending_actions=actions,
                session_notes=session_notes,
            )

    def save_client_profile(self, client: ClientProfile):
        """Persists or updates a ClientProfile back into SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO clients VALUES (?, ?, ?)",
                (client.client_id, client.preferred_name, client.pronouns),
            )
            cm = client.consent_matrix
            allowed_json = json.dumps([r.value for r in cm.allowed_roles])
            cursor.execute(
                "INSERT OR REPLACE INTO consent_matrices VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    client.client_id,
                    int(cm.share_trauma_history),
                    int(cm.share_medical_diagnosis),
                    int(cm.share_social_determinants),
                    int(cm.share_substance_history),
                    int(cm.share_third_party),
                    allowed_json,
                ),
            )
            for note in client.session_notes:
                sens_json = json.dumps([s.value for s in note.sensitive_categories])
                cursor.execute(
                    "INSERT OR REPLACE INTO session_notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        note.session_id,
                        client.client_id,
                        note.date,
                        note.author_role.value,
                        getattr(note, "author_name", "Staff Clinician"),
                        note.summary,
                        sens_json,
                        note.risk_level,
                        note.quality_score,
                    ),
                )
            for goal in client.active_goals:
                cursor.execute(
                    "INSERT OR REPLACE INTO goals VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        goal.id,
                        client.client_id,
                        goal.title,
                        goal.category,
                        goal.status,
                        goal.priority,
                        goal.assigned_role.value,
                    ),
                )
            for action in client.pending_actions:
                cursor.execute(
                    "INSERT OR REPLACE INTO pending_actions VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        action.id,
                        client.client_id,
                        action.assigned_role.value,
                        action.description,
                        action.due_date,
                        action.status,
                    ),
                )
            conn.commit()

    def log_emergency_override(
        self,
        client_id: str,
        duty_clinician_id: str,
        emergency_reason: str,
        supervisor_code: str,
        actions_accessed: str,
    ) -> int:
        """Inserts an immutable audit record for break-glass emergency override."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO clients (client_id, preferred_name, pronouns) VALUES (?, ?, ?)",
                (client_id, f"Client {client_id}", "they/them"),
            )
            cursor.execute(
                """
                INSERT INTO emergency_audit_logs 
                (client_id, duty_clinician_id, emergency_reason, supervisor_code, actions_accessed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, duty_clinician_id, emergency_reason, supervisor_code, actions_accessed),
            )
            conn.commit()
            return cursor.lastrowid

    def get_emergency_audit_logs(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves emergency break-glass audit logs, optionally filtered by client_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if client_id:
                cursor.execute(
                    "SELECT * FROM emergency_audit_logs WHERE client_id = ? ORDER BY timestamp DESC",
                    (client_id,),
                )
            else:
                cursor.execute("SELECT * FROM emergency_audit_logs ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
