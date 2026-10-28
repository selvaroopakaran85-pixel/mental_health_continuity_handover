"""
Crisis & Emergency Consent Override Protocol (IR-04 Break-Glass Engine).
Allows authorized duty clinicians to override client consent restrictions during active life-safety emergencies,
recording un-alterable audit logs into SQLite and injecting crisis banners into handovers.
"""

from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
from src.models.data_models import ClientProfile, HandoverSummary, RoleEnum
from src.db.database import DatabaseManager


VALID_SUPERVISOR_CODES = {
    "SUPERVISOR-EMERGENCY-AUTH",
    "SAFE-OVERRIDE-99",
    "CLINICAL-DIRECTOR-PASS",
}


@dataclass
class EmergencyOverrideRequest:
    client_id: str
    duty_clinician_id: str
    emergency_reason: str
    supervisor_approval_code: str


class EmergencyOverrideEngine:
    """
    Executes break-glass consent overrides during acute crisis de-escalation,
    logging audit trails to SQLite database.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def validate_and_execute_override(
        self, request: EmergencyOverrideRequest, client: ClientProfile
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates supervisor code and executes break-glass consent override.
        Returns: (success, message, audit_record)
        """
        # 1. Validate clinician ID
        if not request.duty_clinician_id or not request.duty_clinician_id.strip():
            return (
                False,
                "Emergency Override REJECTED: Duty clinician ID is required.",
                None,
            )

        # 2. Validate supervisor code
        if request.supervisor_approval_code not in VALID_SUPERVISOR_CODES:
            return (
                False,
                f"Emergency Override REJECTED: Invalid supervisor code '{request.supervisor_approval_code}'.",
                None,
            )

        # 3. Check emergency reason justification length
        if len(request.emergency_reason.strip()) < 10:
            return (
                False,
                "Emergency Override REJECTED: Justification reason must be at least 10 characters long.",
                None,
            )

        # 3. Log break-glass event to SQLite database
        log_id = self.db_manager.log_emergency_override(
            client_id=client.client_id,
            duty_clinician_id=request.duty_clinician_id,
            emergency_reason=request.emergency_reason,
            supervisor_code=request.supervisor_approval_code,
            actions_accessed="BREAK_GLASS_FULL_RECORD_UNSCRUBBED",
        )

        audit_record = {
            "log_id": log_id,
            "client_id": client.client_id,
            "duty_clinician_id": request.duty_clinician_id,
            "emergency_reason": request.emergency_reason,
            "supervisor_code": request.supervisor_approval_code,
            "status": "APPROVED_AND_LOGGED",
        }

        return (
            True,
            f"CRISIS SAFETY OVERRIDE APPROVED (Audit Log #{log_id}). Full record access granted for duty team.",
            audit_record,
        )

    def apply_override_to_summary(
        self, summary: HandoverSummary, request: EmergencyOverrideRequest, audit_id: int
    ) -> HandoverSummary:
        """
        Applies crisis safety banners and restores un-scrubbed context for duty team review.
        """
        crisis_banner = (
            f"🚨 CRISIS SAFETY OVERRIDE ACTIVE (IR-04 Break-Glass Protocol) 🚨\n"
            f"Duty Clinician ID: {request.duty_clinician_id} | Supervisor Code: {request.supervisor_approval_code}\n"
            f"Justification: {request.emergency_reason}\n"
            f"Audit Log ID: #{audit_id} | Emergency Override Status: ACTIVE & LOGGED TO DB"
        )
        summary.disclaimer_header = crisis_banner + "\n\n" + summary.disclaimer_header
        summary.audit_trail.insert(
            0, f"[CRISIS BREAK-GLASS OVERRIDE] Clinician '{request.duty_clinician_id}' accessed un-scrubbed record. Reason: {request.emergency_reason}"
        )
        return summary
