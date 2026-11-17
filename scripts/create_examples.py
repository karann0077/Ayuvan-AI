"""Stable developer examples for API and documentation."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.types import AssessmentInput,Fact,Episode
from app.clinical.engine import assess
from app.clinical.registry import Registry
BASE=Path(__file__).resolve().parents[1]
DIR=BASE/'examples'
NOW=datetime(2026,11,16,10,0,tzinfo=timezone.utc)
registry=Registry(BASE/'clinical'/'pathways')

def fact(code,state='present',value=None):
    return Fact(code=code,state=state,value=value,observed_at=NOW,
                source_type='patient',source_id='message-001',verification='patient_confirmed')

def payload(name,codes,facts,episodes=None):
    x=AssessmentInput(user_id='DEMO_PATIENT_DO_NOT_USE_REAL_PHI',request_id=name,as_of=NOW,
           population={'age_years':28,'pregnant':False,'location_country':'IN'},
           symptom_codes=codes,facts=facts,episodes=episodes or [])
    (DIR/f'{name}.json').write_text(x.model_dump_json(indent=2),encoding='utf-8')
    y=assess(registry,x)
    (DIR/f'{name}_RESULT.json').write_text(y.model_dump_json(indent=2),encoding='utf-8')
    print(name,'=>',y.status,y.priority,y.action,'question:',y.question['id'] if y.question else None)

payload('mild_cough',['cough'],[fact('cough'),fact('duration_days',value=1),
        fact('breathing_difficulty','absent'),fact('blood_in_sputum','absent'),
        fact('worsening','absent'),fact('functional_impairment','absent')])
payload('confirmed_cough_15_days',['cough'],[fact('cough')],
        [Episode(episode_id='EP-C1',symptom_code='cough',onset_at=NOW-timedelta(days=15),
                  status='active',onset_confirmed=True,continuity='continuous')])
payload('cough_history_continuity_unknown',['cough'],[fact('cough'),
        fact('breathing_difficulty','absent'),fact('blood_in_sputum','absent')],
        [Episode(episode_id='EP-C2',symptom_code='cough',onset_at=NOW-timedelta(days=20),
                 status='uncertain',onset_confirmed=False,continuity='unknown')])
payload('emergency_chest_symptoms',['chest_discomfort'],[
        fact('chest_pressure'),fact('breathing_difficulty'),fact('chest_discomfort')])
payload('fever_bleeding',['fever'],[fact('fever'),fact('rash_bleeding')])
payload('severe_abdominal_pain',['abdominal_pain'],[fact('abdominal_pain'),
        fact('sudden_severe_abdominal_pain')])
payload('metabolic_symptoms',['excessive_thirst','frequent_urination'],[
        fact('excessive_thirst'),fact('frequent_urination')])
