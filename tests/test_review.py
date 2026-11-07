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
