"""
Unit tests for SQLite Database Persistence, Schema Migrations, and RBAC Authorization.
"""

import os
import tempfile
from src.db.database import DatabaseManager
from src.db.auth import RBACManager
from src.models.data_models import RoleEnum


def test_database_schema_migrations():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_mgr = DatabaseManager(db_path, auto_seed=False)
        history = db_mgr.get_migration_history()
        assert len(history) == 4
        assert history[0]["version"] == 1
        assert history[0]["name"] == "v1_initial_core_schema"
        assert history[1]["name"] == "v2_emergency_break_glass_audit"
        assert history[2]["name"] == "v3_rbac_clinician_users"
        assert history[3]["name"] == "v4_longitudinal_indices_and_author_columns"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_database_seeding_and_crud():
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "synthetic_clients.json"
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_mgr = DatabaseManager(db_path, auto_seed=False)
        db_mgr.seed_from_json(json_path)

        # Load Alex Rivera (MH-101)
        client = db_mgr.get_client_profile("MH-101")
        assert client is not None
        assert client.preferred_name == "Alex Rivera"
        assert len(client.active_goals) >= 2
        assert len(client.session_notes) >= 2
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_longitudinal_ehr_persistence_and_queries():
    ehr_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "longitudinal_ehr_dataset.json"
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_mgr = DatabaseManager(db_path, auto_seed=False)
        db_mgr.seed_from_json(ehr_path)

        # Load Marcus Vance (MH-202)
        marcus = db_mgr.get_client_profile("MH-202")
        assert marcus is not None
        assert marcus.preferred_name == "Marcus Vance"
        assert len(marcus.session_notes) == 6
        assert len(marcus.active_goals) == 3

        # Verify multi-clinician roles recorded
        roles = {n.author_role for n in marcus.session_notes}
        assert RoleEnum.DUTY_TEAM in roles
        assert RoleEnum.MEDICAL_CLINICIAN in roles
        assert RoleEnum.COUNSELLOR in roles
        assert RoleEnum.SOCIAL_WORKER in roles
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_rbac_authorization():
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "synthetic_clients.json"
    )
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_mgr = DatabaseManager(db_path, auto_seed=False)
        db_mgr.seed_from_json(json_path)
        client = db_mgr.get_client_profile("MH-101")

        # Test valid role
        auth, msg = RBACManager.validate_role_access(RoleEnum.COUNSELLOR, client)
        assert auth is True

        # Test restricted role
        client.consent_matrix.allowed_roles = [RoleEnum.COUNSELLOR]
        auth_sw, msg_sw = RBACManager.validate_role_access(RoleEnum.SOCIAL_WORKER, client)
        assert auth_sw is False
        assert "RESTRICTED" in msg_sw
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
