"""
Data models for the Consent-Aware Continuity Summary System.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class RoleEnum(str, Enum):
    COUNSELLOR = "counsellor"
    SOCIAL_WORKER = "social_worker"
    DUTY_TEAM = "duty_team"
    MEDICAL_CLINICIAN = "medical_clinician"


class ConsentCategory(str, Enum):
    TRAUMA_HISTORY = "trauma_history"
    MEDICAL_DIAGNOSIS = "medical_diagnosis"
    SOCIAL_DETERMINANTS = "social_determinants"
    SUBSTANCE_HISTORY = "substance_history"
    THIRD_PARTY_SHARING = "third_party_sharing"


class ConsentMatrix(BaseModel):
    share_trauma_history: bool = False
    share_medical_diagnosis: bool = True
    share_social_determinants: bool = True
    share_substance_history: bool = False
    share_third_party: bool = False
    allowed_roles: List[RoleEnum] = Field(
        default_factory=lambda: [RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER]
    )

    def is_category_consented(self, category: str) -> bool:
        category_map = {
            ConsentCategory.TRAUMA_HISTORY.value: self.share_trauma_history,
            ConsentCategory.MEDICAL_DIAGNOSIS.value: self.share_medical_diagnosis,
            ConsentCategory.SOCIAL_DETERMINANTS.value: self.share_social_determinants,
            ConsentCategory.SUBSTANCE_HISTORY.value: self.share_substance_history,
            ConsentCategory.THIRD_PARTY_SHARING.value: self.share_third_party,
        }
        return category_map.get(category, False)


class Goal(BaseModel):
    id: str
    title: str
    category: str  # psychological, social, housing, coping, medical
    status: str  # active, in_progress, completed, blocked
    priority: str  # high, medium, low
    assigned_role: RoleEnum


class PendingAction(BaseModel):
    id: str
    assigned_role: RoleEnum
    description: str
    due_date: str
    status: str  # pending, in_progress, completed


class SessionNote(BaseModel):
    session_id: str
    date: Optional[str] = None
    author_role: RoleEnum
    summary: str
    sensitive_categories: List[ConsentCategory] = Field(default_factory=list)
    risk_level: str = "low"  # low, moderate, high, crisis
    quality_score: float = 1.0  # 0.0 to 1.0
    clinical_jargon_present: bool = False


class UncertaintyNotice(BaseModel):
    session_id: str
    issue_type: str  # missing_date, low_quality_text, contradictory_goal, clinical_spillover
    description: str
    severity: str  # warning, error, info


class ClientProfile(BaseModel):
    client_id: str
    preferred_name: str
    pronouns: str
    consent_matrix: ConsentMatrix
    active_goals: List[Goal] = Field(default_factory=list)
    pending_actions: List[PendingAction] = Field(default_factory=list)
    session_notes: List[SessionNote] = Field(default_factory=list)


class HandoverSummary(BaseModel):
    client_id: str
    client_name: str
    target_role: RoleEnum
    disclaimer_header: str
    operational_support_notes: List[str] = Field(default_factory=list)
    psychological_continuity_notes: List[str] = Field(default_factory=list)
    redacted_sensitive_topics: List[str] = Field(default_factory=list)
    active_goals: List[Goal] = Field(default_factory=list)
    pending_actions: List[PendingAction] = Field(default_factory=list)
    uncertainty_flags: List[UncertaintyNotice] = Field(default_factory=list)
    medical_disclaimer_active: bool = True
    audit_trail: List[str] = Field(default_factory=list)
