"""Controlled, patient-aware intake questions.

This module deliberately contains no LLM-generated questions or clinical conclusions.
Question wording and option IDs are versioned product content which must be reviewed by
qualified clinicians before a production rollout.
"""

from app.db.models import HealthEpisode
from app.schemas import FollowUpQuestion, PatientContext


NOT_SURE = ("NOT_SURE", "Not sure")


def symptom_category(episode: HealthEpisode) -> str:
    value = (episode.normalized_symptom or episode.primary_symptom or "").lower()
    if any(word in value for word in ("headache", "head pain", "migraine")):
        return "headache_neuro"
    if any(word in value for word in ("chest", "palpitation")):
        return "chest"
    if any(word in value for word in ("cough", "breath", "respirat")):
        return "respiratory"
    if "fever" in value:
        return "fever"
    if any(word in value for word in ("stomach", "abdominal", "abdomen", "vomit", "nausea")):
        return "gastro"
    if any(word in value for word in ("urine", "urinary")):
        return "urinary"
    if any(word in value for word in ("injury", "fall", "accident")):
        return "injury"
    return "general"


HEADACHE_WARNING = FollowUpQuestion(
    field="headache_warning_signs",
    text="*Quick safety check*\nWhich option is closest?",
    options=[
        ("HEADACHE_SCREEN_NONE", "No warning signs"),
        ("HEADACHE_SCREEN_SUDDEN", "Sudden / worst-ever"),
        ("HEADACHE_SCREEN_NEURO", "Weakness / numbness"),
        ("HEADACHE_SCREEN_VISION", "Vision change / loss"),
        ("HEADACHE_SCREEN_FEVER_NECK", "Fever / stiff neck"),
        ("HEADACHE_SCREEN_OTHER", "Something else"),
    ],
    presentation="list",
    button_label="Choose one",
    urgent_option_ids=[
        "HEADACHE_SCREEN_SUDDEN", "HEADACHE_SCREEN_NEURO", "HEADACHE_SCREEN_VISION",
        "HEADACHE_SCREEN_FEVER_NECK",
    ],
    pathway_id="headache_neuro_v0_draft",
)

CHEST_NOW = FollowUpQuestion(
    field="chest_current_state",
    text="*Quick safety check*\nWhat is happening right now?",
    options=[
        ("CHEST_NOW_ONGOING", "Still happening"),
        ("CHEST_NOW_WORSE", "Getting worse"),
        ("CHEST_NOW_BREATHING", "Trouble breathing"),
        ("CHEST_NOW_FAINT", "Faint / very dizzy"),
        ("CHEST_NOW_STOPPED", "Has stopped"),
        NOT_SURE,
    ],
    presentation="list",
    button_label="Choose one",
    urgent_option_ids=["CHEST_NOW_WORSE", "CHEST_NOW_BREATHING", "CHEST_NOW_FAINT"],
    pathway_id="chest_v0_draft",
)

RESPIRATORY_NOW = FollowUpQuestion(
    field="breathing_status",
    text="*Quick safety check*\nHow is your breathing right now?",
    options=[
        ("BREATHING_OK", "Normal"),
        ("BREATHING_MILD", "A little harder"),
        ("BREATHING_DIFFICULT", "Hard to breathe"),
    ],
    urgent_option_ids=["BREATHING_DIFFICULT"],
    pathway_id="respiratory_v0_draft",
)

SEVERITY = FollowUpQuestion(
    field="severity",
    text="*How much is this affecting you right now?*\nChoose the closest answer.",
    options=[
        ("SEVERITY_MILD", "Mild"),
        ("SEVERITY_MODERATE", "Moderate"),
        ("SEVERITY_SEVERE", "Severe"),
    ],
    pathway_id="general_symptom_intake_v0_draft",
)

PROGRESSION = FollowUpQuestion(
    field="progression",
    text="*Since it began, is it changing?*",
    options=[
        ("PROGRESSION_BETTER", "Improving"),
        ("PROGRESSION_SAME", "About the same"),
        ("PROGRESSION_WORSE", "Getting worse"),
    ],
    pathway_id="general_symptom_intake_v0_draft",
)

FUNCTIONAL_IMPACT = FollowUpQuestion(
    field="functional_impact",
    text="*Can you manage your usual activities?*",
    options=[
        ("IMPACT_NORMAL", "Yes, mostly"),
        ("IMPACT_SOME", "Some are difficult"),
        ("IMPACT_UNABLE", "Hard to carry on"),
    ],
    pathway_id="general_symptom_intake_v0_draft",
)


class QuestionEngine:
    """Select the next smallest useful question from an approved starter pack."""

    pathway_version = "0.2-draft"

    flow_fields = {
        "onset", "duration", "frequency", "severity", "progression", "functional_impact",
        "headache_warning_signs", "chest_current_state", "breathing_status", "associated_symptoms",
    }

    def next_question(self, episode: HealthEpisode, context: PatientContext) -> FollowUpQuestion | None:
        # ``context`` is intentionally received here even when a starter pack does not need it:
        # a reviewed pathway can use it to omit already-known, still-current fields.
        del context
        summary = episode.summary or {}
        category = symptom_category(episode)
        pack: list[FollowUpQuestion] = []
        if category == "headache_neuro":
            pack.append(HEADACHE_WARNING)
        elif category == "chest":
            pack.append(CHEST_NOW)
        elif category == "respiratory":
            pack.append(RESPIRATORY_NOW)

        # Three concise questions give a usable factual record without a long free-text loop.
        # Severity may already be explicit in the patient's original message, so it is skipped.
        pack.extend([SEVERITY, PROGRESSION, FUNCTIONAL_IMPACT])
        for question in pack:
            if not self._has_answer(summary, question.field):
                return question
        return None

    @staticmethod
    def _has_answer(summary: dict, field: str) -> bool:
        value = summary.get(field)
        return value not in (None, "", [], "unknown")
