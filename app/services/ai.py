import json
import logging
import re
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas import PatientContext, SymptomExtraction

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTION = """You extract patient-reported symptom information for AYUVAN.
Return JSON only. Never diagnose, prescribe, assess urgency, invent information, or turn an
inference into a fact. Use null for unknown scalar values. Retain the patient's language."""


class GeminiService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def extract_symptoms(self, text: str, context: PatientContext) -> SymptomExtraction:
        if not self.settings.gemini_api_key:
            return self._heuristic_extraction(text)
        prompt = {
            "instruction": SYSTEM_INSTRUCTION,
            "schema": SymptomExtraction.model_json_schema(),
            "patient_context": context.model_dump(mode="json"),
            "user_message": text,
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent?key="
            f"{self.settings.gemini_api_key.get_secret_value()}"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt)}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            candidate = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return SymptomExtraction.model_validate_json(candidate)
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("Gemini extraction failed; using safe fallback: %s", type(exc).__name__)
            return self._heuristic_extraction(text)

    @staticmethod
    def _heuristic_extraction(text: str) -> SymptomExtraction:
        lower = text.lower()
        aliases = {
            "headache": ["headache", "head pain", "sar dard", "sir dard"],
            "cough": ["cough", "khansi"],
            "fever": ["fever", "bukhar"],
            "stomach pain": ["stomach pain", "abdominal pain", "pet dard", "pet mein dard"],
        }
        symptom = next((name for name, terms in aliases.items() if any(term in lower for term in terms)), None)
        duration = None
        duration_match = re.search(r"\b(?:for|since)\s+([\w\s]+?(?:day|days|week|weeks|month|months))\b", lower)
        if duration_match:
            duration = duration_match.group(1).strip()
        return SymptomExtraction(
            main_symptom=symptom,
            normalized_symptom=symptom,
            duration=duration,
            missing_information=["onset", "frequency", "severity", "associated_symptoms"],
            confidence=30 if symptom else 0,
        )
