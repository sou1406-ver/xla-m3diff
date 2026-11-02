import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=30);a=p.parse_args()
rows=json.loads((Path(__file__).parent/'results/masked_predictions.json').read_text(encoding='utf8'))
for i,r in list(enumerate(rows))[a.start:a.end]:
 print(f"\n[{i}] {r['id']} ({r['split']})")
 print('C1:',r['candidate_1']);print('C2:',r['candidate_2'])
