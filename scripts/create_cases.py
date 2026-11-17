from pathlib import Path
import json
CASES=Path(__file__).resolve().parents[1] / 'clinical' / 'cases'

def f(code,state='present',value=None): return {'code':code,'state':state,'value':value}
def c(id,symptoms,facts,status,priority=None,action=None,episodes=None):
    return {'id':id,'symptom_codes':symptoms,'facts':facts,'episodes':episodes or [],
            'expected':{'status':status,'priority':priority,'action':action}}

def episode(continuity,age_days,confirmed=True,status='active'):
    return [{'episode_id':'EP1','symptom_code':'cough','onset_days_ago':age_days,
             'continuity':continuity,'status':status,'onset_confirmed':confirmed}]

cough=[
 c('cough_isolated_mild',['cough'],[f('cough'),f('duration_days','present',1),f('breathing_difficulty','absent'),f('blood_in_sputum','absent'),f('worsening','absent'),f('functional_impairment','absent')],'DECIDED','P0','monitor_with_safety_net'),
 c('cough_15_days_confirmed',['cough'],[f('cough')],'DECIDED','P2','professional_assessment',episode('continuous',15)),
 c('cough_14_days_not_persistent',['cough'],[f('cough')],'QUESTION_REQUIRED',None,None,episode('continuous',14)),
 c('cough_old_history_unverified',['cough'],[f('cough'),f('breathing_difficulty','absent'),f('blood_in_sputum','absent')],'QUESTION_REQUIRED',None,None,episode('unknown',18,False)),
 c('cough_resolved_returned',['cough'],[f('cough')],'QUESTION_REQUIRED',None,None,episode('resolved_then_recurred',20)),
 c('cough_blood',['cough'],[f('cough'),f('blood_in_sputum')],'DECIDED','P3','prompt_clinical_assessment'),
 c('cough_unknown',['cough'],[f('cough')],'QUESTION_REQUIRED'),
 c('cough_emergency',['cough'],[f('severe_breathlessness')],'DECIDED','P4','emergency_help'),
]
fever=[
 c('fever_very_brief_no_flags',['fever'],[f('fever'),f('fever_duration_days','present',1),f('worsening','absent'),f('dehydration_signs','absent'),f('confusion_severe','absent'),f('rash_bleeding','absent'),f('unable_to_drink','absent')],'DECIDED','P0','monitor_with_safety_net'),
 c('fever_with_bleeding',['fever'],[f('fever'),f('rash_bleeding')],'DECIDED','P3','prompt_clinical_assessment'),
 c('fever_can_not_drink',['fever'],[f('fever'),f('unable_to_drink')],'DECIDED','P3','prompt_clinical_assessment'),
 c('fever_worse_day4',['fever'],[f('fever'),f('fever_duration_days','present',4),f('worsening')],'DECIDED','P2','professional_assessment'),
 c('fever_no_answers',['fever'],[f('fever')],'QUESTION_REQUIRED'),
]
abd=[
 c('abd_mild_brief',['abdominal_pain'],[f('abdominal_pain'),f('pain_duration_days','present',1),f('pain_severe','absent'),f('sudden_severe_abdominal_pain','absent'),f('pain_worsening','absent'),f('black_or_bloody_stool','absent'),f('persistent_vomiting','absent')],'DECIDED','P0','monitor_with_safety_net'),
 c('abd_blood',['abdominal_pain'],[f('abdominal_pain'),f('black_or_bloody_stool')],'DECIDED','P3','prompt_clinical_assessment'),
 c('abd_severe',['abdominal_pain'],[f('abdominal_pain'),f('pain_severe')],'DECIDED','P3','prompt_clinical_assessment'),
 c('abd_worsening_and_impairment',['abdominal_pain'],[f('abdominal_pain'),f('pain_worsening'),f('functional_impairment')],'DECIDED','P2','professional_assessment'),
 c('abd_unassessed',['abdominal_pain'],[f('abdominal_pain')],'QUESTION_REQUIRED'),
]
chest=[
 c('chest_discomfort_only',['chest_discomfort'],[f('chest_discomfort')],'DECIDED','P3','prompt_clinical_assessment'),
 c('chest_and_sweat',['chest_discomfort'],[f('chest_discomfort'),f('cold_sweat')],'DECIDED','P4','emergency_help'),
 c('chest_pressure_and_dyspnea',['chest_discomfort'],[f('chest_pressure'),f('breathing_difficulty')],'DECIDED','P4','emergency_help'),
 c('palpitations_alone',['palpitations'],[f('palpitations'),f('chest_discomfort','absent'),f('fainting','absent'),f('breathing_difficulty','absent'),f('cold_sweat','absent')],'DECIDED','P1','monitor_or_clarify'),
 c('palpitations_info_missing',['palpitations'],[f('palpitations')],'QUESTION_REQUIRED'),
]
metabolic=[
 c('thirst_plus_urination',['excessive_thirst','frequent_urination'],[f('excessive_thirst'),f('frequent_urination')],'DECIDED','P2','professional_assessment'),
 c('classic_cluster',['excessive_thirst','frequent_urination','unexplained_weight_change'],[f('excessive_thirst'),f('frequent_urination'),f('unexplained_weight_change')],'DECIDED','P2','professional_assessment'),
 c('known_diabetes_vomiting',['fatigue'],[f('known_diabetes'),f('persistent_vomiting')],'DECIDED','P3','prompt_clinical_assessment'),
 c('fatigue_ambiguous',['fatigue'],[f('fatigue')],'QUESTION_REQUIRED'),
]
common=[
 c('no_route_no_emergency',['vision_loss'],[f('vision_loss')],'INSUFFICIENT_INFORMATION'),
 c('emergency_no_route',['vision_loss'],[f('severe_breathlessness')],'DECIDED','P4','emergency_help'),
]
for name,cases in [('cough',cough),('fever',fever),('abdominal',abd),('chest',chest),('metabolic',metabolic),('common',common)]:
    (CASES/f'{name}.jsonl').write_text(''.join(json.dumps(case)+'\n' for case in cases),encoding='utf-8')
print('created',sum(map(len,[cough,fever,abd,chest,metabolic,common])),'test case records')
