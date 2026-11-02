from pathlib import Path
import json,collections,hashlib
HERE=Path(__file__).parent
records=json.loads((HERE/'data/train.json').read_text(encoding='utf-8'));syn=[json.loads(l) for l in (HERE/'data/synthetic_manifest.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()];replay=json.loads((HERE/'data/replay_manifest.json').read_text(encoding='utf-8'))
assert len(records)==len({r['id'] for r in records})==7200
assert len(syn)==len({r['id'] for r in syn})==len({tuple(r['rgb_sha256']) for r in syn})==1800
assert len(replay)==len({r['id'] for r in replay})==len({tuple(r['image']) for r in replay})==5400
assert collections.Counter(r['subset'] for r in replay)=={'real':3039,'render':2361}
val=json.loads((HERE.parent/'r64_val_precheck_20261102/IMAGE_MANIFEST.json').read_text());vh={r['rgb_sha256'] for r in val};vp={r['path'] for r in val}
source_hashes=json.loads((HERE/'TRAIN_SOURCE_RGB_HASHES.json').read_text())
assert not any(p in vp or source_hashes[p] in vh for r in replay for p in r['image'])
assert not any(h in vh for r in syn for h in r['rgb_sha256'])
assert not any(r['source_image_rgb_sha256'] in vh for r in syn)
policy=json.loads((HERE/'CAPTION_POLICY.json').read_text());allowed={p for a in policy['camera_prefixes'].values() for p in a}
byid={r['id']:r for r in records}
for r in syn:
    assert byid[r['id']]['conversations'][-1]['value']==r['caption']
    if r['kind'].startswith('camera'):
        prefix=r['metadata']['camera_prefix'];assert prefix in allowed and r['caption'].startswith(prefix)
multi=[r for r in syn if r['kind']=='multi_object'];assert len(multi)==300
assert all(len(r['metadata']['operations']) in [2,3] for r in multi)
assert all(r['caption'].count('.')>=2 for r in multi)
assert sum(r['kind']=='single_color' or r['kind']=='multi_object' for r in syn)==600
result={'records':7200,'unique_replay_pairs':5400,'unique_synthetic_rgb_pairs':1800,'selected_val_path_matches':0,'selected_val_raw_rgb_matches':0,'selected_val_generated_rgb_matches':0,'multi_records':300,'multi_3_edits':sum(len(r['metadata']['operations'])==3 for r in multi),'multi_mean_words':sum(r['word_count'] for r in multi)/300,'camera_templates_valid':True,'train_json_sha256':hashlib.sha256((HERE/'data/train.json').read_bytes()).hexdigest(),'image_review':'PENDING visual check32examples before DATA_APPROVED'}
(HERE/'VALIDATED_DATA.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
