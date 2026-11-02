"""Verify the experiment contract before spending GPU time on training."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
read=lambda n:json.loads((HERE/n).read_text(encoding='utf8'))
a,b=read('train_control.json'),read('train_revised.json');audit=read('data_audit.json')
assert len(a)==len(b)==512
for arm,rows in [('control',a),('revised',b)]:
    assert hashlib.sha256((HERE/f'train_{arm}.json').read_bytes()).hexdigest()==audit['train_hashes'][arm]
    assert sum(r['is_invariance_negative'] for r in rows)==128
    for r in rows:
        assert len(r['image'])==2 and all('/test/' not in p for p in r['image'])
        turns=r['conversations'];assert len(turns)==2 and turns[0]['from']=='human' and turns[1]['from']=='gpt'
        assert turns[0]['value'].count('<image>')==2 and turns[1]['value'].strip()
assert all(x['is_invariance_negative']==y['is_invariance_negative'] for x,y in zip(a,b))
q=read('eval_questions.json');rubric=read('eval_rubric.json');meta=read('eval_manifest.json')
assert len(q)==len(meta)==len({x['id'] for x in q})==96
assert [x['id'] for x in q]==[x['id'] for x in meta]
assert len(rubric['facts'])==16 and all(m['scene'] in rubric['facts'] for m in meta)
assert audit['RGB_overlap_with_excluded']==0
print('PASS:512 records/arm;384 replay/positive+128 negatives;96 eval;zero recorded RGB overlap; hashes and prompt/answer structure valid.')
