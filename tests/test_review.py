from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.schemas import PatientContext
from app.services.review import ClinicalReviewEngine


def test_persistent_worsening_symptom_gets_explainable_clinician_review() -> None:
    episode = SimpleNamespace(
        id="episode-1", normalized_symptom="headache",
        summary={"duration": "five days", "progression": "Getting worse", "severity": "Moderate"},
    )
    context = PatientContext(patient_id="patient-1", summary_version=1)
    outcome = ClinicalReviewEngine().assess(episode, context)
    assert outcome.level == "timely_assessment"
    assert "PERSISTENT_REPORTED_SYMPTOM" in outcome.trigger_codes
    assert "WORSENING_REPORTED_SYMPTOM" in outcome.trigger_codes
    assert all("cancer" not in reason.lower() for reason in outcome.reasons)


def test_short_isolated_cough_does_not_trigger_consultation() -> None:
    episode = SimpleNamespace(
        id="cough-1", normalized_symptom="cough", primary_symptom="cough",
        summary={"duration": "one day", "severity": "Mild", "progression": "Improving",
                 "functional_impact": "Yes, mostly"},
    )
    outcome = ClinicalReviewEngine().assess(
        episode, PatientContext(patient_id="patient-1", summary_version=1)
    )
    assert outcome.priority == "P0"
    assert outcome.level == "routine"
    assert outcome.trigger_codes == []


def test_two_week_cough_requires_reported_duration_or_confirmed_continuity() -> None:
    context = PatientContext(patient_id="patient-1", summary_version=1)
    episode = SimpleNamespace(
        id="cough-1", normalized_symptom="cough", primary_symptom="cough",
        summary={"duration": "14 days"},
    )
    result = ClinicalReviewEngine().assess(episode, context)
    assert result.priority == "P2"
    assert result.evidence["reported_duration_days"] == 14
    assert "COUGH_PERSISTENCE_IN_01_DRAFT" in result.trigger_codes

    episode.summary = {"continuity": "unknown"}
    result = ClinicalReviewEngine().assess(episode, context)
    assert result.priority == "P1"
    assert result.evidence["reported_duration_days"] is None

    episode.created_at = datetime.now(timezone.utc) - timedelta(days=15)
    episode.summary = {"continuity": "confirmed_continuous"}
    result = ClinicalReviewEngine().assess(episode, context)
    assert result.priority == "P2"
    assert result.evidence["reported_duration_days"] >= 14
