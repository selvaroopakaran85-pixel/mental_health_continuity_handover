# Technical Architecture & Component Topology

## 1. System Overview
The **Consent-Aware Mental Health Continuity Summary System** is built on a modular, privacy-first Python and SQLite architecture. It decouples privacy enforcement, clinical scope boundary guardrails, and uncertainty detection from presentation logic to ensure deterministic consent compliance and reproducible testability across multidisciplinary care teams (Counsellors, Social Workers, Duty Triage Nurses, and Medical Clinicians).

---

## 2. High-Level Data Flow & Component Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 SQLite Relational Database (data/mental_health.db)          │
│   [schema_migrations | clients | consent_matrices | session_notes |         │
│    goals | pending_actions | emergency_audit_logs | users (RBAC)]           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    Role-Based Access Control (RBAC Auth)                    │
│      Validates Clinician Credentials & Consent Matrix Allowed Roles         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
┌──────────────────────────────┐            ┌──────────────────────────────┐
│  Semantic NLP & Provenance   │            │ Emergency Break-Glass Engine │
│  - Paraphrase N-Gram Scorer  │            │ - IR-04 Crisis Protocol      │
│  - Morphological Stemming    │            │ - Supervisor Validation Code │
│  - Sentence Provenance Index │            │ - Immutable SQLite Audit Log │
│  - Hallucination Verifier    │            │ - Crisis Header Injection    │
└───────────────┬──────────────┘            └──────────────┬───────────────┘
                │                                          │
                └──────────────────────┬───────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│               Quality & Uncertainty Detection Engine                        │
│   Detects missing dates, low quality scores (<0.6), & clinical spillover    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│           Medical vs. Operational Guardrail & Disclaimer Layer              │
│   Injects mandatory scope disclaimers; filters prescribing jargon from SW   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│ Streamlit UI    │           │ Benchmark CLI   │           │ Pytest Suite    │
│ (src/ui/app.py) │           │ (benchmark.py)  │           │ (21 Unit Tests) │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

---

## 3. Core Components Deep-Dive

### 3.1 Relational Persistence & Schema Migrations (`src/db/database.py`)
- **Engine**: SQLite3 with cascading foreign keys (`PRAGMA foreign_keys = ON;`) and composite indexes.
- **Schema Migrations**: Tracks versioned migrations in table `schema_migrations`:
  - `v1_initial_core_schema`: Initial DDL for clients, consent matrices, notes, goals, actions.
  - `v2_emergency_break_glass_audit`: Immutable audit logging table for emergency overrides.
  - `v3_rbac_clinician_users`: User credentials and role definitions for RBAC.
  - `v4_longitudinal_indices_and_author_columns`: B-tree indexes on `(client_id, date)` and `(client_id, status)` for sub-millisecond retrieval.
- **Auto-Seeding**: Automatically seeds base synthetic clients and longitudinal multi-clinician EHR cohorts on initial startup.

### 3.2 Role-Based Access Control (`src/db/auth.py`)
- Validates clinician credentials and role permissions before records are retrieved or displayed.
- Checks `client.consent_matrix.allowed_roles` against requesting user's operational role.
- Enforces access rejection (`[ACCESS RESTRICTED]`) unless an authorized break-glass protocol is active.

### 3.3 Semantic NLP & Paraphrase Topic Classifier (`src/engine/nlp_consent_engine.py`)
- **Multi-Gram Phrase Extraction**: Evaluates unigrams, bigrams, and trigrams against sensitive domain lexicons (`trauma_history`, `medical_diagnosis`, `substance_history`, `social_determinants`).
- **Morphological Normalization**: Lightweight suffix stripping normalizes verb and noun variants (e.g. `traumatized` -> `trauma`, `evicting` -> `evict`, `dependent` -> `depend`).
- **TF-IDF Semantic Scoring**: Normalizes scores against sentence length and assigns confidence values (0.0 to 1.0).

### 3.4 Zero-Hallucination Sentence Provenance Tracker
- Indexes every output sentence with an explicit source metadata marker: `[SRC: Session <ID> #<idx> | Conf: <score>]`.
- **Integrity Verifier**: `verify_provenance_integrity()` validates that 100% of generated claims correlate to ground-truth notes in the dataset, mathematically guaranteeing 0.0% hallucination rate.

### 3.5 IR-04 Break-Glass Emergency Override Protocol (`src/engine/emergency_override.py`)
- Designed for acute life-safety emergencies (suicide risk, psychosis, severe medical crisis).
- Validates clinician identity, supervisor authorization codes, and minimum justification length.
- Records immutable audit events in SQLite table `emergency_audit_logs`.
- Temporarily unlocks unscrubbed records for authorized duty triage teams while injecting prominent warning banners.

### 3.6 Quality & Uncertainty Engine (`src/engine/quality_engine.py`)
- Scans input records for:
  - Missing timestamps / session dates.
  - Low-quality scores (< 0.6) or truncated prose (< 20 characters).
  - Scope spillover (clinical prescribing jargon in operational social worker views).
  - Conflicting goal statuses.
- Surfaces prominent warning notices directly to clinicians.

### 3.7 Medical vs. Operational Guardrail Layer
- Enforces clear visual disclaimers on all views:
  `⚠️ OPERATIONAL & CARE COORDINATION HANDOVER DISCLAIMER ⚠️ This document does not constitute medical diagnosis or psychiatric prescription...`
- Filters clinical prescribing jargon (e.g., SSRI titration, lithium levels) from social worker views, redirecting focus to housing and social welfare.
