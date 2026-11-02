import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;folder=HERE/'positive_stress'
read=lambda n:json.loads((folder/n).read_text(encoding='utf8'))
a=read('assessments.json');masked=read('masked.json');key=read('mask_key.json');rubric=json.loads((HERE/'eval_rubric.json').read_text())
assert a['masked_sha256']==hashlib.sha256((folder/'masked.json').read_bytes()).hexdigest()
rows=[]
for r,m in zip(a['cases'],masked):
    assert r['id']==m['id']
    for i in range(1,5):
        k=f'candidate_{i}';s=r[k];assert s['caption']==m[k]['caption'] and s['raw_sha256']==m[k]['raw_sha256']
        assert len(s['facts'])==len(set(s['facts'])) and all(1<=f<=len(rubric['facts'][r['scene']]) for f in s['facts'])
        rows.append({'id':r['id'],'scene':r['scene'],'domain':r['domain'],'arm':key[r['id']][k],**s})
assert len(rows)==64
(folder/'decoded.json').write_text(json.dumps({'assessment_sha256':hashlib.sha256((folder/'assessments.json').read_bytes()).hexdigest(),'rows':rows},ensure_ascii=False,indent=2),encoding='utf8')
stats={}
for domain in ['all','Real','Render']:
    stats[domain]={}
    for arm in ['baseline','old_mixed','control','revised']:
        rs=[r for r in rows if r['arm']==arm and (domain=='all' or r['domain']==domain)]
        stats[domain][arm]={'n':len(rs),'fact_hits':sum(len(r['facts']) for r in rs),'possible_facts':sum(len(rubric['facts'][r['scene']]) for r in rs),
                           'unsupported_pairs':sum(bool(r['unsupported']) for r in rs),'uncertain_pairs':sum(bool(r['uncertain']) for r in rs),
                           'display_ack':sum(r['display_ack'] for r in rs)}
(folder/'metrics.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
