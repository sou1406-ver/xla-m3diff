"""Prepare the prelocked Real review while Render runs; no reference metric is computed."""
from pathlib import Path
import json,pickle,random,hashlib
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from utility import select
ROOT=Path('/mnt/m3diff/mbr_pilot_20261103');P=ROOT/'val200'
records=[json.loads(x) for x in (P/'results200.jsonl').read_text().splitlines() if x.strip()];rr=[r for r in records if r['domain']=='real'];assert len(rr)==100
assert hashlib.sha256((ROOT/'train_idf.pkl').read_bytes()).hexdigest()==json.loads((ROOT/'CPU_READY.json').read_text())['train_idf_sha256']
cache=pickle.load((ROOT/'train_idf.pkl').open('rb'));caps={r['id']:[r['greedy']['caption']]+r['methods']['batch8']['samples'] for r in rr};tok=PTBTokenizer().tokenize({f'{i}|{j}':[{'caption':c}] for i,cs in caps.items() for j,c in enumerate(cs)})
chosen={i:select([tok[f'{i}|{j}'][0] for j in range(9)],cache)[0] for i in caps};changed=sorted([i for i,cs in caps.items() if cs[0]!=cs[chosen[i]]]);random.Random(20261106).shuffle(changed)
meta={r['id']:r for r in json.loads((P/'selection200.json').read_text())};coin=random.Random(20261108);rows=[];mapping=[]
for i in changed[:20]:
 cs=caps[i];j=chosen[i];swap=bool(coin.getrandbits(1));a,b=(cs[j],cs[0]) if swap else (cs[0],cs[j])
 rows.append({'id':i,'image':meta[i]['image'],'caption_A':a,'caption_B':b,'reference_for_review_only':meta[i]['caption']});mapping.append({'id':i,'A':'MBR' if swap else 'greedy','B':'greedy' if swap else 'MBR','selected_index':j})
(P/'PRE_REVIEW_REAL.json').write_text(json.dumps({'phase':'before val200 metric computation','selection':'20changed Real IDs,seed20261106; matches final review-selection rule','rows':rows},indent=2));(P/'PRE_REVIEW_REAL_MAPPING.json').write_text(json.dumps(mapping,indent=2));print('Prepared masked20Real review, no CIDEr reference scoring.',flush=True)
