"""Non-diagnostic, explainable clinician-review signals.

These are conservative starter signals, not a disease predictor or a substitute for a
clinician-approved symptom pathway. They are kept separate from language generation so every
recommendation has inspectable patient-reported evidence.
"""

import re
from dataclasses import dataclass, field
from typing import Literal

from app.db.models import HealthEpisode
from app.schemas import PatientContext
from app.services.intake import symptom_category


ReviewLevel = Literal["routine", "timely_assessment"]


@dataclass(frozen=True)
class ClinicalReviewOutcome:
    level: ReviewLevel
    reasons: list[str] = field(default_factory=list)
    trigger_codes: list[str] = field(default_factory=list)
    pathway_name: str = "longitudinal_review_draft"
    pathway_version: str = "0.2-draft"


class ClinicalReviewEngine:
    """Match patient-reported change with relevant recorded context.

    Emergency detection remains in ``ClinicalSafetyEngine`` and takes precedence. This engine
    never names a possible disease or estimates probability.
    """

    def assess(self, episode: HealthEpisode, context: PatientContext) -> ClinicalReviewOutcome:
        summary = episode.summary or {}
        reasons: list[str] = []
        triggers: list[str] = []

        if self._is_persistent(summary):
            reasons.append("this concern has continued for several days")
            triggers.append("PERSISTENT_REPORTED_SYMPTOM")
        if self._matches(summary.get("progression"), "worse", "worsening"):
            reasons.append("you reported that it is getting worse")
            triggers.append("WORSENING_REPORTED_SYMPTOM")
        if self._matches(summary.get("severity"), "severe"):
            reasons.append("you described it as severe")
            triggers.append("SEVERE_REPORTED_SYMPTOM")
        if self._matches(summary.get("functional_impact"), "hard to carry", "unable"):
            reasons.append("it is making usual activities hard to manage")
            triggers.append("FUNCTIONAL_IMPACT_REPORTED")

        related = [item for item in context.related_episodes if item.get("id") != episode.id]
        if related and ("PERSISTENT_REPORTED_SYMPTOM" in triggers or "WORSENING_REPORTED_SYMPTOM" in triggers):
            reasons.append("a similar concern is already in your AYUVAN record")
            triggers.append("RELATED_EPISODE_CONTEXT")

        modifier = self._relevant_profile_modifier(symptom_category(episode), context.conditions)
        if modifier and triggers:
            reasons.append(f"your recorded {modifier} should be considered with this concern")
            triggers.append("RELEVANT_RECORDED_HISTORY")

        return ClinicalReviewOutcome(
            level="timely_assessment" if triggers else "routine",
            reasons=reasons,
            trigger_codes=triggers,
        )

    @staticmethod
    def _matches(value: object, *terms: str) -> bool:
        text = str(value or "").lower()
        return any(term in text for term in terms)

    @staticmethod
    def _is_persistent(summary: dict) -> bool:
        value = str(summary.get("duration") or summary.get("onset") or "").lower()
        if "week" in value or "month" in value:
            return True
        match = re.search(r"\b(\d+)\s*days?\b", value)
        if match and int(match.group(1)) >= 5:
            return True
        word_numbers = {"five", "six", "seven", "eight", "nine", "ten"}
        return any(f"{word} day" in value for word in word_numbers)

    @staticmethod
    def _relevant_profile_modifier(category: str, conditions: list[str]) -> str | None:
        # Narrow, visible matching only. Unknown/absent history is never treated as negative.
        keywords = {
            "chest": ("heart", "cardiac", "diabetes", "hypertension", "stroke"),
            "respiratory": ("asthma", "copd", "lung", "respiratory"),
            "urinary": ("kidney",),
        }
        for condition in conditions:
            if any(term in condition.lower() for term in keywords.get(category, ())):
                return condition
        return None
