"""Strict clinical-input types. All interpretations must be explicitly sourced."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class FactState(str, Enum):
    PRESENT = "present"             # Affirmed by source
    ABSENT = "absent"               # Explicitly denied by source
    UNKNOWN = "unknown"             # No reliable observation
    CONTRADICTORY = "contradictory" # Conflicting evidence

class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    state: FactState
    value: Any = None
    observed_at: datetime
    recorded_at: datetime | None = None
    valid_until: datetime | None = None # Optional explicitly reviewed expiry; expired facts become unknown
    source_type: Literal["patient", "clinician", "document", "extracted", "device"]
    source_id: str = Field(min_length=1)
    verification: Literal["unverified", "patient_confirmed", "clinician_confirmed"] = "unverified"

    @field_validator("observed_at", "recorded_at", "valid_until")
    @classmethod
    def require_timezone(cls, v):
        if v is not None and (v.tzinfo is None or v.utcoffset() is None):
            raise ValueError("Timestamps must include timezone information")
        return v

class Episode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    episode_id: str
    symptom_code: str
    onset_at: datetime | None = None
    resolution_at: datetime | None = None
    status: Literal["active", "resolved", "uncertain"] = "uncertain"
    continuity: Literal["continuous", "resolved_then_recurred", "new", "unknown"] = "unknown"
    onset_confirmed: bool = False

    @field_validator("onset_at", "resolution_at")
    @classmethod
    def require_episode_timezone(cls, v):
        if v is not None and (v.tzinfo is None or v.utcoffset() is None):
            raise ValueError("Episode timestamps must include timezone")
        return v

class Population(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_years: int | None = Field(default=None, ge=0, le=125)
    pregnant: bool | None = None
    location_country: str = "IN"

class AssessmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=128) # DEV only; replace with authenticated principal
    request_id: str = Field(min_length=1, max_length=128)
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    population: Population
    symptom_codes: list[str] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    episodes: list[Episode] = Field(default_factory=list)
    desired_versions: dict[str, str] = Field(default_factory=dict)

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, v):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("as_of must include timezone")
        return v

class PathwayResult(BaseModel):
    pathway_id: str
    version: str
    pathway_status: str
    status: Literal["DECIDED", "QUESTION_REQUIRED", "OUT_OF_SCOPE", "INSUFFICIENT_INFORMATION"]
    priority: str | None = None
    action: str | None = None
    timeframe: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    question: dict | None = None
    missing_or_conflicting: list[str] = Field(default_factory=list)
    response: str | None = None

class AssessmentOutput(BaseModel):
    assessment_id: str
    simulated: bool = True
    intended_use: str = "Engineering simulation, NOT a validated clinical assessment"
    status: Literal["DECIDED", "QUESTION_REQUIRED", "OUT_OF_SCOPE", "INSUFFICIENT_INFORMATION"]
    priority: str | None = None
    action: str | None = None
    timeframe: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    question: dict | None = None
    response: str
    results: list[PathwayResult]
    pathway_versions: dict[str, str]
    pathway_sha256: dict[str, str] = Field(default_factory=dict)
    knowledge_sha256: dict[str, str] = Field(default_factory=dict)
    unresolved_pathways: list[str] = Field(default_factory=list)
    unmapped_symptoms: list[str] = Field(default_factory=list)
    requires_additional_assessment: bool = False
