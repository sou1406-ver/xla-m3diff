"""Prepare model-name-masked captions, preserving full raw outputs and a private key."""
import argparse,hashlib,json,random,sys
from pathlib import Path
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE.parent/'caption_cleanup_v2'))
from deduplicate_caption_v2 import deduplicate_caption
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['initial','new','all'],default='initial');a=p.parse_args()
arms=['baseline','old_mixed'] if a.stage=='initial' else ['control','revised'] if a.stage=='new' else ['baseline','old_mixed','control','revised']
assert not (HERE/(a.stage+'_assessments.json')).exists(), 'Do not reshuffle a reviewed assessment.'
questions=json.loads((HERE/'eval_questions.json').read_text());meta=json.loads((HERE/'eval_manifest.json').read_text())
raw={}
for arm in arms:
    rows=[json.loads(x) for x in (HERE/(arm+'.jsonl')).read_text().splitlines() if x.strip()]
    assert [r['id'] for r in rows]==[q['id'] for q in questions]
    raw[arm]={r['id']:r for r in rows}
rng=random.Random(2026110203) if a.stage=='initial' else random.SystemRandom();masked=[];key={}
for m in meta:
    shuffled=arms[:];rng.shuffle(shuffled);row=dict(m);mapping={}
    for i,arm in enumerate(shuffled):
        label='candidate_'+str(i+1);caption=raw[arm][m['id']]['caption']
        clean,audit=deduplicate_caption(caption)
        row[label]={'caption':clean,'raw_sha256':hashlib.sha256(caption.encode()).hexdigest(),'cleanup':audit}
        mapping[label]=arm
    masked.append(row);key[m['id']]=mapping
(HERE/(a.stage+'_masked.json')).write_text(json.dumps(masked,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/(a.stage+'_mask_key.json')).write_text(json.dumps(key,indent=2),encoding='utf8')
print('Prepared masked captions',len(masked),'models',len(arms))
