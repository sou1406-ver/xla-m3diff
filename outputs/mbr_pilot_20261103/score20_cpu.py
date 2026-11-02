"""Offline diagnostics after generation; oracle labels cannot affect candidate generation/ranking."""
from pathlib import Path
import json,pickle,statistics,collections
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
from utility import select
P=Path('/mnt/m3diff/mbr_pilot_20261103');VAL=Path('/mnt/m3diff/r64_val_precheck_20261102');records=[json.loads(x) for x in (P/'results20.jsonl').read_text().splitlines() if x.strip()]
assert len(records)==20 and json.loads((P/'BENCHMARK_DONE.json').read_text())['complete']
cache=pickle.load((P/'train_idf.pkl').open('rb'));tokenizer=PTBTokenizer();token_input={};captions={}
for r in records:
 for method in ['sequential8','batch8']:
  cs=[r['greedy']['caption']]+r['methods'][method]['samples'];captions[(r['id'],method)]=cs
  for i,c in enumerate(cs):token_input[f"{r['id']}|{method}|{i}"]=[{'caption':c}]
tokenized=tokenizer.tokenize(token_input);selected={};utilities={}
for key,cs in captions.items():
 toks=[tokenized[f'{key[0]}|{key[1]}|{i}'][0] for i in range(9)]
 selected[key],utilities[key]=select(toks,cache)
method_times={m:sum(r['methods'][m]['seconds'] for r in records) for m in ['sequential8','batch8']}
chosen=min(method_times,key=method_times.get) # Runtime-only decision, before oracle/quality metrics.
result={'n':20,'chosen_generation_method_by_runtime_only':chosen,'generation_sample_seconds':method_times,'batch_speedup_vs_sequential':method_times['sequential8']/method_times['batch8'],'batch_sizes':dict(collections.Counter(r['methods']['batch8']['effective_batch_size'] for r in records)),'methods':{},'oracle_diagnostic_only':True,'no_reference_labels_used_by_selector':True,'full100_per_domain_reference_DF_used_for_diagnostic_scores':True}
per=[]
for method in ['sequential8','batch8']:
 summary={}
 for domain in ['real','render']:
  rr=[r for r in records if r['domain']==domain];ref=json.loads((VAL/f'{domain}_reference.json').read_text());ids=[x['id'] for x in ref['images']]
  rawrefs={i:[] for i in ids}
  for a in ref['annotations']:rawrefs[a['image_id']].append({'caption':a['caption']})
  gts=tokenizer.tokenize(rawrefs);arm_scores=[]
  for arm in range(9):
   preds={i:[''] for i in ids}
   for r in rr:preds[r['id']]=tokenized[f"{r['id']}|{method}|{arm}"]
   _,scores=Cider().compute_score(gts,preds);arm_scores.append({i:float(s)*100 for i,s in zip(gts.keys(),scores)})
  pairs=[]
  for r in rr:
   cs=captions[(r['id'],method)];idx=selected[(r['id'],method)];ss=[a[r['id']] for a in arm_scores];oracle=max(range(9),key=lambda i:(ss[i],-i))
   row={'id':r['id'],'domain':domain,'method':method,'greedy_cider_x100':ss[0],'selected_index':idx,'mbr_cider_x100':ss[idx],'oracle_index':oracle,'oracle_cider_x100':ss[oracle],'unique_captions':len(set(cs)),'greedy_words':len(cs[0].split()),'mbr_words':len(cs[idx].split()),'greedy':cs[0],'selected_caption':cs[idx],'consensus_utility_scores':utilities[(r['id'],method)]};pairs.append(row);per.append(row)
  def mean(k):return statistics.mean(x[k] for x in pairs)
  summary[domain]={'n':len(pairs),'greedy_CIDEr_x100':mean('greedy_cider_x100'),'MBR_CIDEr_x100':mean('mbr_cider_x100'),'oracle_CIDEr_x100':mean('oracle_cider_x100'),'MBR_delta':mean('mbr_cider_x100')-mean('greedy_cider_x100'),'oracle_delta':mean('oracle_cider_x100')-mean('greedy_cider_x100'),'mean_unique_captions':mean('unique_captions'),'changed_from_greedy':sum(x['selected_index']!=0 and x['selected_caption']!=x['greedy'] for x in pairs),'greedy_mean_words':mean('greedy_words'),'MBR_mean_words':mean('mbr_words'),'greedy_median_words':statistics.median(x['greedy_words'] for x in pairs),'MBR_median_words':statistics.median(x['mbr_words'] for x in pairs)}
 result['methods'][method]=summary
stage=result['methods'][chosen]
result['operational_low_promise_stop']=all(stage[d]['oracle_delta']<=0 and stage[d]['MBR_delta']<=0 for d in ['real','render'])
result['interpretation']='Only10pairs/domain; oracle is a conditional ceiling for these candidate sets, not a prediction or proof about val200. Method chosen only by runtime. Hyperparameters unchanged. Final val200 must regenerate greedy+samples in one session.'
(P/'METRICS20.json').write_text(json.dumps(result,indent=2));(P/'PER_PAIR20.json').write_text(json.dumps(per,indent=2))
print(json.dumps(result,indent=2),flush=True)
