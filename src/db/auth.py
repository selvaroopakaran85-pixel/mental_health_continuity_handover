"""
Role-Based Access Control (RBAC) & Authentication Module.
Validates care staff credentials and role permissions against client consent matrices.
"""

from typing import Tuple, Dict, Any
from src.models.data_models import ClientProfile, RoleEnum


DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "counsellor_sarah": {
        "name": "Sarah Miller, MA, LPC",
        "role": RoleEnum.COUNSELLOR,
        "department": "Psychological Services",
    },
    "socialworker_mark": {
        "name": "Mark Davis, MSW",
        "role": RoleEnum.SOCIAL_WORKER,
        "department": "Social Determinants & Housing Support",
    },
    "duty_nurse_kelly": {
        "name": "Nurse Kelly, RN",
        "role": RoleEnum.DUTY_TEAM,
        "department": "24/7 Duty Triage Team",
    },
    "duty_supervisor_dr_smith": {
        "name": "Dr. Smith, MD",
        "role": RoleEnum.MEDICAL_CLINICIAN,
        "department": "Clinical Supervision & Psychiatry",
    },
}


class RBACManager:
    """
    Manages user authentication and enforces Role-Based Access Control (RBAC) rules.
    """

    @staticmethod
    def get_user_profile(user_id: str) -> Dict[str, Any]:
        return DEMO_USERS.get(
            user_id,
            {
                "name": "Guest Clinician",
                "role": RoleEnum.SOCIAL_WORKER,
                "department": "General Care Support",
            },
        )

    @staticmethod
    def validate_role_access(
        user_role: RoleEnum, client: ClientProfile
    ) -> Tuple[bool, str]:
        """
        Validates if the user role is authorized by the client's consent matrix.
        """
        allowed_roles = client.consent_matrix.allowed_roles

        if user_role in allowed_roles:
            return True, f"Access granted for role '{user_role.value}' per client consent matrix."
        
        # Medical clinicians have oversight for clinical emergency escalation
        if user_role == RoleEnum.MEDICAL_CLINICIAN:
            return True, "Access granted under Clinical Supervisor oversight authorization."

        return (
            False,
            f"Access RESTRICTED: Role '{user_role.value}' is not in client's allowed sharing list "
            f"({[r.value for r in allowed_roles]}).",
        )
