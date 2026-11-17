from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.clinical.types import AssessmentInput, Fact, Episode, FactState
from app.clinical.engine import assess
from app.clinical.registry import Registry, validate_condition
from app.main import app
from app.core.config import get_settings

NOW = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)
REGISTRY = Registry(Path(__file__).resolve().parents[2] / 'clinical' / 'pathways')

def fact(code, state='present', value=None, hour_offset=0, source='patient'):
    return Fact(code=code, state=state, value=value, observed_at=NOW + timedelta(hours=hour_offset),
                source_type=source, source_id='message-1', verification='patient_confirmed')

def inp(symptoms, facts=None, episodes=None, age=28, pregnant=False, desired_versions=None):
    return AssessmentInput(user_id='dev-user', request_id='req-1', as_of=NOW, symptom_codes=symptoms,
                           population={'age_years':age,'pregnant':pregnant,'location_country':'IN'},
                           facts=facts or [], episodes=episodes or [], desired_versions=desired_versions or {})

def run(symptoms, fs=None, **kwargs):
    return assess(REGISTRY, inp(symptoms, fs, **kwargs))


def test_library_has_five_domains_plus_emergency():
    assert len(REGISTRY.by_id) >= 40
    assert {REGISTRY.get(k, include_drafts=True).domain for k in REGISTRY.by_id} >= {
        'respiratory','infectious','gastroenterology','cardiology','endocrinology','shared'}

def test_patient_loader_refuses_unapproved_pathways():
    with pytest.raises(PermissionError):
        REGISTRY.get('adult_cough_in')

def test_draft_approval_gate_cannot_be_bypassed_with_version():
    with pytest.raises(PermissionError):
        REGISTRY.get('adult_cough_in','0.1.0')

def test_no_eval_in_rule_grammar():
    with pytest.raises(ValueError):
        validate_condition({'fact':'cough','op':'__import__','value':'os'}, {'cough'})

@pytest.mark.parametrize('bad', [
 {'fact':'cough','op':'present','execute':'rm -rf /'},
 {'all':[]},
 {'all':[{'fact':'nonsense','op':'present'}]},
 {'not':{'fact':'cough','op':'present'},'fact':'cough'},
])
def test_reject_unsafe_or_ambiguous_dsl(bad):
    with pytest.raises(ValueError):validate_condition(bad, {'cough'})

def test_emergency_override_without_any_symptom_route():
    result = run([], [fact('severe_breathlessness')])
    assert (result.status,result.priority,result.action)==('DECIDED','P4','emergency_help')
    assert len(result.results)==1

def test_chest_pressure_and_breathlessness_emergency():
    res=run(['cough','chest_discomfort'], [fact('chest_pressure'),fact('breathing_difficulty')])
    assert res.priority=='P4'
    assert res.pathway_versions=={'global_emergency':'0.2.0'}

def test_explicit_denial_not_emergency():
    res=run(['cough'], [fact('chest_pressure','absent'),fact('breathing_difficulty','absent'),fact('cough')])
    assert res.priority!='P4'

def test_uncertain_never_defaults_to_p0():
    res=run(['cough'],[fact('cough')])
    assert res.status=='QUESTION_REQUIRED' and res.priority is None

def test_brief_cough_complete_negatives_p0():
    fs=[fact('cough'),fact('duration_days',value=1),fact('breathing_difficulty','absent'),
        fact('blood_in_sputum','absent'),fact('worsening','absent'),fact('functional_impairment','absent')]
    res=run(['cough'],fs)
    assert res.status=='DECIDED' and res.priority=='P0'

def test_cough_15_days_confirmed_p2():
    ep=Episode(episode_id='ep-1',symptom_code='cough',onset_at=NOW-timedelta(days=15),
               onset_confirmed=True,status='active',continuity='continuous')
    res=run(['cough'],[fact('cough')],episodes=[ep])
    assert res.priority=='P2' and 'COUGH_PERSISTENT_NTEP' in res.reason_codes

def test_cough_14_days_does_not_meet_more_than_2_weeks_rule():
    ep=Episode(episode_id='ep-1',symptom_code='cough',onset_at=NOW-timedelta(days=14),
               onset_confirmed=True,status='active',continuity='continuous')
    res=run(['cough'],[fact('cough')],episodes=[ep])
    assert 'COUGH_PERSISTENT_NTEP' not in res.reason_codes

def test_unconfirmed_old_episode_does_not_inflate_duration():
    ep=Episode(episode_id='ep-1',symptom_code='cough',onset_at=NOW-timedelta(days=20),
               onset_confirmed=False,status='active',continuity='unknown')
    fs=[fact('cough'),fact('breathing_difficulty','absent'),fact('blood_in_sputum','absent')]
    res=run(['cough'],fs,episodes=[ep])
    assert res.status=='QUESTION_REQUIRED'
    assert res.question['id']=='COUGH_CONTINUITY'
    assert 'COUGH_PERSISTENT_NTEP' not in res.reason_codes

def test_resolved_then_recurrent_does_not_use_old_onset():
    ep=Episode(episode_id='ep-1',symptom_code='cough',onset_at=NOW-timedelta(days=20),
               resolution_at=NOW-timedelta(days=8),onset_confirmed=True,
               status='active',continuity='resolved_then_recurred')
    res=run(['cough'],[fact('cough')],episodes=[ep])
    assert 'COUGH_PERSISTENT_NTEP' not in res.reason_codes

def test_conflicting_same_time_facts_are_not_treated_as_negative():
    fs=[fact('cough'),fact('duration_days',value=1),fact('breathing_difficulty','absent'),
        fact('breathing_difficulty','present'),fact('blood_in_sputum','absent'),
        fact('worsening','absent'),fact('functional_impairment','absent')]
    res=run(['cough'],fs)
    assert res.priority is None and res.status=='QUESTION_REQUIRED'

def test_time_order_newer_answer_replaces_old_answer():
    fs=[fact('cough'),fact('duration_days',value=1),
        fact('breathing_difficulty','present',hour_offset=-3),fact('breathing_difficulty','absent'),
        fact('blood_in_sputum','absent'),fact('worsening','absent'),fact('functional_impairment','absent')]
    res=run(['cough'],fs)
    assert res.priority=='P0'

def test_stale_emergency_fact_not_current_emergency():
    res=run(['cough'], [fact('cough'),fact('unilateral_weakness',hour_offset=-48)])
    assert res.priority!='P4'

def test_fever_bleeding_rash_p3():
    res=run(['fever'],[fact('fever'),fact('rash_bleeding')])
    assert res.priority=='P3'

def test_abdominal_severe_p3():
    res=run(['abdominal_pain'],[fact('abdominal_pain'),fact('pain_severe')])
    assert res.priority=='P3'

def test_chest_discomfort_prototype_prompt_not_p0():
    res=run(['chest_discomfort'],[fact('chest_discomfort')])
    assert res.priority=='P3'

def test_metabolic_cluster_p2():
    res=run(['frequent_urination','excessive_thirst'],
      [fact('frequent_urination'),fact('excessive_thirst')])
    assert res.priority=='P2'

def test_multi_pathway_most_urgent_wins():
    res=run(['cough','abdominal_pain'], [fact('cough'),fact('abdominal_pain'),fact('pain_severe'),
        fact('duration_days',value=1),fact('blood_in_sputum','absent'),fact('breathing_difficulty','absent'),
        fact('worsening','absent'),fact('functional_impairment','absent')])
    assert res.priority=='P3'
    assert set(res.pathway_versions)=={'global_emergency','adult_cough_in','adult_abdominal_pain_in'}

def test_unknown_other_pathway_blocks_p0_reassurance():
    fs=[fact('cough'),fact('duration_days',value=1),fact('breathing_difficulty','absent'),
        fact('blood_in_sputum','absent'),fact('worsening','absent'),fact('functional_impairment','absent')]
    res=run(['cough','abdominal_pain'],fs)
    assert res.status=='QUESTION_REQUIRED' and res.priority is None

def test_unsupported_age_out_of_scope():
    res=run(['cough'],[fact('cough')],age=6)
    assert res.status=='INSUFFICIENT_INFORMATION' and res.priority is None
    assert any('CHILD_UNSUPPORTED' in p.reason_codes for p in res.results)

def test_pregnancy_unsupported():
    res=run(['abdominal_pain'],[fact('abdominal_pain')],pregnant=True)
    assert res.priority is None and res.status=='INSUFFICIENT_INFORMATION'

def test_unknown_pregnancy_status_requires_verification_for_some_pathways():
    res=run(['fever'],[fact('fever')],pregnant=None)
    assert res.status=='INSUFFICIENT_INFORMATION'

def test_unsupported_symptom_fails_closed():
    res=run(['vision_loss'],[fact('unexplained_eye_symptom')])
    assert res.status=='INSUFFICIENT_INFORMATION'

def test_version_pin_reproducible():
    res=run(['cough'],[fact('cough')],desired_versions={'adult_cough_in':'0.1.0'})
    assert res.pathway_versions['adult_cough_in']=='0.1.0'

def test_api_patient_route_always_disabled():
    client=TestClient(app)
    assert client.post('/api/v1/assess').status_code==503

def test_api_simulator_disabled_by_default(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','test')
    monkeypatch.setenv('ENABLE_PATHWAY_SIMULATOR','false')
    get_settings.cache_clear()
    client=TestClient(app)
    assert client.post('/api/v1/simulate',json=inp(['cough'],[fact('cough')]).model_dump(mode='json')).status_code==403

def test_api_simulator_enabled_local_dev(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','test')
    monkeypatch.setenv('ENABLE_PATHWAY_SIMULATOR','true')
    monkeypatch.setenv('PATHWAY_SIMULATION_KEY','test-pathway-secret-at-least-32-chars')
    get_settings.cache_clear()
    client=TestClient(app)
    res=client.post('/api/v1/simulate',json=inp(['cough'],[fact('cough')]).model_dump(mode='json'),
                    headers={'X-Ayuvan-Simulation-Key':'test-pathway-secret-at-least-32-chars'})
    assert res.status_code==200 and res.json()['simulated'] is True

def test_api_simulator_rejects_missing_key(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','test')
    monkeypatch.setenv('ENABLE_PATHWAY_SIMULATOR','true')
    monkeypatch.setenv('PATHWAY_SIMULATION_KEY','test-pathway-secret-at-least-32-chars')
    get_settings.cache_clear()
    client=TestClient(app)
    assert client.post('/api/v1/simulate',json=inp(['cough']).model_dump(mode='json')).status_code==403

def test_api_simulator_rejects_production_even_with_key(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','production')
    monkeypatch.setenv('ENABLE_PATHWAY_SIMULATOR','true')
    monkeypatch.setenv('PATHWAY_SIMULATION_KEY','test-pathway-secret-at-least-32-chars')
    get_settings.cache_clear()
    client=TestClient(app)
    assert client.post('/api/v1/simulate',json=inp(['cough']).model_dump(mode='json'),
                       headers={'X-Ayuvan-Simulation-Key':'test-pathway-secret-at-least-32-chars'}).status_code==403

def test_audit_record_stores_version_hash_and_replay_input():
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from app.clinical.audit import Base, AssessmentAudit, record_audit
    from app.clinical import storage
    db=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(db)
    request=inp(['cough'],[fact('cough')])
    result=assess(REGISTRY,request)
    record_audit(db,request,result)
    with Session(db) as session:
        row=session.get(AssessmentAudit,result.assessment_id)
        assert row is not None
        assert 'adult_cough_in' in row.pathway_sha256_json
        assert 'source_id' in row.evidence_snapshot_json

def test_clinical_fact_idempotency_and_replay():
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from app.clinical.audit import Base
    from app.clinical.storage import put_episode, put_fact, load_facts
    db=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(db)
    ep=Episode(episode_id='E1',symptom_code='cough')
    with Session(db) as session:
        put_episode(session,'dev-user',ep)
        assert put_fact(session,'dev-user',fact('cough'),'E1') is True
        assert put_fact(session,'dev-user',fact('cough'),'E1') is False
        session.commit()
    with Session(db) as session:
        saved=load_facts(session,'dev-user','E1')
        assert len(saved)==1 and saved[0].code=='cough'

def test_duplicate_fact_mutation_is_rejected():
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from app.clinical.audit import Base
    from app.clinical.storage import put_fact
    db=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(db)
    with Session(db) as session:
        put_fact(session,'dev-user',fact('cough','present'))
        with pytest.raises(ValueError):
            put_fact(session,'dev-user',fact('cough','absent'))

def test_expired_old_negative_is_unknown():
    f=fact('breathing_difficulty','absent')
    expired=f.model_copy(update={'valid_until':NOW-timedelta(days=1)})
    fs=[fact('cough'),fact('duration_days',value=1),expired,
        fact('blood_in_sputum','absent'),fact('worsening','absent'),fact('functional_impairment','absent')]
    res=run(['cough'],fs)
    assert res.priority is None and res.status=='QUESTION_REQUIRED'

def test_yes_button_equals_exact_typed_answer():
    from app.clinical.answers import normalized_answer
    cough=REGISTRY.get('adult_cough_in',include_drafts=True)
    question=next(q for q in cough.questions if q.id=='COUGH_BREATH')
    button=normalized_answer(question,'yes',NOW,'msg1')
    typed=normalized_answer(question,'Yes',NOW,'msg1')
    assert button==typed and button.state==FactState.PRESENT

def test_no_button_is_explicit_denial():
    from app.clinical.answers import normalized_answer
    cough=REGISTRY.get('adult_cough_in',include_drafts=True)
    question=next(q for q in cough.questions if q.id=='COUGH_BREATH')
    assert normalized_answer(question,'no',NOW,'msg1').state==FactState.ABSENT

def test_unclear_typed_answer_never_auto_negated():
    from app.clinical.answers import normalized_answer,NeedsValidatedExtraction
    cough=REGISTRY.get('adult_cough_in',include_drafts=True)
    question=next(q for q in cough.questions if q.id=='COUGH_BREATH')
    with pytest.raises(NeedsValidatedExtraction):
        normalized_answer(question,'I am gasping for air',NOW,'msg1')

def test_answer_number_days_is_validated():
    from app.clinical.answers import normalized_answer,NeedsValidatedExtraction
    cough=REGISTRY.get('adult_cough_in',include_drafts=True)
    question=next(q for q in cough.questions if q.id=='COUGH_DURATION')
    assert normalized_answer(question,'15',NOW,'msg2').value==15
    with pytest.raises(NeedsValidatedExtraction):
        normalized_answer(question,'two weeks',NOW,'msg2')

def test_old_confirmed_chronic_history_can_modify_fresh_emergency_pattern():
    known=fact('known_diabetes',hour_offset=-24*90)
    current=[fact('persistent_vomiting'),fact('unable_to_drink')]
    res=run(['fatigue'],[known,*current])
    assert res.priority=='P4' and 'EMERG_DIABETES_UNABLE_TO_DRINK' in res.reason_codes
