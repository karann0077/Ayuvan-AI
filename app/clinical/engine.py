"""Deterministic tri-state, multi-pathway simulation. No LLM can set disposition."""
from datetime import datetime, timezone
from uuid import uuid4
from .types import AssessmentInput, AssessmentOutput, PathwayResult, Fact, FactState
from .facts import Truth, effective_fact, test_condition
from .registry import Registry, Pathway

PRIORITIES = {f"P{i}": i for i in range(5)}


def add_derived_episode_facts(request: AssessmentInput) -> list[Fact]:
    """Infer generic duration ONLY for one uniquely identified current episode.

    v0.1 stores duration_days without a symptom namespace. Applying two episodes
    to one generic fact leaks the older onset into the newer symptom. Fail closed
    for multi-symptom/multi-episode requests until the backend migrates to
    symptom-scoped duration facts (planned before clinical deployment).
    """
    facts = list(request.facts)
    if len(set(request.symptom_codes)) != 1:
        return facts
    code = request.symptom_codes[0]
    candidates = [e for e in request.episodes if e.symptom_code == code and e.status != "resolved"]
    if len(candidates) != 1:
        return facts
    ep = candidates[0]
    if ep.status == "active" and ep.continuity == "continuous" and ep.onset_at and ep.onset_confirmed:
        elapsed = (request.as_of - ep.onset_at).total_seconds()
        if elapsed >= 0:
            facts.append(Fact(
                code="duration_days", state=FactState.PRESENT,
                value=int(elapsed // 86400), observed_at=request.as_of,
                source_type="patient", source_id=f"episode:{ep.episode_id}:confirmed_onset",
                verification="patient_confirmed"
            ))
            facts.append(Fact(
                code="continuity", state=FactState.PRESENT, value="continuous",
                observed_at=request.as_of, source_type="patient",
                source_id=f"episode:{ep.episode_id}:confirmed_continuity",
                verification="patient_confirmed"
            ))
    elif ep.continuity == "unknown" and ep.onset_at:
        facts.append(Fact(
            code="prior_episode_unresolved", state=FactState.PRESENT, value=True,
            observed_at=request.as_of, source_type="patient",
            source_id=f"episode:{ep.episode_id}:history", verification="unverified"
        ))
    return facts


def eligible(pathway: Pathway, request: AssessmentInput) -> tuple[bool, str | None]:
    if request.population.location_country != pathway.jurisdiction:
        return False, "COUNTRY_UNSUPPORTED"
    if pathway.id == "global_emergency":
        return True, None  # Emergency rules apply irrespective of declared population.
    scope = pathway.scope
    if request.population.age_years is None:
        return False, "AGE_UNKNOWN"
    if request.population.age_years < scope.get("minimum_age_years", 18):
        return False, "CHILD_UNSUPPORTED"
    if request.population.pregnant is True and scope.get("exclude_pregnancy", False):
        return False, "PREGNANCY_UNSUPPORTED"
    if request.population.pregnant is None and (scope.get("exclude_pregnancy", False)
                                                or scope.get("require_known_pregnancy_status", False)):
        return False, "PREGNANCY_STATUS_UNKNOWN"
    return True, None


def run_pathway(pathway: Pathway, request: AssessmentInput, facts: list[Fact]) -> PathwayResult:
    ok, why = eligible(pathway, request)
    if not ok:
        return PathwayResult(pathway_id=pathway.id, version=pathway.version, pathway_status=pathway.status,
                             status="OUT_OF_SCOPE", reason_codes=[why])

    matches = [rule for rule in pathway.rules if test_condition(rule.when, facts, request.as_of) == Truth.TRUE]
    if matches:
        # Rules encode minimum urgency, never numeric weights.
        best = max(matches, key=lambda x: PRIORITIES[x.priority])
        missing = [code for code in pathway.required_facts
                   if (f := effective_fact(facts, code, request.as_of)) is None or f.state in
                   (FactState.UNKNOWN, FactState.CONTRADICTORY)]
        # A matched non-emergency rule does not mean all safety facts were checked.
        # Preserve the already-established minimum disposition and expose the
        # highest-priority outstanding safety question (do not downgrade it).
        pending_safety_question = None
        if best.priority != "P4":
            for q in sorted(pathway.questions, key=lambda x: x.priority, reverse=True):
                f = effective_fact(facts, q.fact, request.as_of)
                if q.priority >= 90 and (f is None or f.state in (FactState.UNKNOWN, FactState.CONTRADICTORY)) \
                        and test_condition(q.when, facts, request.as_of) == Truth.TRUE:
                    pending_safety_question = q.model_dump()
                    break
        if pending_safety_question is not None and best.priority in {"P0", "P1"}:
            # Never reassure before a still-unanswered potentially urgent question.
            return PathwayResult(
                pathway_id=pathway.id, version=pathway.version, pathway_status=pathway.status,
                status="QUESTION_REQUIRED", question=pending_safety_question,
                reason_codes=["SAFETY_QUESTION_BEFORE_LOW_ACUITY"],
                missing_or_conflicting=missing)
        return PathwayResult(
            pathway_id=pathway.id, version=pathway.version, pathway_status=pathway.status,
            status="DECIDED", priority=best.priority, action=best.action,
            timeframe=best.timeframe, reason_codes=[r.id for r in matches],
            evidence_ids=sorted(set(e for r in matches for e in r.evidence)),
            question=pending_safety_question,
            missing_or_conflicting=missing,
            response=pathway.responses[best.response_key]["en"]
        )

    for q in sorted(pathway.questions, key=lambda x: x.priority, reverse=True):
        # Questions only when fact is absent/uncertain; no repeated questions for known facts.
        f = effective_fact(facts, q.fact, request.as_of)
        if f is not None and f.state not in (FactState.UNKNOWN, FactState.CONTRADICTORY):
            continue
        if test_condition(q.when, facts, request.as_of) == Truth.TRUE:
            return PathwayResult(
                pathway_id=pathway.id, version=pathway.version, pathway_status=pathway.status,
                status="QUESTION_REQUIRED", question=q.model_dump(),
                reason_codes=[f"QUESTION:{q.id}"], missing_or_conflicting=[q.fact]
            )

    unknown = [code for code in pathway.required_facts
               if (f := effective_fact(facts, code, request.as_of)) is None or
               f.state in (FactState.UNKNOWN, FactState.CONTRADICTORY)]
    return PathwayResult(
        pathway_id=pathway.id, version=pathway.version, pathway_status=pathway.status,
        status="INSUFFICIENT_INFORMATION", reason_codes=["NO_APPROVED_RULE_MATCHED"],
        missing_or_conflicting=unknown
    )


def assess(registry: Registry, request: AssessmentInput, include_drafts: bool = True) -> AssessmentOutput:
    facts = add_derived_episode_facts(request)
    global_package = registry.get("global_emergency", request.desired_versions.get("global_emergency"), include_drafts)
    global_result = run_pathway(global_package, request, facts)
    active = registry.matching(request.symptom_codes, request.desired_versions, include_drafts)
    outcomes = [global_result]
    routed = {code for p in active for code in p.routing.get("symptom_codes", [])}
    unmapped = sorted(set(request.symptom_codes) - routed)
    # Critical safety override occurs before any regular pathway; no question can block it.
    if global_result.status == "DECIDED" and global_result.priority == "P4":
        return finalize(outcomes, global_result, registry, unmapped)
    for package in active:
        outcomes.append(run_pathway(package, request, facts))
    if not active:
        # A global emergency non-match cannot imply it is safe.
        return finalize(outcomes, None, registry, unmapped)
    decided = [x for x in outcomes if x.status == "DECIDED"]
    best = max(decided, key=lambda x: PRIORITIES[x.priority]) if decided else None
    return finalize(outcomes, best, registry, unmapped)


def finalize(outcomes: list[PathwayResult], best: PathwayResult | None, registry: Registry,
             unmapped: list[str] | None = None) -> AssessmentOutput:
    unmapped = unmapped or []
    unresolved = [p.pathway_id for p in outcomes if p.status != "DECIDED" and p.pathway_id != "global_emergency"]
    unresolved.extend(f"UNMAPPED:{code}" for code in unmapped)
    selected_question = next((p.question for p in outcomes if p.question is not None and p.priority != "P4"), None)
    if best and best.priority in {"P2", "P3", "P4"}:
        status = "DECIDED"
        message = best.response or "Professional assessment guidance requires clinical review."
        if unresolved:
            message += " Other reported concerns are not yet fully assessed."
    elif unresolved:
        status = "QUESTION_REQUIRED" if selected_question else "INSUFFICIENT_INFORMATION"
        message = "More verified information is required; no low-risk conclusion can be made."
    elif best:
        status = "DECIDED"
        message = best.response or "Clinical message requires review."
    else:
        status = "INSUFFICIENT_INFORMATION"
        message = "No validated pathway covers this presentation. Do not infer that it is low risk."
    return AssessmentOutput(
        assessment_id=str(uuid4()), status=status, priority=best.priority if best and status == "DECIDED" else None,
        action=best.action if best and status == "DECIDED" else None,
        timeframe=best.timeframe if best and status == "DECIDED" else None,
        reason_codes=best.reason_codes if best and status == "DECIDED" else [status],
        question=selected_question if status in {"QUESTION_REQUIRED", "DECIDED"} else None,
        response=message,
        results=outcomes,
        pathway_versions={x.pathway_id: x.version for x in outcomes},
        pathway_sha256={x.pathway_id: registry.hashes[(x.pathway_id,x.version)] for x in outcomes},
        knowledge_sha256=registry.knowledge_hashes,
        unresolved_pathways=unresolved,
        unmapped_symptoms=unmapped,
        requires_additional_assessment=bool(unresolved) or bool(selected_question)
    )
