import argparse,json
from pathlib import Path
ROOT=Path(__file__).parent;p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=30);args=p.parse_args()
preds=json.loads((ROOT/'comparison_results/masked_predictions.json').read_text());work=json.loads((ROOT/'review_working.json').read_text())['cases']
for i in range(args.start,min(args.end,len(preds))):
    r=preds[i];pending=[c for c in [1,2] if work[i][f'candidate_{c}'] is None]
    if not pending:continue
    print(f"\n[{i}] {r['id']}")
    for c in pending:print(f'C{c}:',r[f'candidate_{c}'])
