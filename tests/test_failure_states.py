"""
Unit tests for Realistic Failure States and Edge Cases.
"""

from src.models.data_models import (
    ClientProfile,
    ConsentMatrix,
    SessionNote,
    RoleEnum,
    ConsentCategory,
)
from src.engine.summary_engine import SummaryEngine


def test_failure_state_1_mid_care_consent_revocation():
    """Client revokes consent for trauma history mid-care flow."""
    client = ClientProfile(
        client_id="FS-1",
        preferred_name="Revocation Client",
        pronouns="they/them",
        consent_matrix=ConsentMatrix(
            share_trauma_history=False,  # Revoked
            allowed_roles=[RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER],
        ),
        session_notes=[
            SessionNote(
                session_id="S-REV1",
                date="2026-08-01",
                author_role=RoleEnum.COUNSELLOR,
                summary="Client discussed historical abuse and trauma.",
                sensitive_categories=[ConsentCategory.TRAUMA_HISTORY],
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.COUNSELLOR)

    # Sensitive history must be redacted
    assert len(summary.redacted_sensitive_topics) == 1
    assert "abuse" not in summary.psychological_continuity_notes[0].lower()
    assert "[REDACTED-TRAUMA_HISTORY]" in summary.psychological_continuity_notes[0]


def test_failure_state_2_low_quality_and_missing_date():
    """Notes with missing timestamp or low quality score surface explicit uncertainty notices."""
    client = ClientProfile(
        client_id="FS-2",
        preferred_name="Fragmented Client",
        pronouns="she/her",
        consent_matrix=ConsentMatrix(allowed_roles=[RoleEnum.COUNSELLOR]),
        session_notes=[
            SessionNote(
                session_id="S-CORRUPT",
                date="",  # Missing date
                author_role=RoleEnum.COUNSELLOR,
                summary="Upset note.",
                quality_score=0.2,  # Low quality
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.COUNSELLOR)

    assert len(summary.uncertainty_flags) >= 2
    issue_types = [f.issue_type for f in summary.uncertainty_flags]
    assert "missing_date" in issue_types
    assert "low_quality_text" in issue_types


def test_failure_state_3_clinical_boundary_leak():
    """Notes containing clinical diagnostic codes are flagged when generating Social Worker view."""
    client = ClientProfile(
        client_id="FS-3",
        preferred_name="Clinical Client",
        pronouns="he/him",
        consent_matrix=ConsentMatrix(
            share_medical_diagnosis=True,
            allowed_roles=[RoleEnum.SOCIAL_WORKER],
        ),
        session_notes=[
            SessionNote(
                session_id="S-CLINICAL",
                date="2026-09-05",
                author_role=RoleEnum.COUNSELLOR,
                summary="Client diagnosed with DSM-5 Bipolar disorder (F31.1), psychiatrist advised quetiapine dosage titration.",
                sensitive_categories=[ConsentCategory.MEDICAL_DIAGNOSIS],
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)

    # Must contain clinical spillover uncertainty flag
    assert any(f.issue_type == "clinical_spillover" for f in summary.uncertainty_flags)
    assert summary.medical_disclaimer_active is True


def test_failure_state_4_restricted_role_access_block():
    """Client consent restricts allowed roles, blocking unauthorized care team access."""
    client = ClientProfile(
        client_id="FS-4",
        preferred_name="Restricted Client",
        pronouns="ze/zir",
        consent_matrix=ConsentMatrix(
            allowed_roles=[RoleEnum.COUNSELLOR]  # Social worker NOT allowed
        ),
        session_notes=[
            SessionNote(
                session_id="S-PRIV",
                date="2026-09-08",
                author_role=RoleEnum.COUNSELLOR,
                summary="Private psychological notes.",
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)

    assert len(summary.operational_support_notes) == 0
    assert any("NOT authorized" in r for r in summary.redacted_sensitive_topics)
