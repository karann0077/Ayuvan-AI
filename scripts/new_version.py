"""Create a new unapproved draft version; never edit an approved release in place."""
from pathlib import Path
import argparse,yaml
def Version(v):
    parts=v.split(".")
    if len(parts)!=3 or not all(p.isdigit() for p in parts): raise ValueError("Semver X.Y.Z required")
    return tuple(map(int,parts))

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Create next immutable-pathway candidate')
parser.add_argument('pathway_id')
parser.add_argument('new_version')
parser.add_argument('--reason',required=True)
a=parser.parse_args()
pathways=ROOT/'clinical'/'pathways'
existing=[]
for p in pathways.glob(f'{a.pathway_id}_v*.yaml'):
    x=yaml.safe_load(p.read_text())
    if x['id']==a.pathway_id: existing.append((Version(x['version']),x))
if not existing:raise SystemExit('Unknown pathway ID')
old_v, content=max(existing,key=lambda x:x[0])
if Version(a.new_version)<=old_v:raise SystemExit('New version must be greater than existing')
dest=pathways/f'{a.pathway_id}_v{a.new_version}.yaml'
if dest.exists():raise SystemExit('Refusing to overwrite existing version')
content['version']=a.new_version
content['status']='draft'
content['governance']['approval']={'clinician_id':None,'approved_at':None,'release_hash':None}
content['governance']['change_log'].append({'version':a.new_version,'change':a.reason})
content['governance']['rollback_version']='.'.join(map(str,old_v))
dest.write_text(yaml.safe_dump(content,sort_keys=False,allow_unicode=True),encoding='utf-8')
print(dest)
