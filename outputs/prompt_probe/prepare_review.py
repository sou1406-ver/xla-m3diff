from pathlib import Path
import json
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
questions={q['id']:q for q in load(ROOT/'eval_questions.json')};assert load(ROOT/'results/eval_questions.json')==list(questions.values())
meta={r['id']:r for r in load(ROOT/'eval_manifest.json')};lookup={}
for folder in ['invariance_ablation','prompt_balanced_sft']:
 oldq={q['id']:q for q in load(ROOT.parent/folder/'results/eval_questions.json')}
 for r in load(ROOT.parent/folder/'masked_assessments.json')['cases']:
  for k,s in r.items():
   if k.startswith('candidate_'):
    q=oldq[r['id']];lookup.setdefault((r['id'],json.dumps({'image':q['image'],'conversations':q['conversations']},sort_keys=True),s['caption']),[]).append(s)
preds=load(ROOT/'results/masked_predictions.json');cases=[];reused=0
for i,p in enumerate(preds):
 q=questions[p['id']];case={'id':p['id'],'index':i}
 for c in [1,2,3]:
  k=f'candidate_{c}';matches=lookup.get((meta[p['id']]['source_case_id'],json.dumps({'image':q['image'],'conversations':q['conversations']},sort_keys=True),p[k]),[])
  if matches:
   assert all(all(s[f]==matches[0][f] for f in ['fp','illum','ack','identity_diff','facts']) for s in matches)
   case[k]={**matches[0],'wrong_geometry':int('WRONG:' in matches[0].get('note','')),'annotation_source':'exact_source_case_images_human_prompt_caption'};reused+=1
  else:case[k]=None
 cases.append(case)
(ROOT/'review_working.json').write_text(json.dumps({'reviewer':'Codex assistant, not independent human ground truth','reused':reused,'rule':'Probe ID namespaces source case; reuse requires sourcecase mapping, identical images+humanprompt and entirecaption. New strings manually scored before current key.','cases':cases},ensure_ascii=False,indent=2),encoding='utf8');print({'reused':reused,'new':120-reused})
