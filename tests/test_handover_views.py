"""
Unit tests for Handover Views and Medical vs Operational Disclaimer enforcement.
"""

from src.models.data_models import (
    ClientProfile,
    ConsentMatrix,
    SessionNote,
    RoleEnum,
    Goal,
    PendingAction,
)
from src.engine.summary_engine import SummaryEngine


def test_handover_view_disclaimer_and_role_goals():
    client = ClientProfile(
        client_id="TEST-002",
        preferred_name="Jordan",
        pronouns="he/him",
        consent_matrix=ConsentMatrix(
            share_trauma_history=True,
            share_medical_diagnosis=True,
            share_social_determinants=True,
            allowed_roles=[RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER],
        ),
        active_goals=[
            Goal(
                id="G1",
                title="Grounding exercises",
                category="coping",
                status="active",
                priority="high",
                assigned_role=RoleEnum.COUNSELLOR,
            ),
            Goal(
                id="G2",
                title="Housing grant application",
                category="housing",
                status="in_progress",
                priority="high",
                assigned_role=RoleEnum.SOCIAL_WORKER,
            ),
        ],
        pending_actions=[
            PendingAction(
                id="A1",
                assigned_role=RoleEnum.SOCIAL_WORKER,
                description="Submit housing application",
                due_date="2026-09-15",
                status="pending",
            )
        ],
        session_notes=[
            SessionNote(
                session_id="S-10",
                date="2026-09-01",
                author_role=RoleEnum.COUNSELLOR,
                summary="Client practicing sensory grounding.",
            )
        ],
    )

    engine = SummaryEngine(client)

    # Social worker summary
    sw_summary = engine.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)
    assert sw_summary.medical_disclaimer_active is True
    assert "DISCLAIMER" in sw_summary.disclaimer_header
    assert any(g.title == "Housing grant application" for g in sw_summary.active_goals)
    assert len(sw_summary.pending_actions) == 1

    # Counsellor summary
    c_summary = engine.generate_prototype_summary(RoleEnum.COUNSELLOR)
    assert c_summary.medical_disclaimer_active is True
    assert any(g.title == "Grounding exercises" for g in c_summary.active_goals)
