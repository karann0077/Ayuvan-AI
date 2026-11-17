from pathlib import Path
from datetime import datetime,timedelta,timezone
import json
import pytest
from app.clinical.registry import Registry
from app.clinical.types import AssessmentInput,Fact,Episode
from app.clinical.engine import assess
ROOT=Path(__file__).resolve().parents[2]
REGISTRY=Registry(ROOT/'clinical'/'pathways')
NOW=datetime(2026,11,16,10,0,tzinfo=timezone.utc)

def cases():
    return [json.loads(line) for p in sorted((ROOT/'clinical'/'cases').glob('*.jsonl'))
            for line in p.read_text().splitlines() if line.strip()]

@pytest.mark.parametrize('case',cases(),ids=lambda x:x['id'])
def test_clinical_case(case):
    facts=[Fact(code=x['code'],state=x['state'],value=x.get('value'),observed_at=NOW,
                source_type='patient',source_id=f"case-{case['id']}") for x in case['facts']]
    episodes=[Episode(episode_id=x['episode_id'],symptom_code=x['symptom_code'],
                     onset_at=NOW-timedelta(days=x['onset_days_ago']),status=x['status'],
                     continuity=x['continuity'],onset_confirmed=x['onset_confirmed'])
              for x in case.get('episodes',[])]
    input=AssessmentInput(user_id='TEST',request_id=case['id'],as_of=NOW,
          population={'age_years':32,'pregnant':False,'location_country':'IN'},
          symptom_codes=case['symptom_codes'],facts=facts,episodes=episodes)
    result=assess(REGISTRY,input)
    exp=case['expected']
    assert (result.status,result.priority,result.action)==(exp['status'],exp['priority'],exp['action'])
