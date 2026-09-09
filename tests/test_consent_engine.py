"""
Unit tests for the Consent & Privacy Enforcement Engine.
"""

import pytest
from src.models.data_models import (
    ClientProfile,
    ConsentMatrix,
    SessionNote,
    RoleEnum,
    ConsentCategory,
)
from src.engine.consent_engine import ConsentEngine


@pytest.fixture
def sample_client():
    return ClientProfile(
        client_id="TEST-001",
        preferred_name="Test Client",
        pronouns="they/them",
        consent_matrix=ConsentMatrix(
            share_trauma_history=False,
            share_medical_diagnosis=True,
            share_social_determinants=True,
            share_substance_history=False,
            allowed_roles=[RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER],
        ),
        session_notes=[
            SessionNote(
                session_id="S-1",
                date="2026-09-01",
                author_role=RoleEnum.COUNSELLOR,
                summary="Client discussed severe childhood trauma and nightmares.",
                sensitive_categories=[ConsentCategory.TRAUMA_HISTORY],
            ),
            SessionNote(
                session_id="S-2",
                date="2026-09-02",
                author_role=RoleEnum.SOCIAL_WORKER,
                summary="Assisted with food bank schedule and utility bill relief grant.",
                sensitive_categories=[ConsentCategory.SOCIAL_DETERMINANTS],
            ),
        ],
    )


def test_consent_engine_redaction(sample_client):
    engine = ConsentEngine(sample_client)
    consented_notes, redacted_notices, audit_trail = engine.filter_session_notes(
        RoleEnum.COUNSELLOR
    )

    # Trauma note (S-1) should trigger redaction
    assert len(redacted_notices) == 1
    assert "S-1" in redacted_notices[0]
    assert "[REDACTED-TRAUMA_HISTORY]" in consented_notes[0]

    # Social determinants note (S-2) should pass
    assert "S-2" in consented_notes[1]
    assert len(audit_trail) >= 2


def test_restricted_role_access(sample_client):
    # Revoke social_worker permission
    sample_client.consent_matrix.allowed_roles = [RoleEnum.COUNSELLOR]
    engine = ConsentEngine(sample_client)

    consented_notes, redacted_notices, audit_trail = engine.filter_session_notes(
        RoleEnum.SOCIAL_WORKER
    )

    assert len(consented_notes) == 0
    assert len(redacted_notices) == 1
    assert "NOT authorized" in redacted_notices[0]
    assert "[AUDIT BLOCK]" in audit_trail[0]
