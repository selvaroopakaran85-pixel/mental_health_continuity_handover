"""
Consent & Privacy Enforcement Engine.
Handles deterministic redaction, scope checks, and audit logging based on client consent choices.
"""

import re
from typing import List, Tuple
from src.models.data_models import (
    ClientProfile,
    SessionNote,
    RoleEnum,
    ConsentCategory,
)


class ConsentEngine:
    """
    Enforces privacy rules, redacts sensitive topics based on client consent choices,
    and maintains an explicit consent audit trail.
    """

    SENSITIVE_PATTERNS = {
        ConsentCategory.TRAUMA_HISTORY: [
            r"\b(trauma|abuse|assault|ptsd|flashback|domestic violence|neglect|childhood trauma|nightmares)\b",
            r"\b(childhood experience|traumatic event)\b",
        ],
        ConsentCategory.MEDICAL_DIAGNOSIS: [
            r"\b(bipolar|schizophrenia|dsm-5|icd-11|medication|dosage|psychiatrist|prescription|sertraline|fluoxetine|quetiapine)\b",
            r"\b(clinical diagnosis|psychiatric evaluation|pharmacotherapy)\b",
        ],
        ConsentCategory.SUBSTANCE_HISTORY: [
            r"\b(substance|alcohol|addiction|overdose|detox|rehab|opioid|cannabis|withdrawal)\b",
        ],
        ConsentCategory.SOCIAL_DETERMINANTS: [
            r"\b(eviction|homelessness|food bank|unemployment|debt|welfare|court date|legal dispute)\b",
        ],
    }

    def __init__(self, client: ClientProfile):
        self.client = client
        self.consent_matrix = client.consent_matrix

    def filter_session_notes(
        self, target_role: RoleEnum
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Filters session notes for the target role.
        Returns: (consented_notes, redacted_notices, audit_trail)
        """
        consented_notes = []
        redacted_notices = []
        audit_trail = []

        # Check basic role permission
        if target_role not in self.consent_matrix.allowed_roles:
            msg = f"Role '{target_role.value}' is NOT authorized by client consent matrix."
            audit_trail.append(f"[AUDIT BLOCK] {msg}")
            redacted_notices.append(f"[ACCESS RESTRICTED: {msg}]")
            return [], redacted_notices, audit_trail

        for note in self.client.session_notes:
            note_audit = []
            is_redacted = False
            processed_summary = note.summary

            # 1. Check explicit tagged sensitive categories
            for category in note.sensitive_categories:
                if not self.consent_matrix.is_category_consented(category.value):
                    is_redacted = True
                    note_audit.append(
                        f"Category '{category.value}' not consented -> Redact."
                    )
                    # Scrub patterns for this category
                    patterns = self.SENSITIVE_PATTERNS.get(category, [])
                    for pat in patterns:
                        processed_summary = re.sub(
                            pat,
                            f"[REDACTED-{category.value.upper()}]",
                            processed_summary,
                            flags=re.IGNORECASE,
                        )

            # 2. Check keyword pattern matches for unconsented categories
            for cat_enum, patterns in self.SENSITIVE_PATTERNS.items():
                if not self.consent_matrix.is_category_consented(cat_enum.value):
                    for pattern in patterns:
                        if re.search(pattern, processed_summary, re.IGNORECASE):
                            is_redacted = True
                            note_audit.append(
                                f"Detected pattern '{cat_enum.value}' in text without consent -> Redact."
                            )
                            processed_summary = re.sub(
                                pattern,
                                f"[REDACTED-{cat_enum.value.upper()}]",
                                processed_summary,
                                flags=re.IGNORECASE,
                            )

            # Log audit and decide output
            if is_redacted:
                redacted_notice = (
                    f"Session {note.session_id} ({note.date or 'Unknown Date'}): "
                    f"Sensitive details redacted per client consent settings."
                )
                redacted_notices.append(redacted_notice)
                audit_trail.append(f"[AUDIT REDACT] Session {note.session_id}: {'; '.join(set(note_audit))}")
                
                sanitized_entry = (
                    f"[Sanitized Note - Session {note.session_id}]: {processed_summary}"
                )
                consented_notes.append(sanitized_entry)
            else:
                audit_trail.append(
                    f"[AUDIT PASS] Session {note.session_id}: Consented for role '{target_role.value}'."
                )
                consented_notes.append(
                    f"Session {note.session_id} ({note.date or 'N/A'}) [{note.author_role.value}]: {note.summary}"
                )

        return consented_notes, redacted_notices, audit_trail
