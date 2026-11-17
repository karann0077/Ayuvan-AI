"""Export every candidate rule with evidence references and missing review status."""
import sys,csv,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.registry import Registry
ROOT=Path(__file__).resolve().parents[1]
REG=Registry(ROOT/'clinical'/'pathways')
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
with (OUT/'rule_source_traceability_v0.2.0.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['pathway_id','version','rule_id','priority','action','timeframe','when_json','evidence_ids','exact_guideline_passage_verified','clinical_reviewer','review_status'])
 for pid in sorted(REG.by_id):
  p=REG.get(pid,include_drafts=True)
  for r in p.rules:
   w.writerow([pid,p.version,r.id,r.priority,r.action,r.timeframe,json.dumps(r.when,sort_keys=True),
               '; '.join(r.evidence),'NO','UNASSIGNED','PENDING'])
print('Generated',OUT/'rule_source_traceability_v0.2.0.csv')
