# Clinical, Privacy & Ethical Risk Register

## Risk Matrix Overview

| Risk ID | Risk Category | Risk Description | Severity | Mitigation Strategy in System | Status |
|---|---|---|---|---|---|
| **R-01** | **Privacy & Consent** | Unconsented disclosure of traumatic history to non-consented care roles. | **CRITICAL** | Deterministic `ConsentEngine` redacts sensitive tags and keyword regexes before view synthesis. Maintains full audit trail. | **MITIGATED** |
| **R-02** | **Clinical Scope** | Social workers acting on unverified clinical advice or prescribing jargon. | **HIGH** | Mandatory header banner in all views. Strips clinical codes and maps diagnostic context to operational support needs. | **MITIGATED** |
| **R-03** | **Data Integrity** | Care staff making decisions based on incomplete, un-dated, or corrupted session notes. | **HIGH** | `QualityEngine` scans all notes for missing dates and quality scores < 0.6, generating prominent red uncertainty alerts. | **MITIGATED** |
| **R-04** | **Safety / Crisis Override** | Client revokes consent for substance/trauma history while in active crisis, blinding care staff. | **CRITICAL** | Emergency safety override flag workflow (log alert raised with mandatory audit log for duty team review). | **MITIGATED** |
| **R-05** | **Client Repetition** | Key goals or pending actions buried in raw text, causing client to repeat history. | **MEDIUM** | Role-tailored summary structures active goals and pending tasks into dedicated UI cards. | **MITIGATED** |
