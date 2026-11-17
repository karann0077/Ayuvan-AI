"""Evidence-aware fact selection, with conservative three-valued decisions."""
from datetime import timedelta
from enum import Enum
from .types import Fact, FactState

class Truth(Enum):
    FALSE = 0
    TRUE = 1
    UNKNOWN = -1


def effective_fact(facts: list[Fact], code: str, as_of, max_age_hours=None) -> Fact | None:
    matches = [f for f in facts if f.code == code and f.observed_at <= as_of
               and (f.valid_until is None or f.valid_until >= as_of)]
    if max_age_hours is not None:
        matches = [f for f in matches if as_of - f.observed_at <= timedelta(hours=max_age_hours)]
    if not matches:
        return None
    latest_time = max(f.observed_at for f in matches)
    latest = [f for f in matches if f.observed_at == latest_time]
    # Same-time explicit disagreements must not be silently overwritten.
    signatures = {(f.state, repr(f.value)) for f in latest if f.state != FactState.UNKNOWN}
    if len(signatures) > 1:
        return latest[-1].model_copy(update={"state": FactState.CONTRADICTORY, "value": None})
    # Unknown at exactly the latest instant cannot erase a known observation.
    confirmed = [f for f in latest if f.state != FactState.UNKNOWN]
    return (confirmed or latest)[-1]


def test_condition(condition: dict, facts: list[Fact], as_of) -> Truth:
    if "all" in condition:
        parts = [test_condition(x, facts, as_of) for x in condition["all"]]
        return Truth.FALSE if Truth.FALSE in parts else (Truth.UNKNOWN if Truth.UNKNOWN in parts else Truth.TRUE)
    if "any" in condition:
        parts = [test_condition(x, facts, as_of) for x in condition["any"]]
        return Truth.TRUE if Truth.TRUE in parts else (Truth.UNKNOWN if Truth.UNKNOWN in parts else Truth.FALSE)
    if "not" in condition:
        val = test_condition(condition["not"], facts, as_of)
        return Truth.UNKNOWN if val == Truth.UNKNOWN else (Truth.TRUE if val == Truth.FALSE else Truth.FALSE)
    code = condition["fact"]
    observation = effective_fact(facts, code, as_of, condition.get("max_age_hours"))
    op = condition["op"]
    if op == "unknown":
        return Truth.TRUE if observation is None or observation.state in (FactState.UNKNOWN, FactState.CONTRADICTORY) else Truth.FALSE
    if observation is None or observation.state in (FactState.UNKNOWN, FactState.CONTRADICTORY):
        return Truth.UNKNOWN
    if op == "present":
        return Truth.TRUE if observation.state == FactState.PRESENT else Truth.FALSE
    if op == "absent":
        return Truth.TRUE if observation.state == FactState.ABSENT else Truth.FALSE
    if observation.state != FactState.PRESENT:
        return Truth.FALSE
    value = condition.get("value")
    observed = observation.value
    if op == "eq":
        return Truth.TRUE if observed == value else Truth.FALSE
    if op == "in":
        return Truth.TRUE if observed in value else Truth.FALSE
    if op in ("gte", "gt", "lte", "lt"):
        if not isinstance(observed, (int, float)) or isinstance(observed, bool):
            return Truth.UNKNOWN
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return Truth.UNKNOWN
        return Truth.TRUE if {"gte": lambda: observed >= value, "gt": lambda: observed > value, "lte": lambda: observed <= value, "lt": lambda: observed < value}[op]() else Truth.FALSE
    raise ValueError(f"Non-allowlisted operator: {op}")


def condition_codes(condition: dict) -> set[str]:
    if "fact" in condition:
        return {condition["fact"]}
    if "not" in condition:
        return condition_codes(condition["not"])
    return set().union(*(condition_codes(c) for c in condition.get("all", condition.get("any", []))))
