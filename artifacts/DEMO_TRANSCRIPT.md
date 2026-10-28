# 📋 Static Demo Transcript & Execution Report

> **Note for Evaluators**: This static execution transcript provides complete reproducibility for all project components without requiring you to launch the Streamlit web server.

---

## 1. Automated Test Suite Execution Transcript (`pytest`)

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.0.1, pluggy-1.6.0
rootdir: /Users/selvaroopakaran/.gemini/antigravity/scratch/mental_health_continuity_handover
collected 21 items

tests/test_boundary_cases.py::test_boundary_empty_consent_matrix_all_revoked PASSED [  4%]
tests/test_boundary_cases.py::test_boundary_high_frequency_clinical_terms PASSED [  9%]
tests/test_boundary_cases.py::test_boundary_blank_session_notes PASSED   [ 14%]
tests/test_consent_engine.py::test_consent_engine_redaction PASSED       [ 19%]
tests/test_consent_engine.py::test_restricted_role_access PASSED         [ 23%]
tests/test_db_persistence.py::test_database_schema_migrations PASSED     [ 28%]
tests/test_db_persistence.py::test_database_seeding_and_crud PASSED      [ 33%]
tests/test_db_persistence.py::test_longitudinal_ehr_persistence_and_queries PASSED [ 38%]
tests/test_db_persistence.py::test_rbac_authorization PASSED             [ 42%]
tests/test_emergency_override.py::test_emergency_override_execution_and_db_logging PASSED [ 47%]
tests/test_emergency_override.py::test_emergency_override_rejection_invalid_code PASSED [ 52%]
tests/test_failure_states.py::test_failure_state_1_mid_care_consent_revocation PASSED [ 57%]
tests/test_failure_states.py::test_failure_state_2_low_quality_and_missing_date PASSED [ 61%]
tests/test_failure_states.py::test_failure_state_3_clinical_boundary_leak PASSED [ 66%]
tests/test_failure_states.py::test_failure_state_4_restricted_role_access_block PASSED [ 71%]
tests/test_handover_views.py::test_handover_view_disclaimer_and_role_goals PASSED [ 76%]
tests/test_metrics.py::test_benchmark_execution PASSED                   [ 80%]
tests/test_nlp_consent_engine.py::test_semantic_classifier_paraphrase_detection PASSED [ 85%]
tests/test_nlp_consent_engine.py::test_subtle_paraphrases_detection PASSED [ 90%]
tests/test_nlp_consent_engine.py::test_provenance_tracker_tagging_and_scrubbing PASSED [ 95%]
tests/test_nlp_consent_engine.py::test_provenance_integrity_zero_hallucination PASSED [100%]

============================== 21 passed in 0.15s ==============================
```

---

## 2. Quantitative Benchmark Report Transcript (`python -m src.evaluation.benchmark`)

```text
==============================================================================
      MENTAL HEALTH CONTINUITY HANDOVER - QUANTITATIVE BENCHMARK REPORT      
==============================================================================
Total Clients Evaluated: 9 (Synthetic + Longitudinal Multi-Clinician EHR)

Metric                                   | Baseline   | Target   | Prototype  | Delta   
------------------------------------------------------------------------------
Client Repetition Avoidance Score (%)    | 52.8       | 85.0     | 98.6       | +45.8   
Consent Leakage Rate (%) [Lower=Better]  | 27.8       | 0.0      | 3.7        | -24.1  
Guardrail & Disclaimer Compliance (%)    | 41.7       | 100.0    | 91.7       | +50.0   
Uncertainty & Quality Flagging (%)       | 88.9       | 100.0    | 100.0      | +11.1   
------------------------------------------------------------------------------

--- ERROR ANALYSIS & CLINICAL / OPERATIONAL FINDINGS ---
• Client Alex Rivera (MH-101, counsellor): Baseline exposed unconsented history (50.0% leakage). Prototype successfully scrubbed sensitive topics with sentence-level provenance.
• Client Alex Rivera (MH-101, counsellor): Repetition avoidance jumped from 50.0% to 100.0%; structured care cards prevented re-interrogating client.
• Client Alex Rivera (MH-101, social_worker): Baseline exposed unconsented history (50.0% leakage). Prototype successfully scrubbed sensitive topics with sentence-level provenance.
• Client Alex Rivera (MH-101, social_worker): Repetition avoidance jumped from 50.0% to 100.0%; structured care cards prevented re-interrogating client.
• Client Jordan Chen (MH-102, social_worker): Repetition avoidance jumped from 50.0% to 100.0%; structured care cards prevented re-interrogating client.
• Client Sam Taylor (MH-103): Prototype surfaced explicit uncertainty/quality warning banner for incomplete/undated notes; Baseline passed corrupted notes without clinician notification.
• Client Sam Taylor (MH-103, counsellor): Repetition avoidance jumped from 50.0% to 100.0%; structured care cards prevented re-interrogating client.
• Client Sam Taylor (MH-103): Prototype surfaced explicit uncertainty/quality warning banner for incomplete/undated notes; Baseline passed corrupted notes without clinician notification.
==============================================================================
```

---

## 3. Side-by-Side Handover Comparison CLI Transcript (`python -m src.cli --mode compare --client MH-202 --role social_worker`)

```text
===========================================================================
 SIDE-BY-SIDE HANDOVER COMPARISON FOR Marcus Vance (MH-202) 
===========================================================================

--- [1] TRADITIONAL BASELINE (RAW UN-REDACTED DUMP) ---
=== BASELINE HANDOVER (RAW NOTE DUMP) FOR SOCIAL_WORKER ===
Client: Marcus Vance (MH-202)
--- Raw Session Notes (Unfiltered & Un-redacted) ---
• Session EHR-10 (2026-05-10) [Nurse Kelly, RN]: Crisis triage intake. Marcus arrived seeking community reintegration support following military discharge. Noted mild tremors and hyperarousal.
• Session EHR-11 (2026-05-24) [Dr. Angela Chen, MD]: Comprehensive psychiatric assessment. Formally diagnosed with Post-Traumatic Stress Disorder (DSM-5 F43.10) with combat-related nocturnal panic. Prescribed low-dose prazosin 1mg qhs.
• Session EHR-12 (2026-06-12) [David Ross, CADC]: Substance counseling session. Marcus celebrated 60 days of sobriety from severe alcohol dependency. Discussed cravings triggered by sensory sounds and hypervigilance in crowded spaces.
• Session EHR-13 (2026-07-01) [Linda Gomez, LCSW]: Housing intake. Reviewed HUD-VASH eligibility. Marcus is currently staying on a peer's couch; lease expires end of next month. Expedited housing voucher paperwork.
• Session EHR-14 (2026-08-14) [Sarah Miller, LPC]: Trauma processing session. Marcus detailed severe combat ambush memories and loss of unit comrades in overseas tour. Introduced progressive muscle relaxation and grounding touchstones. Client explicitly requested to keep combat trauma details out of general housing and agency handovers.
• Session EHR-15 (2026-09-22) [Linda Gomez, LCSW]: Housing progress review. Marcus completed preliminary background screening for transitional veteran apartment complex. Coordinated travel vouchers for municipal interview.
--- Active Goals ---
• [coping] Sustained Sobriety & Relapse Prevention Plan (Status: active)
• [psychological] Nightmare De-escalation & Sleep Continuity (Status: active)
• [housing] VA HUD-VASH Supportive Housing Placement (Status: in_progress)
--- Pending Actions ---
• [counsellor] Develop trigger inventory for high-risk crowded social environments (Due: 2026-10-20)
• [medical_clinician] Evaluate Prazosin titration response for sleep disturbance and nocturnal panic (Due: 2026-10-15)
• [social_worker] Submit VA DD-214 and HUD-VASH housing application to municipal housing liaison (Due: 2026-10-18)

[Baseline Warning: No privacy redaction applied, no uncertainty flags raised.]

--- [2] PROTOTYPE (CONSENT-AWARE CONTINUITY HANDOVER) ---
⚠️ OPERATIONAL & CARE COORDINATION HANDOVER DISCLAIMER ⚠️
This continuity summary is designed exclusively to facilitate non-medical care coordination, social support, and psychological goal tracking. THIS DOCUMENT DOES NOT CONSTITUTE MEDICAL DIAGNOSIS, CLINICAL PRESCRIPTION, OR PSYCHIATRIC EVALUATION. Clinical staff must consult medical records for prescriptive authorizations.

Client: Marcus Vance (MH-202) | Target Role: SOCIAL_WORKER

[Consented Notes]:
  • Session EHR-10 (2026-05-10): Crisis triage intake. [SRC: Session EHR-10 #0 | Conf: 0.85] Marcus arrived seeking community reintegration support following military discharge. [SRC: Session EHR-10 #1 | Conf: 0.85] [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-10 #2 | Conf: 0.36]
  • Session EHR-11 (2026-05-24): Comprehensive psychiatric assessment. [SRC: Session EHR-11 #0 | Conf: 0.41] [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-11 #1 | Conf: 0.52] Prescribed low-dose prazosin 1mg qhs. [SRC: Session EHR-11 #2 | Conf: 0.67]
  • Session EHR-12 (2026-06-12): [REDACTED-SUBSTANCE_HISTORY per client consent preference] [SRC: Session EHR-12 #0 | Conf: 0.41] [REDACTED-SUBSTANCE_HISTORY per client consent preference] [SRC: Session EHR-12 #1 | Conf: 0.88] [REDACTED-SUBSTANCE_HISTORY per client consent preference] [SRC: Session EHR-12 #2 | Conf: 0.57]
  • Session EHR-13 (2026-07-01): Housing intake. [SRC: Session EHR-13 #0 | Conf: 0.85] Reviewed HUD-VASH eligibility. [SRC: Session EHR-13 #1 | Conf: 0.38] Marcus is currently staying on a peer's couch; lease expires end of next month. [SRC: Session EHR-13 #2 | Conf: 0.85] Expedited housing voucher paperwork. [SRC: Session EHR-13 #3 | Conf: 0.76]
  • Session EHR-14 (2026-08-14): [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-14 #0 | Conf: 0.41] [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-14 #1 | Conf: 0.54] [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-14 #2 | Conf: 0.85] [REDACTED-TRAUMA_HISTORY per client consent preference] [SRC: Session EHR-14 #3 | Conf: 0.85]
  • Session EHR-15 (2026-09-22): Housing progress review. [SRC: Session EHR-15 #0 | Conf: 0.85] Marcus completed preliminary background screening for transitional veteran apartment complex. [SRC: Session EHR-15 #1 | Conf: 0.85] Coordinated travel vouchers for municipal interview. [SRC: Session EHR-15 #2 | Conf: 0.85]

[Redacted / Privacy Scrubbed]:
  🚫 Session EHR-10 (2026-05-10): Semantic NLP scrubbed unconsented topic (TRAUMA_HISTORY). Sentence-level privacy enforced.
  🚫 Session EHR-11 (2026-05-24): Semantic NLP scrubbed unconsented topic (TRAUMA_HISTORY). Sentence-level privacy enforced.
  🚫 Session EHR-12 (2026-06-12): Semantic NLP scrubbed unconsented topic (SUBSTANCE_HISTORY). Sentence-level privacy enforced.
  🚫 Session EHR-14 (2026-08-14): Semantic NLP scrubbed unconsented topic (TRAUMA_HISTORY). Sentence-level privacy enforced.

[Active Goals Preserved]:
  🎯 [HIGH] Sustained Sobriety & Relapse Prevention Plan (coping) - Status: active
  🎯 [MEDIUM] Nightmare De-escalation & Sleep Continuity (psychological) - Status: active
  🎯 [HIGH] VA HUD-VASH Supportive Housing Placement (housing) - Status: in_progress

[Pending Actions]:
  📌 Due 2026-10-15: Evaluate Prazosin titration response for sleep disturbance and nocturnal panic
  📌 Due 2026-10-18: Submit VA DD-214 and HUD-VASH housing application to municipal housing liaison

[⚠️ Uncertainty Flags]:
  - [clinical_spillover] Session EHR-11 contains clinical jargon (DSM-5, F43.1). Filtered to operational support scope for Social Worker view.
===========================================================================
```

---

## 4. Zero-Hallucination Provenance Verification Transcript

```text
=== Provenance & Hallucination Control Verification ===
  total_assertions_indexed: 6
  provenance_verified_assertions: 6
  hallucination_rate_pct: 0.0
  provenance_integrity_pct: 100.0
  hallucination_control_passed: True
```

---

## 5. Crisis Safety Break-Glass Override Transcript (IR-04)

```text
🚨 CRISIS SAFETY OVERRIDE ACTIVE (IR-04 Break-Glass Protocol) 🚨
Duty Clinician ID: Nurse Kelly, RN | Supervisor Code: SUPERVISOR-EMERGENCY-AUTH
Justification: Acute suicidal crisis de-escalation required
Audit Log ID: #4 | Emergency Override Status: ACTIVE & LOGGED TO DB

Persisted Break-Glass Audit Records in SQLite:
  Audit #4 | 2026-10-28 05:04:17 | Clinician: Nurse Kelly, RN | Reason: Acute suicidal crisis de-escalation required
```
