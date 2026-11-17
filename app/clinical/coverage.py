"""Clinical library coverage audit. Routing != clinical safety validation.

The report intentionally never calls a drafted rule clinically 'complete'.
"""
from collections import Counter
from pathlib import Path
import json
import yaml
from .registry import Registry


def build_coverage_report(root: Path) -> dict:
    root = Path(root)
    registry = Registry(root / 'clinical' / 'pathways')
    concepts = yaml.safe_load((root / 'clinical' / 'concepts' / 'symptoms.yaml').read_text())
    mapping = yaml.safe_load((root / 'clinical' / 'concepts' / 'condition_presentation_map.yaml').read_text())
    cases = [json.loads(line) for p in (root / 'clinical' / 'cases').glob('*.jsonl')
             for line in p.read_text().splitlines() if line.strip()]
    scenarios = Counter()
    for case in cases:
        # The case is an engineering expectation, not a clinically adjudicated label.
        for code in case.get('symptom_codes', []):
            scenarios[code] += 1
    active = {pid: registry.get(pid, include_drafts=True) for pid in registry.by_id}
    normal = {pid: p for pid,p in active.items() if pid!='global_emergency'}
    route_map = {code: [] for code in concepts}
    for pid, p in normal.items():
        for code in p.routing.get('symptom_codes', []):
            route_map.setdefault(code, []).append(pid)
    global_emergency = active['global_emergency']
    safety_codes = set(global_emergency.required_facts)
    supporting_codes = set(code for p in normal.values() for code in p.required_facts)
    symptoms = []
    for code, obj in concepts.items():
        routes = sorted(route_map.get(code, []))
        state = ('ROUTED_DRAFT' if routes else
                 'SAFETY_FACT_ONLY' if code in safety_codes else
                 'SUPPORTING_FACT_ONLY' if code in supporting_codes else 'VOCABULARY_ONLY')
        symptoms.append({
            'code':code, 'domains':obj.get('domains',[]), 'term_status':'DRAFT_UNREVIEWED',
            'routing_status':state,'route_pathways':routes,
            'safety_fact':code in safety_codes,'engineering_cases_count':scenarios[code],
            'clinical_readiness':'NOT_VALIDATED'
        })
    by_symptom = {x['code']:x for x in symptoms}
    disease_rows = []
    for e in mapping['entries']:
        codes=e['associated_symptom_codes']
        routed=[code for code in codes if by_symptom[code]['routing_status']=='ROUTED_DRAFT']
        safety=[code for code in codes if by_symptom[code]['routing_status']=='SAFETY_FACT_ONLY']
        missing=[code for code in codes if code not in routed and code not in safety]
        pids=sorted({p for c in codes for p in route_map.get(c, [])})
        available_cases=sum(scenarios[c] for c in codes)
        # Clinically ready only with a qualified approval, independent validation, and eligible populations.
        approved=[p for p in pids if active[p].status=='approved']
        readiness='NOT_CLINICALLY_VALIDATED'
        mapping_status=('ALL_PRESENTATIONS_ROUTED_IN_DRAFT' if not missing and not safety else
                        'ALL_ROUTED_OR_SAFETY_ONLY_IN_DRAFT' if not missing else
                        'PARTIAL_ROUTING_IN_DRAFT' if routed or safety else 'NO_ROUTING')
        disease_rows.append({
            'condition_id':e['id'], 'domain':e['domain'], 'name':e['name'],
            'presentation_mode':e['presentation_mode'], 'associated_symptom_count':len(codes),
            'routed_symptoms':routed, 'safety_only_symptoms':safety,'unrouted_symptoms':missing,
            'pathways':pids, 'engineering_case_count':available_cases,
            'candidate_source_ids':e['source_ids'], 'mapping_status':mapping_status,
            'approved_pathway_count':len(approved),'clinical_readiness':readiness,
            'limitations':['associations are not diagnostic','draft decision tables',
                           'child/pregnancy populations not supported','clinical sign-off missing']
        })
    group=Counter(e['domain'] for e in disease_rows)
    routecounts=Counter(x['routing_status'] for x in symptoms)
    return {
        'release':'0.2.0', 'date':'2026-11-16', 'purpose':'Engineering coverage and clinical review planning',
        'disclaimer':'DO NOT interpret mapping or tests as validated diagnosis or triage coverage.',
        'summary':{
            'domain_count':len(group),'condition_entries':len(disease_rows),
            'symptom_concepts':len(concepts), 'draft_pathway_ids':len(normal)+1,
            'pathway_versions_on_disk':sum(map(len, registry.by_id.values())),
            'condition_entries_with_all_presentations_routed_or_safety_only':sum(not e['unrouted_symptoms'] for e in disease_rows),
            'clinically_validated_condition_entries':0,
            'symptom_concepts_routed':routecounts['ROUTED_DRAFT'],
            'symptom_concepts_safety_only':routecounts['SAFETY_FACT_ONLY'],
            'symptom_concepts_supporting_only':routecounts['SUPPORTING_FACT_ONLY'],
            'symptom_concepts_vocabulary_only':routecounts['VOCABULARY_ONLY'],
            'engineering_scenarios':len(cases), 'independently_clinician_adjudicated_scenarios':0,
            'domains':dict(group)},
        'conditions':disease_rows,'symptoms':symptoms,
        'pathways':[{'id':pid, 'version':p.version,'clinical_status':p.status,
                     'rule_count':len(p.rules),'question_count':len(p.questions),
                     'route_codes':p.routing.get('symptom_codes',[]),
                     'clinical_owner':p.governance.get('clinical_owner'),
                     'limitations':p.governance.get('limitations',[])} for pid,p in sorted(active.items())]
    }
