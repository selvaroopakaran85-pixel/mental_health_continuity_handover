"""
Continuity Summary Synthesis Engine.
Generates baseline (unfiltered dump) and prototype (consent-aware, role-tailored) handover summaries.
"""

from src.models.data_models import (
    ClientProfile,
    HandoverSummary,
    RoleEnum,
)
from src.engine.consent_engine import ConsentEngine
from src.engine.quality_engine import QualityEngine


class SummaryEngine:
    """
    Synthesizes continuity handover summaries for mental health care teams.
    Distinguishes operational care coordination support from medical/clinical advice.
    """

    DISCLAIMER_TEXT = (
        "⚠️ OPERATIONAL & CARE COORDINATION HANDOVER DISCLAIMER ⚠️\n"
        "This continuity summary is designed exclusively to facilitate non-medical care coordination, "
        "social support, and psychological goal tracking. THIS DOCUMENT DOES NOT CONSTITUTE MEDICAL DIAGNOSIS, "
        "CLINICAL PRESCRIPTION, OR PSYCHIATRIC EVALUATION. Clinical staff must consult medical records for "
        "prescriptive authorizations."
    )

    def __init__(self, client: ClientProfile):
        self.client = client
        self.consent_engine = ConsentEngine(client)
        self.quality_engine = QualityEngine(client)

    def generate_baseline_summary(self, target_role: RoleEnum) -> str:
        """
        Generates a simple, un-redacted baseline note dump representing current flawed practice.
        Does NOT respect consent boundaries and mixes clinical/operational details into a raw block.
        """
        lines = [
            f"=== BASELINE HANDOVER (RAW NOTE DUMP) FOR {target_role.value.upper()} ===",
            f"Client: {self.client.preferred_name} ({self.client.client_id})",
            "--- Raw Session Notes (Unfiltered & Un-redacted) ---",
        ]
        for note in self.client.session_notes:
            lines.append(f"• Session {note.session_id} ({note.date or 'No date'}): {note.summary}")

        lines.append("--- Active Goals ---")
        for goal in self.client.active_goals:
            lines.append(f"• [{goal.category}] {goal.title} (Status: {goal.status})")

        lines.append("--- Pending Actions ---")
        for action in self.client.pending_actions:
            lines.append(f"• [{action.assigned_role.value}] {action.description} (Due: {action.due_date})")

        lines.append("\n[Baseline Warning: No privacy redaction applied, no uncertainty flags raised.]")
        return "\n".join(lines)

    def generate_prototype_summary(self, target_role: RoleEnum) -> HandoverSummary:
        """
        Generates a consent-aware, role-tailored continuity handover summary.
        Redacts non-consented sensitive history while preserving active goals and pending tasks.
        """
        # 1. Run Consent Engine
        consented_notes, redacted_notices, audit_trail = (
            self.consent_engine.filter_session_notes(target_role)
        )

        # 2. Run Quality Engine
        uncertainty_flags = self.quality_engine.analyze_quality_and_uncertainty(
            target_role
        )

        # 3. Separate notes into operational vs psychological based on role focus
        operational_notes = []
        psychological_notes = []

        for note_str in consented_notes:
            if target_role == RoleEnum.SOCIAL_WORKER:
                # Filter out pure clinical jargon and emphasize practical/operational context
                operational_notes.append(note_str)
            elif target_role == RoleEnum.COUNSELLOR:
                psychological_notes.append(note_str)
            else:
                operational_notes.append(note_str)

        # 4. Filter goals suitable for target role
        relevant_goals = []
        for g in self.client.active_goals:
            if target_role == RoleEnum.SOCIAL_WORKER and g.category in ["social", "housing", "logistics", "coping"]:
                relevant_goals.append(g)
            elif target_role == RoleEnum.COUNSELLOR and g.category in ["psychological", "coping", "medical"]:
                relevant_goals.append(g)
            else:
                # Include for completeness if un-restricted
                relevant_goals.append(g)

        # 5. Filter pending actions for target role
        relevant_actions = [
            a for a in self.client.pending_actions
            if a.assigned_role == target_role or a.assigned_role == RoleEnum.DUTY_TEAM
        ]

        return HandoverSummary(
            client_id=self.client.client_id,
            client_name=self.client.preferred_name,
            target_role=target_role,
            disclaimer_header=self.DISCLAIMER_TEXT,
            operational_support_notes=operational_notes if target_role == RoleEnum.SOCIAL_WORKER else [],
            psychological_continuity_notes=psychological_notes if target_role == RoleEnum.COUNSELLOR else [],
            redacted_sensitive_topics=redacted_notices,
            active_goals=relevant_goals,
            pending_actions=relevant_actions,
            uncertainty_flags=uncertainty_flags,
            medical_disclaimer_active=True,
            audit_trail=audit_trail,
        )
