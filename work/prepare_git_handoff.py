from pathlib import Path
import json, shutil, hashlib, re

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'git-publish'
allowed = {'.py', '.md', '.json', '.jsonl', '.csv', '.toml', '.txt', '.ps1', '.ipynb'}
records = []
excluded = []
sources = list((ROOT / 'outputs').rglob('*')) + list((ROOT / 'notebooks').rglob('*.ipynb'))
sources += [p for p in (ROOT / 'work').glob('*') if p.suffix in allowed and p.is_file()]
for src in sources:
    if not src.is_file():
        continue
    rel = src.relative_to(ROOT)
    if any(p in {'.modal-client', '__pycache__', '.git'} for p in rel.parts) or src.suffix.lower() not in allowed:
        excluded.append(str(rel).replace('\\', '/'))
        continue
    target = DEST / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = src.read_bytes()
    action = 'byte-identical'
    if src.suffix == '.ipynb':
        nb = json.loads(raw)
        for cell in nb['cells']:
            if cell.get('cell_type') == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
            cell.get('metadata', {}).pop('execution', None)
        nb.get('metadata', {}).pop('widgets', None)
        raw = (json.dumps(nb, ensure_ascii=False, indent=1) + '\n').encode('utf-8')
        action = 'notebook outputs/execution metadata removed'
    target.write_bytes(raw)
    records.append({'path': rel.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'action': action})
(DEST / 'docs').mkdir(exist_ok=True)
(DEST / 'docs' / 'GIT_EXPORT_MANIFEST.json').write_text(json.dumps({'purpose': 'Selected source and text evidence; originals unchanged. Historical evidence manifests may reference deliberately excluded binaries.', 'files': records, 'excluded_extensions': ['model weights', 'archives', 'images', 'environments', 'logs', 'rendered reports'], 'excluded_file_count': len(excluded)}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'files':len(records), 'bytes':sum(r['bytes'] for r in records), 'notebooks':sum(r['action']!='byte-identical' for r in records)}))
