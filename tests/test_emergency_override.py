"""
Unit tests for Crisis & Emergency Consent Override Protocol (IR-04 Break-Glass Protocol).
"""

import os
import tempfile
from src.models.data_models import ClientProfile, ConsentMatrix, SessionNote, RoleEnum
from src.db.database import DatabaseManager
from src.engine.emergency_override import EmergencyOverrideEngine, EmergencyOverrideRequest
from src.engine.summary_engine import SummaryEngine


def test_emergency_override_execution_and_db_logging():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_mgr = DatabaseManager(db_path)
        override_engine = EmergencyOverrideEngine(db_mgr)

        client = ClientProfile(
            client_id="EM-001",
            preferred_name="Emergency Client",
            pronouns="they/them",
            consent_matrix=ConsentMatrix(share_trauma_history=False),
            session_notes=[
                SessionNote(
                    session_id="S-CRISIS",
                    date="2026-10-04",
                    author_role=RoleEnum.COUNSELLOR,
                    summary="High crisis risk session. Disclosed severe distress.",
                )
            ],
        )

        req = EmergencyOverrideRequest(
            client_id="EM-001",
            duty_clinician_id="DUTY-NURSE-01",
            emergency_reason="Active crisis safety evaluation required",
            supervisor_approval_code="SUPERVISOR-EMERGENCY-AUTH",
        )

        success, msg, audit_rec = override_engine.validate_and_execute_override(req, client)

        assert success is True
        assert "APPROVED" in msg
        assert audit_rec["client_id"] == "EM-001"

        # Verify record persisted in SQLite DB
        db_logs = db_mgr.get_emergency_audit_logs("EM-001")
        assert len(db_logs) == 1
        assert db_logs[0]["duty_clinician_id"] == "DUTY-NURSE-01"

        # Summary integration test
        summary_engine = SummaryEngine(client)
        summary = summary_engine.generate_prototype_summary(RoleEnum.DUTY_TEAM, emergency_request=req)
        assert "CRISIS SAFETY OVERRIDE ACTIVE" in summary.disclaimer_header

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_emergency_override_rejection_invalid_code():
    db_mgr = DatabaseManager(":memory:")
    override_engine = EmergencyOverrideEngine(db_mgr)
    client = ClientProfile(
        client_id="EM-002",
        preferred_name="Rejection Test",
        pronouns="he/him",
        consent_matrix=ConsentMatrix(),
    )

    req = EmergencyOverrideRequest(
        client_id="EM-002",
        duty_clinician_id="FAKE-CLINICIAN",
        emergency_reason="No supervisor approval",
        supervisor_approval_code="INVALID-CODE-123",
    )

    success, msg, audit_rec = override_engine.validate_and_execute_override(req, client)
    assert success is False
    assert "REJECTED" in msg
    assert audit_rec is None
