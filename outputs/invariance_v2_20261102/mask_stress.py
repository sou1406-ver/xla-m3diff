import hashlib,json,random,sys,zipfile
from pathlib import Path
HERE=Path(__file__).parent;folder=HERE/'positive_stress'
assert not (folder/'assessments.json').exists(), 'Do not reshuffle reviewed stress captions.'
sys.path.insert(0,str(HERE.parent/'caption_cleanup_v2'))
from deduplicate_caption_v2 import deduplicate_caption
with zipfile.ZipFile(HERE/'positive_stress_results.zip') as z:
    for name in z.namelist():
        target=(HERE/name).resolve();assert target.is_relative_to(folder.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
arms=['baseline','old_mixed','control','revised'];raw={}
meta=json.loads((folder/'manifest.json').read_text());assert len(meta)==16
for a in arms:
    rows=[json.loads(l) for l in (folder/(a+'.jsonl')).read_text().splitlines() if l.strip()]
    assert [r['id'] for r in rows]==[m['id'] for m in meta];raw[a]={r['id']:r for r in rows}
rng=random.SystemRandom();masked=[];key={}
for m in meta:
    names=arms[:];rng.shuffle(names);r=dict(m);key[m['id']]={}
    for i,a in enumerate(names):
        label=f'candidate_{i+1}';cap=raw[a][m['id']]['caption'];clean,audit=deduplicate_caption(cap)
        r[label]={'caption':clean,'raw_sha256':hashlib.sha256(cap.encode()).hexdigest(),'cleanup':audit};key[m['id']][label]=a
    masked.append(r)
(folder/'masked.json').write_text(json.dumps(masked,ensure_ascii=False,indent=2),encoding='utf8')
(folder/'mask_key.json').write_text(json.dumps(key,indent=2))
for r in masked: print(json.dumps({'scene':r['scene'],**{k:v['caption'] for k,v in r.items() if k.startswith('candidate_')}},ensure_ascii=False))
