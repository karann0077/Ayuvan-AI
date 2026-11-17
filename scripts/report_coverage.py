"""Generate reproducible JSON, CSV, and Markdown coverage reports."""
from pathlib import Path
import csv,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.coverage import build_coverage_report
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'reports'; OUT.mkdir(exist_ok=True)
report=build_coverage_report(BASE)
(OUT/'coverage_v0.2.0.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
with (OUT/'condition_coverage_v0.2.0.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['condition_id','domain','condition','presentation_mode','mapping_status','clinical_readiness','symptom_count','unrouted_symptoms','pathways','engineering_case_count'])
 for r in report['conditions']:
  w.writerow([r['condition_id'],r['domain'],r['name'],r['presentation_mode'],r['mapping_status'],r['clinical_readiness'],r['associated_symptom_count'],'; '.join(r['unrouted_symptoms']),'; '.join(r['pathways']),r['engineering_case_count']])
with (OUT/'symptom_coverage_v0.2.0.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['symptom_code','domains','routing_status','clinical_readiness','pathways','engineering_case_count'])
 for r in report['symptoms']:
  w.writerow([r['code'],'; '.join(r['domains']),r['routing_status'],r['clinical_readiness'],'; '.join(r['route_pathways']),r['engineering_cases_count']])
s=report['summary']
md=['# AYUVAN v0.2.0 — Engineering Coverage Report','','> This is NOT medical validation. All clinical pathways remain draft and are disabled for patient-facing use.','',
    f"- Condition entries mapped: **{s['condition_entries']}** across **{s['domain_count']}** domains",
    f"- Clinical concepts: **{s['symptom_concepts']}**; routed: **{s['symptom_concepts_routed']}**; safety-fact-only: **{s['symptom_concepts_safety_only']}**; supporting-fact-only: **{s['symptom_concepts_supporting_only']}**; vocabulary-only: **{s['symptom_concepts_vocabulary_only']}**",
    f"- Versioned pathway IDs: **{s['draft_pathway_ids']}** (including global emergency)",
    f"- Conditions with no un-routed associated symptom concepts: **{s['condition_entries_with_all_presentations_routed_or_safety_only']}**",
    f"- Software regression cases: **{s['engineering_scenarios']}**; independently clinician-labeled: **0**",
    '- Clinically validated conditions: **0**','',
    '| Condition entry | Domain | Mapping status | Clinical status |','|---|---|---|---|']
for r in report['conditions']:
 md.append(f"| {r['name']} | {r['domain']} | {r['mapping_status']} | {r['clinical_readiness']} |")
md+=['','## Gaps and required action','','1. Independently review each symptom-condition association and source mapping.','2. Clinician-author and approve criteria, timeframes, all question wording and populations.','3. Build and validate child, pregnancy, older/frail, and other high-risk pathways.','4. Evaluate emergency under-triage, over-triage, multilingual negation, episode resolution, temporal correctness and contradictory facts.','5. Map codes to SNOMED CT / ICD-11 only after license verification and terminology expert sign-off.','6. Review software intended purpose and applicable India medical-device and privacy requirements.','7. Do not enable /api/v1/assess before approval, external evaluation, change control, monitoring and regulatory assessment.']
(OUT/'COVERAGE_REPORT.md').write_text('\n'.join(md)+'\n')
print(json.dumps(s,indent=2))
