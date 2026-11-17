"""Versioned, explainable draft assessment for recorded symptom episodes.

Unknown continuity is never converted into elapsed symptom duration. These rules
require clinical validation before live patient triage.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.db.models import HealthEpisode
from app.schemas import PatientContext
from app.services.intake import symptom_category

ReviewLevel = Literal["routine", "timely_assessment"]
Priority = Literal["P0", "P1", "P2", "P3", "P4"]


@dataclass(frozen=True)
class ClinicalReviewOutcome:
    level: ReviewLevel
    priority: Priority | None = None
    status: Literal["assessed", "need_more_information"] = "need_more_information"
    reasons: list[str] = field(default_factory=list)
    trigger_codes: list[str] = field(default_factory=list)
    dimensions: dict[str, int | None] = field(default_factory=dict)
    evidence: dict[str, object] = field(default_factory=dict)
    pathway_name: str = "longitudinal_review_draft"
    pathway_version: str = "0.3-draft"


class ClinicalReviewEngine:
    """Return an inspectable next step without generating a disease prediction."""

    def assess(self, episode: HealthEpisode, context: PatientContext) -> ClinicalReviewOutcome:
        summary = episode.summary or {}
        category = symptom_category(episode)
        duration = self._duration_days(summary, episode)
        progression = str(summary.get("progression") or "").lower()
        severity = str(summary.get("severity") or "").lower()
        impact = str(summary.get("functional_impact") or "").lower()
        reasons: list[str] = []
        triggers: list[str] = []

        # NTEP's two-week cough criterion is a draft local pathway candidate. Only
        # an explicit reported duration or confirmed continuity can satisfy it.
        if category == "respiratory" and "cough" in (episode.normalized_symptom or "").lower():
            if duration is not None and duration >= 14:
                reasons.append("you reported a cough continuing for about two weeks or longer")
                triggers.append("COUGH_PERSISTENCE_IN_01_DRAFT")
        elif category == "headache_neuro" and duration is not None and duration >= 5:
            reasons.append("you reported that the headache has continued for several days")
            triggers.append("PERSISTENT_REPORTED_SYMPTOM")

        if any(word in progression for word in ("worse", "worsening")):
            reasons.append("you reported that it is getting worse")
            triggers.append("WORSENING_REPORTED_SYMPTOM")
        if "severe" in severity:
            reasons.append("you described it as severe")
            triggers.append("SEVERE_REPORTED_SYMPTOM")
        if any(word in impact for word in ("hard to carry", "unable")):
            reasons.append("you reported difficulty with usual activities")
            triggers.append("FUNCTIONAL_IMPACT_REPORTED")

        related = [item for item in context.related_episodes if item.get("id") != episode.id]
        if related and triggers:
            reasons.append("a similar concern is recorded previously")
            triggers.append("RELATED_EPISODE_CONTEXT")
        modifier = self._relevant_profile_modifier(category, context.conditions)
        if modifier and triggers:
            reasons.append(f"your recorded {modifier} should be considered with this concern")
            triggers.append("RELEVANT_RECORDED_HISTORY")

        improving = any(word in progression for word in ("better", "improving"))
        if improving and not triggers:
            reasons.append("you reported that it is improving")
        missing = [field for field in ("severity", "progression", "functional_impact") if not summary.get(field)]
        if duration is None:
            missing.append("duration")
        assessed = not missing
        priority: Priority = "P2" if triggers else ("P0" if assessed else "P1")
        return ClinicalReviewOutcome(
            level="timely_assessment" if triggers else "routine",
            priority=priority,
            status="assessed" if assessed or triggers else "need_more_information",
            reasons=reasons,
            trigger_codes=triggers,
            dimensions={
                "persistence": 3 if "COUGH_PERSISTENCE_IN_01_DRAFT" in triggers else None,
                "progression": 2 if "WORSENING_REPORTED_SYMPTOM" in triggers else (0 if improving else None),
                "functional_impact": 2 if "FUNCTIONAL_IMPACT_REPORTED" in triggers else None,
            },
            evidence={"reported_duration_days": duration, "continuity": summary.get("continuity", "unknown"),
                      "missing_fields": missing, "related_episode_ids": [item["id"] for item in related]},
        )

    @staticmethod
    def _duration_days(summary: dict, episode: HealthEpisode) -> int | None:
        text = str(summary.get("duration") or summary.get("onset") or "").lower()
        digits = re.search(r"\b(\d+)\s*(day|week|month)s?\b", text)
        if digits:
            value, unit = int(digits.group(1)), digits.group(2)
            return value * {"day": 1, "week": 7, "month": 30}[unit]
        words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "eleven": 11, "twelve": 12, "fourteen": 14}
        for word, value in words.items():
            match = re.search(rf"\b{word}\s*(day|week|month)s?\b", text)
            if match:
                return value * {"day": 1, "week": 7, "month": 30}[match.group(1)]
        if summary.get("continuity") == "confirmed_continuous":
            start = getattr(episode, "onset_date", None) or getattr(episode, "created_at", None)
            if start:
                start_date = start.date() if hasattr(start, "date") else start
                return max(0, (date.today() - start_date).days)
        return None

    @staticmethod
    def _relevant_profile_modifier(category: str, conditions: list[str]) -> str | None:
        keywords = {
            "chest": ("heart", "cardiac", "diabetes", "hypertension", "stroke"),
            "respiratory": ("asthma", "copd", "lung", "respiratory"),
            "urinary": ("kidney",),
        }
        for condition in conditions:
            if any(term in condition.lower() for term in keywords.get(category, ())):
                return condition
        return None
