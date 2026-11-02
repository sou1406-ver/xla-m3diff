"""Create empty masked annotations after verifying frozen questions and rubric."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(ROOT/'results/eval_questions.json')==load(ROOT/'eval_questions.json')
assert load(ROOT/'results/eval_rubric.json')==load(ROOT/'eval_rubric.json')
preds=load(ROOT/'results/masked_predictions.json');assert len(preds)==80
cases=[{'id':p['id'],'index':i,**{f'candidate_{c}':None for c in [1,2,3]}} for i,p in enumerate(preds)]
obj={'reviewer':'Codex assistant; not independent human adjudication','rule':'Image-first facts fixed before all confirmation captions. Three-way masking; exact identical caption within same question may share a score. No current key opened.','rubric_sha256':hashlib.sha256((ROOT/'eval_rubric.json').read_bytes()).hexdigest(),'cases':cases}
(ROOT/'review_working.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
print({'pairs':80,'candidate_annotations':240})
