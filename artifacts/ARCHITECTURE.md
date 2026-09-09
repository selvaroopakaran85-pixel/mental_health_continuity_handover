# Technical Architecture & Data Flow

## System Overview
The **Consent-Aware Mental Health Continuity Summary System** is built on a modular, privacy-first Python architecture. It decouples privacy enforcement and quality assurance from presentation logic to ensure deterministic consent compliance and reproducible testability.

---

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Synthetic Client Dataset                  │
│       (Session Notes, Active Goals, Pending Actions)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Consent Engine (Privacy)                 │
│  - Inspects Client Consent Matrix                           │
│  - Executes Keyword & Category Redaction Rules              │
│  - Generates Audit Log                                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Quality Engine (Uncertainty)             │
│  - Detects Missing Timestamps & Corrupt Notes               │
│  - Scans for Clinical Jargon Spillover                       │
│  - Surfaces Uncertainty Flags                               │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                   Summary Engine (Synthesis)                │
│  - Counsellor View vs Social Worker View Synthesizer        │
│  - Injects Mandatory Medical vs Operational Disclaimer      │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌───────────────┐
│ Streamlit UI  │     │ Benchmark Suite │     │ Pytest Suite  │
│ (app.py)      │     │ (benchmark.py)  │     │ (tests/)      │
└───────────────┘     └─────────────────┘     └───────────────┘
```

---

## Core Components Breakdown

1. **`src/models/data_models.py`**:
   - Pydantic models (`ClientProfile`, `ConsentMatrix`, `SessionNote`, `Goal`, `PendingAction`, `HandoverSummary`, `UncertaintyNotice`).
2. **`src/engine/consent_engine.py`**:
   - Redaction engine that compares note tags and keyword regex patterns against `ConsentMatrix`.
   - Replaces non-consented sensitive strings with privacy-preserving tokens (`[REDACTED-TRAUMA_HISTORY]`).
3. **`src/engine/quality_engine.py`**:
   - Analyzes notes for missing dates, quality scores < 0.6, clinical code spillover, and contradictory goal statuses.
4. **`src/engine/summary_engine.py`**:
   - Synthesizes role-tailored continuity summaries and injects mandatory operational disclaimers.
5. **`src/evaluation/benchmark.py`**:
   - Automated evaluation suite calculating Repetition Avoidance, Consent Leakage, Guardrail Compliance, and Uncertainty Flagging.
6. **`src/ui/app.py`**:
   - Interactive Streamlit dashboard for care staff and stakeholders.
