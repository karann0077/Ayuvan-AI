from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class NormalizedIncomingMessage(BaseModel):
    provider_message_id: str
    sender: str
    timestamp: datetime | None = None
    message_type: Literal["text", "interactive", "image", "audio", "document", "video", "location", "unsupported"]
    content: str | None = None
    media_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SymptomExtraction(BaseModel):
    main_symptom: str | None = None
    normalized_symptom: str | None = None
    onset: str | None = None
    duration: str | None = None
    frequency: str | None = None
    severity: str | None = None
    progression: str | None = None
    time_pattern: str | None = None
    associated_symptoms: list[str] = Field(default_factory=list)
    medicines_mentioned: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    is_correction: bool = False
    confidence: int = Field(default=0, ge=0, le=100)

    @field_validator("main_symptom", "normalized_symptom", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip().lower() in {"", "unknown", "none", "null"}:
            return None
        return value


class PatientContext(BaseModel):
    patient_id: str
    summary_version: int
    preferred_language: str | None = None
    current_medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    active_episodes: list[dict[str, Any]] = Field(default_factory=list)
    related_episodes: list[dict[str, Any]] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    recent_conversation: list[dict[str, str]] = Field(default_factory=list)
    source_record_ids: list[str] = Field(default_factory=list)


class SafetyOutcome(BaseModel):
    level: Literal["emergency", "standard"] = "standard"
    pathway_name: str = "general_symptom_intake"
    pathway_version: str = "0.1"
    response: str | None = None
    matched_terms: list[str] = Field(default_factory=list)


class FollowUpQuestion(BaseModel):
    field: str
    text: str
    options: list[tuple[str, str]] = Field(default_factory=list)


class HealthRecordResponse(BaseModel):
    patient_id: str
    summary_version: int
    active_episodes: list[dict[str, Any]]
