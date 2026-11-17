"""Engineering regression; no cases have independent clinician adjudication."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, yaml, pytest
from app.clinical.coverage import build_coverage_report
from app.clinical.registry import Registry
from app.clinical.engine import assess, add_derived_episode_facts
from app.clinical.types import AssessmentInput, Fact, Episode
from app.main import app
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[2]
REGISTRY=Registry(ROOT/'clinical'/'pathways')
DATA=build_coverage_report(ROOT)
NOW=datetime(2026,11,16,9,tzinfo=timezone.utc)

def fact(c,s='present',time=NOW):
 return Fact(code=c,state=s,observed_at=time,source_type='patient',source_id='test',verification='patient_confirmed')

def input_for(codes, facts, episodes=None, age=30, pregnant=False):
 return AssessmentInput(user_id='TEST',request_id='TEST',as_of=NOW,
    population={'age_years':age,'pregnant':pregnant,'location_country':'IN'},
    symptom_codes=codes,facts=facts,episodes=episodes or [])

def test_54_source_condition_entries_are_retained():
 assert DATA['summary']['condition_entries']==54
 assert DATA['summary']['domains']=={'respiratory':10,'infectious':12,'gastroenterology':11,'cardiology':11,'endocrinology':10}
 assert len({r['condition_id'] for r in DATA['conditions']})==54

def test_all_user_listed_condition_presentations_have_draft_routing():
 assert DATA['summary']['condition_entries_with_all_presentations_routed_or_safety_only']==54
 assert all(not r['unrouted_symptoms'] for r in DATA['conditions'])

def test_no_clinical_validation_is_claimed():
 assert DATA['summary']['clinically_validated_condition_entries']==0
 assert all(r['clinical_readiness']=='NOT_CLINICALLY_VALIDATED' for r in DATA['conditions'])
 assert all(p['clinical_status']=='draft' for p in DATA['pathways'])

def test_unmapped_extra_symptom_must_prevent_low_priority_reassurance():
 facts=[fact('cough'),fact('duration_days'),fact('breathing_difficulty','absent'),
        fact('blood_in_sputum','absent'),fact('worsening','absent'),fact('functional_impairment','absent')]
 facts[1]=facts[1].model_copy(update={'value':1})
 x=assess(REGISTRY,input_for(['cough','unmapped_extra_symptom'],facts))
 assert x.priority is None
 assert x.status=='INSUFFICIENT_INFORMATION'
 assert x.unmapped_symptoms==['unmapped_extra_symptom']
 assert x.requires_additional_assessment

def test_unmapped_extra_symptom_cannot_hide_emergency():
 r=assess(REGISTRY,input_for(['cough','unknown_code'],[fact('severe_breathlessness')]))
 assert r.priority=='P4' and r.action=='emergency_help'
 assert r.unmapped_symptoms==['unknown_code']

def test_duration_never_inferred_from_unrelated_episode():
 ep=Episode(episode_id='old-cough',symptom_code='cough',status='active',continuity='continuous',
            onset_confirmed=True,onset_at=NOW-timedelta(days=20))
 x=input_for(['fever'],[fact('fever')],[ep])
 derived=add_derived_episode_facts(x)
 assert not any(z.code=='duration_days' for z in derived)

def test_generic_duration_not_inferred_from_multiple_simultaneous_symptoms():
 ep=Episode(episode_id='old-cough',symptom_code='cough',status='active',continuity='continuous',
            onset_confirmed=True,onset_at=NOW-timedelta(days=20))
 x=input_for(['cough','fever'],[fact('cough'),fact('fever')],[ep])
 assert not any(z.code=='duration_days' for z in add_derived_episode_facts(x))

def test_generic_duration_not_inferred_from_ambiguous_multiple_episodes():
 eps=[Episode(episode_id=f'e{i}',symptom_code='cough',status='active',continuity='continuous',
              onset_confirmed=True,onset_at=NOW-timedelta(days=i+17)) for i in (1,2)]
 x=input_for(['cough'],[fact('cough')],eps)
 assert not any(z.code=='duration_days' for z in add_derived_episode_facts(x))

@pytest.mark.parametrize('code', ['blood_in_vomit','speech_difficulty','sudden_severe_headache'])
def test_expanded_emergency_override_has_own_regression(code):
 r=assess(REGISTRY,input_for([],[fact(code)]))
 assert r.priority=='P4'

@pytest.mark.parametrize('code', ['blood_in_vomit','speech_difficulty','sudden_severe_headache'])
def test_stale_emergency_event_not_current(code):
 r=assess(REGISTRY,input_for([],[fact(code,time=NOW-timedelta(days=3))]))
 assert r.priority!='P4'

@pytest.mark.parametrize('p', [v for v in REGISTRY.by_id])
def test_all_active_pathways_hold_2026_draft_status(p):
 x=REGISTRY.get(p, include_drafts=True)
 assert x.status=='draft' and x.version=='0.2.0'
 assert x.governance['approval']['clinician_id'] is None

@pytest.mark.parametrize('r',DATA['conditions'],ids=lambda r:r['condition_id'])
def test_disease_association_terms_exist_and_have_terminology_status(r):
 assert r['routed_symptoms'] or r['safety_only_symptoms']
 assert r['candidate_source_ids']
 assert not r['unrouted_symptoms']

# Every alternate routing word must be representable as a present fact.
ROUTES=[(p.id,code) for byver in REGISTRY.by_id.values()
        for ver,p in byver.items() if ver=='0.2.0' and p.id!='global_emergency'
        for code in p.routing.get('symptom_codes',[])]
@pytest.mark.parametrize('pathway_id,code',ROUTES)
def test_pathway_accepts_each_declared_route_concept(pathway_id,code):
 pkg=REGISTRY.get(pathway_id,include_drafts=True)
 result=assess(REGISTRY,input_for([code],[fact(code)]))
 matches=[x for x in result.results if x.pathway_id==pathway_id]
 assert matches, f'failed to route {code} into {pathway_id}'
 assert matches[0].status in {'DECIDED','QUESTION_REQUIRED','INSUFFICIENT_INFORMATION'}

def test_coverage_endpoint_summarizes_no_patient_data():
 r=TestClient(app).get('/api/v1/coverage')
 assert r.status_code==200
 assert r.json()['summary']['condition_entries']==54
 assert 'user_id' not in r.text

def test_no_two_identical_case_ids():
 cases=[json.loads(line) for p in (ROOT/'clinical'/'cases').glob('*.jsonl') for line in p.read_text().splitlines() if line.strip()]
 names=[x['id'] for x in cases]
 assert len(names)==len(set(names))

# Source bibliography: each condition source and every draft rule source must exist.
def test_evidence_references_resolvable():
 sources=yaml.safe_load((ROOT/'clinical'/'evidence'/'sources.yaml').read_text())
 assert all(x['candidate_source_ids'][0] in sources for x in DATA['conditions'])
 assert all(set(rule.evidence)<=set(sources) for p in REGISTRY.by_id.values() for pkg in p.values() for rule in pkg.rules)



def test_nonpathway_knowledge_manifest_matches_real_file_hashes():
    import hashlib
    manifest=json.loads((ROOT/'clinical'/'knowledge_manifest_v0.2.0.json').read_text())
    for rel,meta in manifest['files'].items():
        p=ROOT/rel
        assert meta['sha256']==hashlib.sha256(p.read_bytes()).hexdigest()


def test_decision_contains_knowledge_source_hashes():
    result=assess(REGISTRY,input_for(['cough'],[fact('cough')]))
    assert result.knowledge_sha256
    assert 'concepts/symptoms.yaml' in result.knowledge_sha256
    assert 'evidence/sources.yaml' in result.knowledge_sha256


def test_unknown_pregnancy_cannot_proceed_into_excluded_adult_pathways():
    result=assess(REGISTRY,input_for(['menstrual_irregularity'],[fact('menstrual_irregularity')],pregnant=None))
    assert result.priority is None and result.status=='INSUFFICIENT_INFORMATION'
    assert any('PREGNANCY_STATUS_UNKNOWN' in r.reason_codes for r in result.results)
