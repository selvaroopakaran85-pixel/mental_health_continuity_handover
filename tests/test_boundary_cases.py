"""
Unit tests for Boundary and Negative Edge Cases.
Coverage: Empty consent matrix, total revocation, high-frequency clinical terms, blank notes.
"""

from src.models.data_models import (
    ClientProfile,
    ConsentMatrix,
    SessionNote,
    RoleEnum,
)
from src.engine.summary_engine import SummaryEngine


def test_boundary_empty_consent_matrix_all_revoked():
    """Client revokes ALL consent sharing flags."""
    client = ClientProfile(
        client_id="BND-01",
        preferred_name="Total Revocation Client",
        pronouns="they/them",
        consent_matrix=ConsentMatrix(
            share_trauma_history=False,
            share_medical_diagnosis=False,
            share_social_determinants=False,
            share_substance_history=False,
            share_third_party=False,
            allowed_roles=[RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER],
        ),
        session_notes=[
            SessionNote(
                session_id="S-B1",
                date="2026-10-01",
                author_role=RoleEnum.COUNSELLOR,
                summary="Client discussed trauma, bipolar diagnosis, substance detox, and eviction threat.",
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)

    # All sensitive topics must be redacted
    assert len(summary.redacted_sensitive_topics) >= 1
    assert "bipolar" not in str(summary.operational_support_notes).lower()
    assert "eviction" not in str(summary.operational_support_notes).lower()


def test_boundary_high_frequency_clinical_terms():
    """Session note filled with dense clinical diagnostic jargon."""
    client = ClientProfile(
        client_id="BND-02",
        preferred_name="Dense Jargon Client",
        pronouns="she/her",
        consent_matrix=ConsentMatrix(
            share_medical_diagnosis=True,
            allowed_roles=[RoleEnum.SOCIAL_WORKER],
        ),
        session_notes=[
            SessionNote(
                session_id="S-JARGON",
                date="2026-10-02",
                author_role=RoleEnum.MEDICAL_CLINICIAN,
                summary="F31.1 Bipolar I disorder, current episode manic without psychotic features. Pharmacotherapy titration of quetiapine 200mg and lithium carbonate.",
            )
        ],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)

    # Clinical spillover flag must be present
    assert any(f.issue_type == "clinical_spillover" for f in summary.uncertainty_flags)
    assert summary.medical_disclaimer_active is True


def test_boundary_blank_session_notes():
    """Client profile with empty/blank session notes."""
    client = ClientProfile(
        client_id="BND-03",
        preferred_name="Blank Client",
        pronouns="he/him",
        consent_matrix=ConsentMatrix(),
        session_notes=[],
    )
    engine = SummaryEngine(client)
    summary = engine.generate_prototype_summary(RoleEnum.COUNSELLOR)

    assert len(summary.psychological_continuity_notes) == 0
    assert len(summary.redacted_sensitive_topics) == 0
    assert summary.medical_disclaimer_active is True
