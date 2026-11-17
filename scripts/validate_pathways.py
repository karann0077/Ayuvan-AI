"""Pathway release lint. These checks do not constitute medical validation."""
from pathlib import Path
import sys,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.clinical.registry import Registry
ROOT=Path(__file__).resolve().parents[1]
registry=Registry(ROOT/'clinical'/'pathways')
sources=yaml.safe_load((ROOT/'clinical'/'evidence'/'sources.yaml').read_text())
errors=[]
for name,versions in registry.by_id.items():
    for version,p in versions.items():
        evidence=set(p.governance['references'])
        for rule in p.rules:
            for source in rule.evidence:
                if source not in sources:errors.append(f'{name}:{rule.id}: unknown source {source}')
                if source not in evidence:errors.append(f'{name}:{rule.id}: source not in governance refs {source}')
        rule_ids=[x.id for x in p.rules]
        if len(rule_ids)!=len(set(rule_ids)):errors.append(f'{name}: duplicate rule id')
        question_ids=[x.id for x in p.questions]
        if len(question_ids)!=len(set(question_ids)):errors.append(f'{name}: duplicate question id')
        if 'change_log' not in p.governance:errors.append(f'{name}: change_log missing')
        print(f'{name}@{version} [{p.status}] rules={len(p.rules)} questions={len(p.questions)} sha256={registry.hashes[name,version][:12]}')
if errors:
    print('\n'.join(errors));sys.exit(1)
print('Pathway structural checks PASS (does not establish clinical safety).')
