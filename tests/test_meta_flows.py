from app.services.meta_flows import SYMPTOM_INTAKE_FLOW_SCREEN, symptom_intake_flow_definition


def test_symptom_intake_flow_has_one_terminal_submission_with_expected_fields() -> None:
    flow = symptom_intake_flow_definition()
    assert flow["version"] == "6.3"
    screen = flow["screens"][0]
    assert screen["id"] == SYMPTOM_INTAKE_FLOW_SCREEN
    assert screen["terminal"] is True
    components = screen["layout"]["children"][0]["children"]
    names = {item["name"] for item in components if "name" in item}
    assert {"onset", "severity", "progression", "associated_symptoms", "functional_impact"} <= names
    footer = components[-1]
    assert footer["on-click-action"]["name"] == "complete"
    assert set(footer["on-click-action"]["payload"]) == {
        "onset", "severity", "progression", "associated_symptoms", "functional_impact",
    }
