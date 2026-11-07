from app.schemas import SafetyOutcome


# This deliberately small starter pathway is not a diagnostic model. It requires clinical review
# before patient-facing deployment and exists to make unsafe LLM-only escalation impossible.
EMERGENCY_TERMS = {
    "chest pain", "difficulty breathing", "cannot breathe", "trouble breathing",
    "unconscious", "passed out", "fainted", "seizure", "stroke", "face drooping",
    "weakness on one side", "heavy bleeding", "suicidal", "self harm",
}


class ClinicalSafetyEngine:
    pathway_version = "0.1"

    def assess(self, user_text: str) -> SafetyOutcome:
        normalized = user_text.lower()
        matched = sorted(term for term in EMERGENCY_TERMS if term in normalized)
        if matched:
            return SafetyOutcome(
                level="emergency",
                pathway_name="emergency_keyword_screen",
                pathway_version=self.pathway_version,
                matched_terms=matched,
                response=(
                    "Some symptoms you mentioned may need urgent medical attention. "
                    "Please seek emergency medical help now or contact your local emergency service. "
                    "AYUVAN cannot provide emergency care."
                ),
            )
        return SafetyOutcome(pathway_version=self.pathway_version)
