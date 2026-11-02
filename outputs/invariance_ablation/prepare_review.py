"""Three-way masked review; reuse only identical questions and whole captions."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
source_questions={q['id']:q for q in load(ROOT.parent/'invariance_sft/results/eval_questions.json')}
for q in load(ROOT/'results/eval_questions.json'):assert q==source_questions[q['id']]
lookup={}
for folder in ['invariance_sft','precision_audit']:
 for r in load(ROOT.parent/folder/'masked_assessments.json')['cases']:
  for c in [1,2]:
   s=r[f'candidate_{c}'];lookup.setdefault((r['id'],s['caption']),[]).append(s)
cases=[];pending=[];reused=0
for i,p in enumerate(load(ROOT/'results/masked_predictions.json')):
 r={'id':p['id'],'index':i}
 for c in [1,2,3]:
  name=f'candidate_{c}';caption=p[name];matches=lookup.get((p['id'],caption),[])
  if matches:
   assert all(all(m[f]==matches[0][f] for f in ['fp','ack','illum','identity_diff','facts','suppression']) for m in matches)
   r[name]={**matches[0],'annotation_source':'exact_prior_case_question_caption'};reused+=1
  else:
   r[name]=None;pending.append({'index':i,'candidate':c,**{k:p[k] for k in ['id','scene','cohort','condition','split']},'caption':caption})
 cases.append(r)
obj={'reviewer':'Codex assistant; not independent human adjudication','rule':'Same question dictionary, same ID and entire displayed caption required for reuse. New captions manually reviewed before current key opened.','reused_candidate_annotations':reused,'cases':cases}
(ROOT/'review_working.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'pending_review.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2),encoding='utf8')
print({'total':len(cases)*3,'reused':reused,'new':len(pending)})
