"""
Uncertainty & Quality Detection Engine.
Identifies low-quality notes, missing metadata, clinical spillover, and goal contradictions.
"""

from typing import List
from src.models.data_models import (
    ClientProfile,
    UncertaintyNotice,
    RoleEnum,
)


class QualityEngine:
    """
    Analyzes client data for metadata gaps, low-quality notes, clinical scope leaks,
    and goal status inconsistencies to surface explicit uncertainty flags to care staff.
    """

    CLINICAL_CODE_PATTERNS = [
        "DSM-5", "ICD-10", "ICD-11", "F32.9", "F41.1", "F43.1",
        "pharmacotherapy", "dosage", "titration", "antipsychotic", "SSRI"
    ]

    def __init__(self, client: ClientProfile):
        self.client = client

    def analyze_quality_and_uncertainty(
        self, target_role: RoleEnum
    ) -> List[UncertaintyNotice]:
        flags: List[UncertaintyNotice] = []

        # 1. Inspect session notes quality
        for note in self.client.session_notes:
            # Check missing date
            if not note.date or note.date.strip() == "":
                flags.append(
                    UncertaintyNotice(
                        session_id=note.session_id,
                        issue_type="missing_date",
                        description=f"Session {note.session_id} has no valid timestamp. Chronological order unverified.",
                        severity="warning",
                    )
                )

            # Check low quality score / truncated notes
            if note.quality_score < 0.6 or len(note.summary.strip()) < 20:
                flags.append(
                    UncertaintyNotice(
                        session_id=note.session_id,
                        issue_type="low_quality_text",
                        description=f"Session {note.session_id} contains fragmented or short notes (quality score: {note.quality_score}). Re-confirm details with client.",
                        severity="warning",
                    )
                )

            # Check clinical scope spillover for Social Worker
            if target_role == RoleEnum.SOCIAL_WORKER:
                found_clinical = [
                    pat for pat in self.CLINICAL_CODE_PATTERNS
                    if pat.lower() in note.summary.lower()
                ]
                if found_clinical:
                    flags.append(
                        UncertaintyNotice(
                            session_id=note.session_id,
                            issue_type="clinical_spillover",
                            description=(
                                f"Session {note.session_id} contains clinical jargon ({', '.join(found_clinical)}). "
                                f"Filtered to operational support scope for Social Worker view."
                            ),
                            severity="info",
                        )
                    )

        # 2. Inspect active goals consistency
        goal_categories = [g.category.lower() for g in self.client.active_goals]
        if "psychological" in goal_categories and "housing" in goal_categories:
            # Informational check for holistic care alignment
            pass

        for goal in self.client.active_goals:
            if goal.status == "blocked":
                flags.append(
                    UncertaintyNotice(
                        session_id="GOAL_AUDIT",
                        issue_type="contradictory_goal",
                        description=f"Goal '{goal.title}' is currently BLOCKED. Operational review required.",
                        severity="warning",
                    )
                )

        # 3. Check orphaned pending actions
        for action in self.client.pending_actions:
            if not action.description or len(action.description) < 5:
                flags.append(
                    UncertaintyNotice(
                        session_id="ACTION_AUDIT",
                        issue_type="missing_action_detail",
                        description=f"Action '{action.id}' has underspecified instructions.",
                        severity="warning",
                    )
                )

        return flags
