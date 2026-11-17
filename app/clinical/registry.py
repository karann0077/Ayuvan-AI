"""Typed, locked-down clinical pathway packages. No eval, import, or dynamic Python."""
from pathlib import Path
import hashlib
import re
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

VALID_OPERATORS = {"present", "absent", "unknown", "eq", "in", "gte", "gt", "lte", "lt"}
ALLOWED_STATUSES = {"draft", "approved", "retired"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def validate_condition(c: dict, allowed: set[str]) -> None:
    if not isinstance(c, dict):
        raise ValueError("Condition must be an object")
    if len([k for k in ("all", "any", "not", "fact") if k in c]) != 1:
        raise ValueError("Condition requires exactly one of all/any/not/fact")
    if "all" in c or "any" in c:
        key = "all" if "all" in c else "any"
        if set(c) != {key} or not isinstance(c[key], list) or not c[key]:
            raise ValueError("Invalid composite condition")
        for sub in c[key]: validate_condition(sub, allowed)
    elif "not" in c:
        if set(c) != {"not"}: raise ValueError("Unexpected NOT condition keys")
        validate_condition(c["not"], allowed)
    else:
        if set(c) - {"fact", "op", "value", "max_age_hours"}:
            raise ValueError("Unexpected leaf keys")
        if c.get("fact") not in allowed or c.get("op") not in VALID_OPERATORS:
            raise ValueError("Unknown fact code or prohibited operator")
        if c.get("max_age_hours") is not None and (not isinstance(c["max_age_hours"], (int, float)) or c["max_age_hours"] <= 0):
            raise ValueError("Invalid max_age_hours")
        if c["op"] in {"eq", "in", "gte", "gt", "lte", "lt"} and "value" not in c:
            raise ValueError("Comparator requires value")

class ClinicalRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    when: dict
    priority: str
    action: str
    timeframe: str
    reason: str
    evidence: list[str] = Field(default_factory=list)
    response_key: str

class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    priority: int = Field(ge=0, le=100)
    fact: str
    when: dict
    text: dict[str, str]
    choices: list[dict] = Field(default_factory=list)
    answer_schema: dict
    can_change: list[str] = Field(default_factory=list)

class Pathway(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    version: str
    status: str
    domain: str
    purpose: str
    jurisdiction: str
    languages: list[str]
    scope: dict
    routing: dict
    required_facts: list[str]
    rules: list[ClinicalRule]
    questions: list[Question]
    responses: dict[str, dict[str, str]]
    unknown_case: dict
    follow_through: dict
    governance: dict

    @model_validator(mode="after")
    def validate_package(self):
        if not SEMVER.match(self.version) or self.status not in ALLOWED_STATUSES:
            raise ValueError("Invalid version or release state")
        if self.jurisdiction != "IN":
            raise ValueError("This starter supports India only")
        available = set(self.required_facts) | set(self.routing.get("symptom_codes", []))
        for r in self.rules:
            if r.priority not in {"P0", "P1", "P2", "P3", "P4"}:
                raise ValueError("Invalid priority")
            validate_condition(r.when, available)
            if r.response_key not in self.responses:
                raise ValueError(f"Missing approved-content candidate {r.response_key}")
        for q in self.questions:
            if q.fact not in available:
                raise ValueError(f"Unknown question fact {q.fact}")
            validate_condition(q.when, available)
            for choice in q.choices:
                if (choice.get("fact_state") not in {"present","absent","unknown"}
                    or not choice.get("code") or not choice.get("label_en")):
                    raise ValueError("Choice missing normalized clinical fact mapping")
            if q.answer_schema.get("kind") not in {"choice","nonnegative_integer","confirmation_required_text"}:
                raise ValueError("Invalid answer schema")
            if not all(lang in q.text for lang in self.languages):
                raise ValueError("Question missing a declared language translation")
        for key, translations in self.responses.items():
            if not all(lang in translations for lang in self.languages):
                raise ValueError(f"Response {key} missing translation")
        if not self.rules and self.id != "global_emergency":
            raise ValueError("Pathway must have rules")
        if self.status == "approved":
            approval = self.governance.get("approval", {})
            if not (approval.get("clinician_id") and approval.get("approved_at") and approval.get("release_hash")):
                raise ValueError("Approved package missing governance fields")
        return self


class Registry:
    def __init__(self, root: Path):
        # Content-addressable non-pathway knowledge used to build structured inputs.
        self.knowledge_hashes: dict[str, str] = {}
        for rel in ('concepts/symptoms.yaml','concepts/facts.yaml',
                    'concepts/condition_presentation_map.yaml','evidence/sources.yaml'):
            file = root.parent / rel
            if file.is_file():
                self.knowledge_hashes[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
        self.by_id: dict[str, dict[str, Pathway]] = {}
        self.hashes: dict[tuple[str,str],str] = {}
        for path in sorted(root.rglob("*.yaml")):
            package = Pathway.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            versions = self.by_id.setdefault(package.id, {})
            if package.version in versions:
                raise ValueError(f"Duplicate pathway {package.id}@{package.version}")
            versions[package.version] = package
            self.hashes[(package.id, package.version)] = hashlib.sha256(path.read_bytes()).hexdigest()
        if "global_emergency" not in self.by_id:
            raise ValueError("Global emergency pathway missing")

    def get(self, name: str, version: str | None = None, include_drafts=False) -> Pathway:
        if name not in self.by_id:
            raise KeyError(name)
        candidates = self.by_id[name]
        if version:
            entry = candidates[version]
            if not include_drafts and entry.status != "approved":
                raise PermissionError("Unapproved pathway cannot serve patients")
            return entry
        available = [p for p in candidates.values() if include_drafts or p.status == "approved"]
        if not available:
            raise PermissionError("No approved version available")
        return max(available, key=lambda p: tuple(map(int, p.version.split('.'))))

    def matching(self, symptom_codes: list[str], desired_versions=None, include_drafts=False) -> list[Pathway]:
        desired_versions = desired_versions or {}
        matched = []
        for name in self.by_id:
            if name == "global_emergency": continue
            # Do not require approval from irrelevant pathways.
            if not any(set(p.routing.get("symptom_codes", [])) & set(symptom_codes) for p in self.by_id[name].values()):
                continue
            package = self.get(name, desired_versions.get(name), include_drafts)
            if set(package.routing.get("symptom_codes", [])) & set(symptom_codes):
                matched.append(package)
        return matched
