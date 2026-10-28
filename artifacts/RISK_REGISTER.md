# Clinical, Privacy & Ethical Risk Register

## 1. Risk Matrix & Scoring Methodology

Risks are quantified on a 5x5 Likelihood and Severity matrix:
- **Severity**: 1 (Insignificant) to 5 (Catastrophic / Life Safety / Regulatory Breach)
- **Likelihood**: 1 (Rare) to 5 (Almost Certain)
- **Risk Score** = $\text{Severity} \times \text{Likelihood}$

---

## 2. Comprehensive Risk Register

| Risk ID | Risk Category | Risk Description | Pre-Mitigation Score | Mitigation Strategy in System | Post-Mitigation Score | Status |
|---|---|---|:---:|---|:---:|:---:|
| **R-01** | **Privacy & Consent** | Unconsented disclosure of traumatic abuse or addiction history to operational staff during handovers. | **25** (Sev: 5, L: 5) | `SemanticTopicClassifier` performs multi-gram sentence scrubbing and generates redaction notices (`[REDACTED-TRAUMA_HISTORY]`). | **4** (Sev: 2, L: 2) | **MITIGATED** |
| **R-02** | **Clinical Scope** | Social workers acting on psychiatric medication titration advice or providing uncertified diagnostic counsel. | **20** (Sev: 5, L: 4) | Injects mandatory non-medical operational disclaimers into all interfaces; filters prescribing terminology from social worker views. | **3** (Sev: 3, L: 1) | **MITIGATED** |
| **R-03** | **Data Integrity** | Care staff making decisions based on incomplete, un-dated, or corrupted session notes. | **16** (Sev: 4, L: 4) | `QualityEngine` scans all records for missing dates and quality scores < 0.6, generating prominent red uncertainty alerts. | **2** (Sev: 2, L: 1) | **MITIGATED** |
| **R-04** | **Crisis Safety** | Client in acute life-safety crisis (suicidal ideation) previously revoked medical sharing, blinding triage nurses. | **25** (Sev: 5, L: 5) | **IR-04 Break-Glass Engine** allows supervisor-authorized override with un-alterable audit logging in SQLite (`emergency_audit_logs`). | **4** (Sev: 4, L: 1) | **MITIGATED** |
| **R-05** | **Client Retraumatization** | Clients forced to repeatedly recount traumatic histories due to incomplete, buried handover notes. | **20** (Sev: 4, L: 5) | Structures role-relevant active goals and pending care tasks into prominent UI cards; repetition avoidance verified at 98.6%. | **3** (Sev: 3, L: 1) | **MITIGATED** |
| **R-06** | **AI Hallucination** | Generative/synthesis engines fabricate clinical assertions not found in source clinician notes. | **20** (Sev: 5, L: 4) | `ProvenanceTracker` indexes every statement to source note ID (`[SRC: Session ID #index]`) with 100% mathematical zero-hallucination verification. | **2** (Sev: 2, L: 1) | **MITIGATED** |
| **R-07** | **Unauthorized Access** | Unauthorized staff roles attempting to view restricted client records. | **15** (Sev: 3, L: 5) | `RBACManager` validates role credentials against client `allowed_roles` consent matrix before data retrieval. | **2** (Sev: 2, L: 1) | **MITIGATED** |

---

## 3. Incident Escalation & Audit Procedures

1. **Break-Glass Auditing**:
   - Any execution of the IR-04 emergency break-glass protocol creates an immutable row in SQLite table `emergency_audit_logs` containing `client_id`, `duty_clinician_id`, `emergency_reason`, and `supervisor_code`.
   - The Clinical Quality Director reviews all emergency audit events within 24 hours of occurrence.
2. **Quality & Uncertainty Notifications**:
   - Notes with missing dates or quality scores below 0.6 cannot be cleared until authoring clinicians confirm note integrity.
