"""Reuse only exact image/question+caption annotations; leave every new string unscored."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent;prior=ROOT.parent/'invariance_sft'
expected=json.loads((prior/'data_audit.json').read_text())['eval_questions_sha256']
assert hashlib.sha256((ROOT/'comparison_results/eval_questions.json').read_bytes()).hexdigest()==expected
old=json.loads((prior/'masked_assessments.json').read_text())['cases'];lookup={}
for r in old:
    for c in [1,2]:
        s=r[f'candidate_{c}'];lookup.setdefault((r['id'],s['caption']),[]).append((r['index'],c,s))
preds=json.loads((ROOT/'comparison_results/masked_predictions.json').read_text());cases=[];reused=0
for i,r in enumerate(preds):
    item={'id':r['id'],'index':i}
    for c in [1,2]:
        caption=r[f'candidate_{c}'];matches=lookup.get((r['id'],caption),[])
        if matches:
            # Exact same sentence can never receive a different fact label by model name.
            fields=['fp','ack','illum','identity_diff','facts','suppression']
            assert all(all(m[2][f]==matches[0][2][f] for f in fields) for m in matches)
            item[f'candidate_{c}']={**matches[0][2],'annotation_source':'exact_prior_caption','prior_sources':[[x[0],x[1]] for x in matches]};reused+=1
        else:item[f'candidate_{c}']=None
    cases.append(item)
obj={'reviewer':'Codex assistant; not independently human adjudicated','rule':'Exact case/question manifest and entire displayed caption only. New strings must be manually assessed. No current precision-mode key opened.','reused_candidate_annotations':reused,'cases':cases}
(ROOT/'review_working.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'total_candidates':216,'exact_annotations_reused':reused,'manual_remaining':216-reused}))
