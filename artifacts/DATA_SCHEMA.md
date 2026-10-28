# Data Schemas & Database Specifications

## 1. Relational SQLite Database Schema (DDL)

```sql
-- Schema Version Migrations Table
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Core Client Records
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    preferred_name TEXT NOT NULL,
    pronouns TEXT NOT NULL
);

-- Granular Client Consent Preferences
CREATE TABLE consent_matrices (
    client_id TEXT PRIMARY KEY,
    share_trauma_history INTEGER NOT NULL,
    share_medical_diagnosis INTEGER NOT NULL,
    share_social_determinants INTEGER NOT NULL,
    share_substance_history INTEGER NOT NULL,
    share_third_party INTEGER NOT NULL,
    allowed_roles TEXT NOT NULL,  -- JSON Array: ["counsellor", "social_worker", ...]
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

-- Longitudinal Multi-Clinician Session Notes
CREATE TABLE session_notes (
    session_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    date TEXT,
    author_role TEXT NOT NULL,    -- counsellor | social_worker | duty_team | medical_clinician
    author_name TEXT DEFAULT 'Staff Clinician',
    summary TEXT NOT NULL,
    sensitive_categories TEXT NOT NULL, -- JSON Array
    risk_level TEXT DEFAULT 'low',
    quality_score REAL DEFAULT 1.0,
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

-- Care Continuity Active Goals
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,       -- psychological | social | housing | coping | medical
    status TEXT NOT NULL,         -- active | in_progress | completed | blocked
    priority TEXT NOT NULL,       -- high | medium | low
    assigned_role TEXT NOT NULL,  -- counsellor | social_worker | duty_team | medical_clinician
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

-- Pending Action Tasks Across Care Team
CREATE TABLE pending_actions (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    assigned_role TEXT NOT NULL,
    description TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL,         -- pending | in_progress | completed
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

-- Immutable Emergency Break-Glass Audit Logs
CREATE TABLE emergency_audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    client_id TEXT NOT NULL,
    duty_clinician_id TEXT NOT NULL,
    emergency_reason TEXT NOT NULL,
    supervisor_code TEXT NOT NULL,
    actions_accessed TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (client_id)
);

-- Clinician Users & RBAC Roles
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL
);

-- B-Tree Performance Indexes
CREATE INDEX idx_session_notes_client_date ON session_notes (client_id, date);
CREATE INDEX idx_goals_client_status ON goals (client_id, status);
CREATE INDEX idx_actions_client_role ON pending_actions (client_id, assigned_role);
CREATE INDEX idx_audit_logs_client ON emergency_audit_logs (client_id);
```

---

## 2. Pydantic Python Domain Models

```python
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
    allowed_roles: List[RoleEnum] = Field(default_factory=lambda: [RoleEnum.COUNSELLOR, RoleEnum.SOCIAL_WORKER])

class SessionNote(BaseModel):
    session_id: str
    date: Optional[str] = None
    author_role: RoleEnum
    author_name: Optional[str] = "Staff Clinician"
    summary: str
    sensitive_categories: List[ConsentCategory] = Field(default_factory=list)
    risk_level: str = "low"
    quality_score: float = 1.0
    clinical_jargon_present: bool = False

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
```

---

## 3. Longitudinal Multi-Clinician Sample Payload

```json
{
  "client_id": "MH-202",
  "preferred_name": "Marcus Vance",
  "pronouns": "he/him",
  "consent_matrix": {
    "share_trauma_history": false,
    "share_medical_diagnosis": true,
    "share_social_determinants": true,
    "share_substance_history": false,
    "share_third_party": false,
    "allowed_roles": ["counsellor", "social_worker", "duty_team", "medical_clinician"]
  },
  "active_goals": [
    {
      "id": "G-210",
      "title": "Sustained Sobriety & Relapse Prevention Plan",
      "category": "coping",
      "status": "active",
      "priority": "high",
      "assigned_role": "counsellor"
    },
    {
      "id": "G-211",
      "title": "VA HUD-VASH Supportive Housing Placement",
      "category": "housing",
      "status": "in_progress",
      "priority": "high",
      "assigned_role": "social_worker"
    }
  ],
  "session_notes": [
    {
      "session_id": "EHR-11",
      "date": "2026-05-24",
      "author_role": "medical_clinician",
      "author_name": "Dr. Angela Chen, MD",
      "summary": "Psychiatric assessment. Formally diagnosed with PTSD (DSM-5 F43.10) with combat-related nocturnal panic. Prescribed low-dose prazosin 1mg.",
      "sensitive_categories": ["medical_diagnosis"],
      "risk_level": "moderate",
      "quality_score": 0.96
    },
    {
      "session_id": "EHR-12",
      "date": "2026-06-12",
      "author_role": "counsellor",
      "author_name": "David Ross, CADC",
      "summary": "Substance counseling session. Marcus celebrated 60 days of sobriety from severe alcohol dependency.",
      "sensitive_categories": ["substance_history"],
      "risk_level": "moderate",
      "quality_score": 0.93
    }
  ]
}
```
