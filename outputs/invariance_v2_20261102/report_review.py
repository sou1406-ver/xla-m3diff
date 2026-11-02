"""Decode only complete, caption-bound masked assessments and report all errors."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['initial','new'],default='initial');args=p.parse_args()
def read(n):return json.loads((HERE/n).read_text(encoding='utf8'))
stage=args.stage;ass=read(stage+'_assessments.json');masked=read(stage+'_masked.json');key=read(stage+'_mask_key.json');rubric=read('eval_rubric.json')
assert len(ass['cases'])==len(masked)==96
assert ass['masked_file_sha256']==hashlib.sha256((HERE/(stage+'_masked.json')).read_bytes()).hexdigest()
rows=[]
for case,m in zip(ass['cases'],masked):
    assert case['id']==m['id']
    for label in ['candidate_1','candidate_2']:
        s=case[label];assert s['caption']==m[label]['caption'] and s['raw_sha256']==m[label]['raw_sha256']
        assert all(s[k] in [0,1] for k in ['physical','false_light','wrong_geometry','ack'])
        assert len(set(s['facts']))==len(s['facts']) and all(1<=i<=len(rubric['facts'][m['scene']]) for i in s['facts'])
        rows.append({**{k:m[k] for k in ['id','scene','domain','condition']},'arm':key[m['id']][label],**s})
(HERE/(stage+'_decoded.json')).write_text(json.dumps({'assessment_sha256':hashlib.sha256((HERE/(stage+'_assessments.json')).read_bytes()).hexdigest(),'rows':rows},ensure_ascii=False,indent=2),encoding='utf8')
arms=list(dict.fromkeys(r['arm'] for r in rows));stats={}
for domain in ['all','Real','Render']:
    for group in ['all_synthetic','geometry','identity','brightness','natural']:
        bucket={}
        for arm in arms:
            rs=[r for r in rows if r['arm']==arm and (domain=='all' or r['domain']==domain) and
                ((group=='all_synthetic' and r['condition']!='natural') or
                 (group=='geometry' and r['condition'] in ['zoom_in','zoom_out','roll']) or r['condition']==group)]
            bucket[arm]={'n':len(rs),'physical':sum(r['physical'] for r in rs),'false_light':sum(r['false_light'] for r in rs),
                'wrong_geometry':sum(r['wrong_geometry'] for r in rs),'any_error':sum(bool(r['unsupported']) if r['condition']=='natural' else bool(r['physical'] or r['false_light'] or r['wrong_geometry']) for r in rs),
                'ack':sum(r['ack'] for r in rs),'fact_hits':sum(len(r['facts']) for r in rs),'unsupported_pairs':sum(bool(r['unsupported']) for r in rs),
                'uncertain_pairs':sum(bool(r['uncertain']) for r in rs)}
            if group=='natural':bucket[arm]['possible_facts']=sum(len(rubric['facts'][r['scene']]) for r in rs)
        stats[domain+'/'+group]=bucket
(HERE/(stage+'_metrics.json')).write_text(json.dumps(stats,indent=2))
print(json.dumps({k:v for k,v in stats.items() if k.startswith('all/') or k.endswith('/natural')},indent=2))
