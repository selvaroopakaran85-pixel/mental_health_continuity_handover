# Stakeholder Assumptions & Care Model Context

## Overview
This document outlines the operational context, stakeholder requirements, and care coordination assumptions for the **Community Mental-Health Service Consent-Aware Continuity & Handover System**.

---

## 1. Core Problem & Need
In multidisciplinary community mental health teams coordinating **counsellors**, **social workers**, and **duty intake teams**:
- Clients are frequently forced to repeatedly re-tell traumatizing or sensitive histories because handovers between care providers are incomplete or unstructured.
- Raw un-redacted handover note dumps expose sensitive personal history without client consent, violating privacy boundaries.
- Social workers receive irrelevant clinical diagnostic jargon rather than practical, actionable social determinant support needs.
- Counsellors lack structured visibility into active grounding techniques and coping goals established in prior sessions.

---

## 2. Key Stakeholder Groups & Roles

### A. Clients
- **Ownership**: Clients own their personal data and consent choices.
- **Granular Consent**: Clients can grant or revoke consent for specific sensitive data categories (`trauma_history`, `medical_diagnosis`, `social_determinants`, `substance_history`, `third_party_sharing`).
- **Right to Revoke**: Revoking consent immediately redacts sensitive details from future handovers without disrupting active goal continuity or social support actions.

### B. Counsellors
- **Focus**: Psychological continuity, emotional trajectory, therapeutic alliance context, coping mechanisms, and consented trauma boundaries.
- **Responsibility**: Maintain therapeutic safety while respecting client consent preferences.

### C. Social Workers
- **Focus**: Practical needs and social determinants of health (housing stability, food security, benefits application support, legal advocacy, transport logistics).
- **Scope Restriction**: Social workers do not prescribe medication or issue medical diagnoses. Handovers must emphasize operational actions while providing explicit medical disclaimers.

### D. Service Management & Compliance Officers
- **Auditability**: Require explicit audit trail logging whenever data is redacted or access is restricted by client consent matrices.
- **Risk Signaling**: Require low-quality or incomplete session notes to be prominently flagged with uncertainty notices.

---

## 3. Operational vs Medical Segregation Guardrail
- All interfaces and exported handover documents MUST feature explicit, prominent headers demarcating **Operational & Care Coordination Support** from **Medical/Clinical Advice**.
- Clinical diagnostic codes (e.g. DSM-5 / ICD-11) and medication titration instructions are filtered out of general operational summaries.
