"""
Continuity Summary Synthesis Engine.
Generates baseline (unfiltered dump) and prototype (consent-aware, role-tailored) handover summaries
integrated with Semantic NLP, Provenance Tracking, and Crisis Break-Glass Overrides.
"""

from typing import Optional
from src.models.data_models import (
    ClientProfile,
    HandoverSummary,
    RoleEnum,
)
from src.engine.consent_engine import ConsentEngine
from src.engine.nlp_consent_engine import ProvenanceTracker
from src.engine.emergency_override import EmergencyOverrideEngine, EmergencyOverrideRequest
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
        self.provenance_tracker = ProvenanceTracker()
        self.emergency_engine = EmergencyOverrideEngine()
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
            author_info = getattr(note, "author_name", note.author_role.value)
            lines.append(
                f"• Session {note.session_id} ({note.date or 'No date'}) [{author_info}]: {note.summary}"
            )

        lines.append("--- Active Goals ---")
        for goal in self.client.active_goals:
            lines.append(f"• [{goal.category}] {goal.title} (Status: {goal.status})")

        lines.append("--- Pending Actions ---")
        for action in self.client.pending_actions:
            lines.append(f"• [{action.assigned_role.value}] {action.description} (Due: {action.due_date})")

        lines.append("\n[Baseline Warning: No privacy redaction applied, no uncertainty flags raised.]")
        return "\n".join(lines)

    def generate_prototype_summary(
        self,
        target_role: RoleEnum,
        emergency_request: Optional[EmergencyOverrideRequest] = None,
    ) -> HandoverSummary:
        """
        Generates a consent-aware, role-tailored continuity handover summary with provenance tracking.
        If emergency_request is provided, executes break-glass consent override with audit logging.
        """
        # Check basic role permissions
        if target_role not in self.client.consent_matrix.allowed_roles and not emergency_request:
            msg = f"Role '{target_role.value}' is NOT authorized by client consent matrix."
            return HandoverSummary(
                client_id=self.client.client_id,
                client_name=self.client.preferred_name,
                target_role=target_role,
                disclaimer_header=self.DISCLAIMER_TEXT,
                operational_support_notes=[],
                psychological_continuity_notes=[],
                redacted_sensitive_topics=[f"[ACCESS RESTRICTED: {msg}]"],
                active_goals=[],
                pending_actions=[],
                uncertainty_flags=[],
                medical_disclaimer_active=True,
                audit_trail=[f"[AUDIT BLOCK] {msg}"],
            )

        # 1. Handle Crisis Safety Override (IR-04)
        override_active = False
        override_audit_id = 0
        if emergency_request:
            success, msg, audit_rec = self.emergency_engine.validate_and_execute_override(
                emergency_request, self.client
            )
            if success and audit_rec:
                override_active = True
                override_audit_id = audit_rec["log_id"]

        # 2. Run Semantic NLP Consent Engine with Provenance Tracking
        if override_active:
            consented_notes = [
                f"Session {n.session_id} ({n.date or 'N/A'}) [{n.author_role.value}]: {n.summary} [SRC: Session {n.session_id} #UNSCRUBBED]"
                for n in self.client.session_notes
            ]
            redacted_notices = ["[BREAK-GLASS OVERRIDE ACTIVE: All session details accessible for crisis team]"]
            audit_trail = [f"[AUDIT BREAK-GLASS] Emergency override active by clinician {emergency_request.duty_clinician_id}"]
        else:
            consented_notes, redacted_notices, provenance_recs = (
                self.provenance_tracker.process_and_redact_notes(
                    self.client.session_notes, self.client.consent_matrix
                )
            )
            audit_trail = [
                f"[AUDIT PROVENANCE] Indexed {len(provenance_recs)} sentences across {len(self.client.session_notes)} session notes."
            ]

        # 3. Run Quality Engine for Uncertainty Flagging
        uncertainty_flags = self.quality_engine.analyze_quality_and_uncertainty(target_role)

        # 4. Filter notes by role focus
        operational_notes = []
        psychological_notes = []

        for note_str in consented_notes:
            if target_role == RoleEnum.SOCIAL_WORKER:
                operational_notes.append(note_str)
            elif target_role == RoleEnum.COUNSELLOR:
                psychological_notes.append(note_str)
            else:
                operational_notes.append(note_str)

        # 5. Filter goals suitable for target role
        relevant_goals = []
        for g in self.client.active_goals:
            if target_role == RoleEnum.SOCIAL_WORKER and g.category in ["social", "housing", "logistics", "coping"]:
                relevant_goals.append(g)
            elif target_role == RoleEnum.COUNSELLOR and g.category in ["psychological", "coping", "medical"]:
                relevant_goals.append(g)
            else:
                relevant_goals.append(g)

        # 6. Filter pending actions for target role
        relevant_actions = [
            a for a in self.client.pending_actions
            if a.assigned_role in [target_role, RoleEnum.DUTY_TEAM, RoleEnum.MEDICAL_CLINICIAN]
        ]

        summary = HandoverSummary(
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

        if override_active and emergency_request:
            summary = self.emergency_engine.apply_override_to_summary(
                summary, emergency_request, override_audit_id
            )

        return summary
