from pathlib import Path
import json,pickle,hashlib,statistics,random,csv
import numpy as np
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
from utility import select
ROOT=Path('/mnt/m3diff/mbr_pilot_20261103');P=ROOT/'val200';VAL=Path('/mnt/m3diff/r64_val_precheck_20261102')
assert json.loads((P/'VAL_DONE.json').read_text())['complete']
records=[json.loads(x) for x in (P/'results200.jsonl').read_text().splitlines() if x.strip()];assert len(records)==len({x['id'] for x in records})==200
questions=json.loads((P/'questions200.json').read_text());assert [x['id'] for x in records]==[x['id'] for x in questions]
assert hashlib.sha256((ROOT/'train_idf.pkl').read_bytes()).hexdigest()==json.loads((ROOT/'CPU_READY.json').read_text())['train_idf_sha256']
cache=pickle.load((ROOT/'train_idf.pkl').open('rb'));ptb=PTBTokenizer();caps={r['id']:[r['greedy']['caption']]+r['methods']['batch8']['samples'] for r in records}
tokenized=ptb.tokenize({f'{i}|{j}':[{'caption':c}] for i,cs in caps.items() for j,c in enumerate(cs)})
selected={};utility={}
for i,cs in caps.items():selected[i],utility[i]=select([tokenized[f'{i}|{j}'][0] for j in range(9)],cache)
# All selections complete before opening any evaluation reference.
metadata={x['id']:x for x in json.loads((P/'selection200.json').read_text())};per=[];summary={};rng=random.Random(20261107)
for domain in ['real','render']:
 rr=[r for r in records if r['domain']==domain];ref=json.loads((VAL/f'{domain}_reference.json').read_text());g={x['id']:[] for x in ref['images']}
 for a in ref['annotations']:g[a['image_id']].append({'caption':a['caption']})
 g=ptb.tokenize(g);assert len(g)==len(rr)==100;scores=[]
 for arm in range(9):
  pred={i:tokenized[f'{i}|{arm}'] for i in g};_,ss=Cider().compute_score(g,pred);scores.append(dict(zip(g.keys(),[float(s)*100 for s in ss])))
 rows=[]
 for r in rr:
  i=r['id'];j=selected[i];ss=[x[i] for x in scores];oracle=max(range(9),key=lambda k:(ss[k],-k));cs=caps[i]
  row={'id':i,'domain':domain,'image_component':metadata[i]['image_component'],'greedy_cider_x100':ss[0],'MBR_cider_x100':ss[j],'delta':ss[j]-ss[0],'oracle_cider_x100':ss[oracle],'selected_index':j,'oracle_index':oracle,'unique_captions':len(set(cs)),'greedy_words':len(cs[0].split()),'MBR_words':len(cs[j].split()),'greedy':cs[0],'MBR':cs[j],'utility':utility[i]};rows.append(row);per.append(row)
 groups={}
 for x in rows:groups.setdefault(x['image_component'],[]).append(x['delta'])
 keys=sorted(groups);boot=[]
 for _ in range(5000):
  sample=[v for k in rng.choices(keys,k=len(keys)) for v in groups[k]];boot.append(statistics.mean(sample))
 mean=lambda k:statistics.mean(x[k] for x in rows)
 summary[domain]={'n':100,'image_components':len(groups),'greedy_CIDEr_x100':mean('greedy_cider_x100'),'MBR_CIDEr_x100':mean('MBR_cider_x100'),'delta':mean('delta'),'oracle_CIDEr_x100':mean('oracle_cider_x100'),'oracle_delta':mean('oracle_cider_x100')-mean('greedy_cider_x100'),'gate_pass':mean('delta')>=1.0,'descriptive_cluster_bootstrap_fixedDF_CI95':np.percentile(boot,[2.5,97.5]).tolist(),'greedy_mean_words':mean('greedy_words'),'MBR_mean_words':mean('MBR_words'),'greedy_median_words':statistics.median(x['greedy_words'] for x in rows),'MBR_median_words':statistics.median(x['MBR_words'] for x in rows),'mean_unique_captions':mean('unique_captions'),'changed_from_greedy':sum(x['greedy']!=x['MBR'] for x in rows)}
result={'domains':summary,'all_gates_passed':all(x['gate_pass'] for x in summary.values()),'gate':'delta>=1.0CIDEr_x100 in BOTHdomains,unrounded','oracle_diagnostic_only':True,'selector_trainIDF_only':True,'CI_interpretation':'Descriptive cluster bootstrap over image-connected groups, conditional on fixed100-reference DF; not a full re-tokenization/recomputation of CIDEr DF per bootstrap sample. Gate uses prelocked point thresholds, not CI.','full_test_run':False,'qualitative_review_complete':False}
(P/'METRICS.json').write_text(json.dumps(result,indent=2));(P/'PER_PAIR.json').write_text(json.dumps(per,indent=2))
review=[];rand=random.Random(20261106)
if result['all_gates_passed']:
 for domain in ['real','render']:
  changed=sorted([x for x in per if x['domain']==domain and x['greedy']!=x['MBR']],key=lambda x:x['id']);rand.shuffle(changed);review+=changed[:20]
 (P/'REVIEW_SELECTION.json').write_text(json.dumps({'method':'up to20changed/domain,seed20261106,not selected by favourable scores','rows':review},indent=2))
decision={'complete':True,'decision':'REVIEW_AND_BUDGET_ADMISSION_BEFORE_FULL' if result['all_gates_passed'] else 'STOP_FAILED_VAL_GATE','no_training':True,'full_test_run':False}
(P/'DECISION.json').write_text(json.dumps(decision,indent=2));print(json.dumps(result,indent=2),flush=True)
