import json
from pathlib import Path
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(ROOT/'results/eval_questions.json')==load(ROOT/'eval_questions.json')
lookup={}
for folder in ['invariance_sft','precision_audit','invariance_ablation']:
 qs={q['id']:q for q in load(ROOT.parent/folder/('comparison_results/eval_questions.json' if folder=='precision_audit' else 'results/eval_questions.json'))}
 for q in load(ROOT/'eval_questions.json'):assert q==qs[q['id']]
 for r in load(ROOT.parent/folder/'masked_assessments.json')['cases']:
  for key,s in r.items():
   if key.startswith('candidate_'):lookup.setdefault((r['id'],s['caption']),[]).append(s)
preds=load(ROOT/'results/masked_predictions.json');cases=[];pending=[];reused=0
for i,p in enumerate(preds):
 r={'id':p['id'],'index':i}
 for c in [1,2]:
  key=f'candidate_{c}';matches=lookup.get((p['id'],p[key]),[])
  if matches:
   assert all(all(m[f]==matches[0][f] for f in ['fp','illum','ack','identity_diff','facts','suppression']) for m in matches)
   r[key]={**matches[0],'annotation_source':'exact_prior_case_question_caption'};reused+=1
  else:r[key]=None;pending.append({'index':i,'candidate':c,**{k:p[k] for k in ['id','scene','cohort','split','condition']},'caption':p[key]})
 cases.append(r)
work={'reviewer':'Codex assistant, not independent human ground truth','rule':'Identical entire question, ID and displayed caption for reuse; all new captions manually reviewed before balanced key opened.','reused_candidate_annotations':reused,'cases':cases}
for n,v in [('review_working.json',work),('pending_review.json',pending)]: (ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
print({'total':144,'reused':reused,'manual_remaining':len(pending)})
