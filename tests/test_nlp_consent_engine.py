"""
Unit tests for Semantic NLP Topic Classifier and Provenance Tracker.
Tests paraphrase resilience, sentence-level scrubbing, and zero-hallucination provenance integrity.
"""

from src.models.data_models import (
    ConsentCategory,
    ConsentMatrix,
    SessionNote,
    RoleEnum,
)
from src.engine.nlp_consent_engine import SemanticTopicClassifier, ProvenanceTracker


def test_semantic_classifier_paraphrase_detection():
    classifier = SemanticTopicClassifier()

    # Paraphrased trauma
    cat, conf, terms = classifier.classify_sentence(
        "Client experienced severe early life stress and nightmares after childhood hardship."
    )
    assert cat == ConsentCategory.TRAUMA_HISTORY
    assert conf >= 0.35

    # Paraphrased medical diagnosis
    cat_m, conf_m, _ = classifier.classify_sentence(
        "Psychiatrist completed clinical diagnosis and prescribed mood stabilizer titration."
    )
    assert cat_m == ConsentCategory.MEDICAL_DIAGNOSIS
    assert conf_m >= 0.35


def test_subtle_paraphrases_detection():
    classifier = SemanticTopicClassifier()

    # Subtle substance dependency paraphrase
    cat_sub, conf_sub, _ = classifier.classify_sentence(
        "Marcus achieved ninety days of continuous sobriety following inpatient detox for chemical dependency."
    )
    assert cat_sub == ConsentCategory.SUBSTANCE_HISTORY
    assert conf_sub >= 0.35

    # Subtle housing distress / eviction paraphrase
    cat_soc, conf_soc, _ = classifier.classify_sentence(
        "Client is facing utility shutoff and impending apartment lease termination due to rent arrears."
    )
    assert cat_soc == ConsentCategory.SOCIAL_DETERMINANTS
    assert conf_soc >= 0.35

    # Subtle trauma paraphrase
    cat_t, conf_t, _ = classifier.classify_sentence(
        "Client continues to battle intrusive night terrors linked to past domestic brutality."
    )
    assert cat_t == ConsentCategory.TRAUMA_HISTORY
    assert conf_t >= 0.35


def test_provenance_tracker_tagging_and_scrubbing():
    tracker = ProvenanceTracker()
    matrix = ConsentMatrix(share_trauma_history=False)
    notes = [
        SessionNote(
            session_id="S-NLP1",
            date="2026-10-01",
            author_role=RoleEnum.COUNSELLOR,
            summary="Client discussed early life stress and nightmares.",
            sensitive_categories=[ConsentCategory.TRAUMA_HISTORY],
        )
    ]

    sanitized, notices, recs = tracker.process_and_redact_notes(notes, matrix)

    assert len(recs) >= 1
    assert recs[0].source_session_id == "S-NLP1"
    assert "SRC: Session S-NLP1" in recs[0].provenance_tag
    assert "[REDACTED-TRAUMA_HISTORY" in sanitized[0]
    assert len(notices) == 1


def test_provenance_integrity_zero_hallucination():
    tracker = ProvenanceTracker()
    matrix = ConsentMatrix(share_trauma_history=True, share_social_determinants=True)
    notes = [
        SessionNote(
            session_id="S-V1",
            date="2026-10-01",
            author_role=RoleEnum.SOCIAL_WORKER,
            summary="Completed food bank referral. Coordinated emergency utility relief grant.",
            sensitive_categories=[ConsentCategory.SOCIAL_DETERMINANTS],
        )
    ]

    sanitized, notices, recs = tracker.process_and_redact_notes(notes, matrix)
    integrity_report = tracker.verify_provenance_integrity(sanitized, notes)

    assert integrity_report["hallucination_control_passed"] is True
    assert integrity_report["hallucination_rate_pct"] == 0.0
    assert integrity_report["provenance_integrity_pct"] == 100.0
    assert integrity_report["total_assertions_indexed"] >= 1
