# Data Schemas Specification

## 1. Client Profile Schema

```json
{
  "client_id": "STRING (e.g. MH-101)",
  "preferred_name": "STRING",
  "pronouns": "STRING",
  "consent_matrix": {
    "share_trauma_history": "BOOLEAN",
    "share_medical_diagnosis": "BOOLEAN",
    "share_social_determinants": "BOOLEAN",
    "share_substance_history": "BOOLEAN",
    "share_third_party": "BOOLEAN",
    "allowed_roles": ["counsellor", "social_worker", "duty_team"]
  },
  "active_goals": [
    {
      "id": "STRING",
      "title": "STRING",
      "category": "psychological | social | housing | coping | medical",
      "status": "active | in_progress | completed | blocked",
      "priority": "high | medium | low",
      "assigned_role": "counsellor | social_worker | duty_team"
    }
  ],
  "pending_actions": [
    {
      "id": "STRING",
      "assigned_role": "counsellor | social_worker | duty_team",
      "description": "STRING",
      "due_date": "STRING (YYYY-MM-DD)",
      "status": "pending | in_progress | completed"
    }
  ],
  "session_notes": [
    {
      "session_id": "STRING",
      "date": "STRING (YYYY-MM-DD)",
      "author_role": "counsellor | social_worker",
      "summary": "STRING",
      "sensitive_categories": ["trauma_history", "medical_diagnosis", "social_determinants", "substance_history"],
      "risk_level": "low | moderate | high | crisis",
      "quality_score": "FLOAT (0.0 to 1.0)"
    }
  ]
}
```

---

## 2. Handover Summary Schema (Output)

```json
{
  "client_id": "STRING",
  "client_name": "STRING",
  "target_role": "counsellor | social_worker",
  "disclaimer_header": "STRING",
  "operational_support_notes": ["ARRAY OF STRINGS"],
  "psychological_continuity_notes": ["ARRAY OF STRINGS"],
  "redacted_sensitive_topics": ["ARRAY OF STRINGS"],
  "active_goals": ["ARRAY OF GOALS"],
  "pending_actions": ["ARRAY OF PENDING ACTIONS"],
  "uncertainty_flags": [
    {
      "session_id": "STRING",
      "issue_type": "missing_date | low_quality_text | contradictory_goal | clinical_spillover",
      "description": "STRING",
      "severity": "warning | error | info"
    }
  ],
  "medical_disclaimer_active": "BOOLEAN",
  "audit_trail": ["ARRAY OF AUDIT LOG STRINGS"]
}
```
