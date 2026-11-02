import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--stage',default='initial');p.add_argument('--domain',choices=['Real','Render']);p.add_argument('--natural',action='store_true');a=p.parse_args()
root=Path(__file__).parent
for r in json.loads((root/(a.stage+'_masked.json')).read_text()):
    if a.domain and r['domain']!=a.domain:continue
    if (r['condition']=='natural')!=a.natural:continue
    print(json.dumps({'id':r['id'],**{k:v['caption'] for k,v in r.items() if k.startswith('candidate_')}},ensure_ascii=False))
