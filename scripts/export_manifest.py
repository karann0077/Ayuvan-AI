from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.registry import Registry
ROOT=Path(__file__).resolve().parents[1]
r=Registry(ROOT/'clinical/pathways')
manifest={
 'release_state':'engineering_draft_not_for_patient_use',
 'packages':[{'id':id,'version':ver,'sha256':r.hashes[id,ver],
              'status':p.status,'domain':p.domain,'rules':len(p.rules),'questions':len(p.questions)}
             for id,versions in sorted(r.by_id.items()) for ver,p in sorted(versions.items())]
}
(ROOT/'clinical/manifest.draft.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Wrote manifest for',len(manifest['packages']),'draft packages')
