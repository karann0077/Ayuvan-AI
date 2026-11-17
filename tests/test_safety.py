from app.services.safety import ClinicalSafetyEngine


def test_emergency_terms_short_circuit() -> None:
    outcome = ClinicalSafetyEngine().assess("I have chest pain and difficulty breathing")
    assert outcome.level == "emergency"
    assert outcome.response


def test_non_emergency_message_is_standard() -> None:
    assert ClinicalSafetyEngine().assess("I have a headache for two days").level == "standard"


def test_denied_warning_sign_does_not_trigger_emergency() -> None:
    assert ClinicalSafetyEngine().assess("I have no chest pain").level == "standard"
    assert ClinicalSafetyEngine().assess("I have no chest pain but difficulty breathing").level == "emergency"
