"""Fail-closed pre-release inspection; not itself a regulatory certification process."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.registry import Registry
ROOT=Path(__file__).resolve().parents[1]
registry=Registry(ROOT/'clinical/pathways')
report=[]
for pid in sorted(registry.by_id):
 p=registry.get(pid,include_drafts=True)
 reasons=[]
 if p.status!='approved': reasons.append('CLINICALLY_UNAPPROVED')
 approval=p.governance.get('approval',{})
 if not approval.get('clinician_id'): reasons.append('MISSING_CLINICIAN_APPROVAL')
 if not approval.get('approved_at'): reasons.append('MISSING_APPROVAL_TIMESTAMP')
 if not p.governance.get('review_date'): reasons.append('MISSING_REVIEW_DATE')
 if not approval.get('release_hash'): reasons.append('MISSING_TRUSTED_RELEASE_ATTESTATION')
 if p.scope.get('exclude_pregnancy'):
  reasons.append('PREGNANCY_EXCLUDED_REQUIRES_SEPARATE_PATHWAY')
 report.append({'pathway_id':pid,'version':p.version,'release_eligible':False,'blocks':reasons})
# Stub remains disabled even after manual YAML modification: real deployment must have
# independent clinician adjudication, verified signed release, operational monitoring,
# legal/regulatory decisions, and a different authenticated patient endpoint.
report_path=ROOT/'reports'/'release_gate_v0.2.0.json';report_path.parent.mkdir(exist_ok=True)
report_path.write_text(json.dumps({'release':'0.2.0','patient_deployment_permitted':False,'trustworthy_release_pipeline_integrated':False,
  'independent_clinician_adjudication_completed':False,'regulatory_review_completed':False,'pathways':report},indent=2)+'\n')
print('BLOCKED: v0.2.0 is ENGINEERING SIMULATION ONLY; clinical and regulatory release gates are incomplete.')
print('Detail:',report_path)
sys.exit(1)
