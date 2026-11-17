import re

from app.schemas import SafetyOutcome


# This deliberately small starter pathway is not a diagnostic model. It requires clinical review
# before patient-facing deployment and exists to make unsafe LLM-only escalation impossible.
EMERGENCY_TERMS = {
    "chest pain", "difficulty breathing", "cannot breathe", "trouble breathing",
    "unconscious", "passed out", "fainted", "seizure", "stroke", "face drooping",
    "weakness on one side", "heavy bleeding", "suicidal", "self harm",
    "sudden severe headache", "worst headache", "vision loss", "fever and stiff neck",
}


class ClinicalSafetyEngine:
    pathway_version = "0.1"

    def assess(self, user_text: str) -> SafetyOutcome:
        normalized = user_text.lower()
        matched = []
        for term in EMERGENCY_TERMS:
            for found in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", normalized):
                preceding = normalized[max(0, found.start() - 25):found.start()]
                # A denied symptom is not evidence that it is present. This narrow
                # guard avoids obvious false alarms; it is not a clinical NLP model.
                if re.search(r"(?:\bno|\bwithout|\bdenies|\bnot|\bnever|don't have|do not have)\s+(?:\w+\s+){0,2}$", preceding):
                    continue
                matched.append(term)
                break
        matched.sort()
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
