"""Capture non-pathway source versions for decision replay and reproducibility."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
files=['clinical/concepts/symptoms.yaml','clinical/concepts/facts.yaml',
       'clinical/concepts/condition_presentation_map.yaml',
       'clinical/concepts/disease_catalog.yaml','clinical/evidence/sources.yaml']
manifest={'version':'0.2.0','status':'UNREVIEWED_DRAFT','jurisdiction':'IN','files':{}}
for f in files:
 p=ROOT/f
 manifest['files'][f]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes':p.stat().st_size}
out=ROOT/'clinical'/'knowledge_manifest_v0.2.0.json'
out.write_text(json.dumps(manifest,indent=2)+'\n')
print('Knowledge manifest generated:',out)
