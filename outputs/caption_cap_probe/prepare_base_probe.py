"""Freeze baseline decoder controls independently of the LoRA cap result."""
from pathlib import Path
import json
HERE=Path(__file__).parent;OUT=HERE.parent;pilot=OUT/'invariance_ablation/results'
meta=json.loads((pilot/'eval_manifest.json').read_text(encoding='utf8'))
ids=[r['id'] for r in meta if r['condition']=='natural' and r['scene']!='clothesline'];assert len(ids)==19
questions={q['id']:q for q in json.loads((pilot/'eval_questions.json').read_text(encoding='utf8'))}
cached={r['id']:r for r in map(json.loads,(pilot/'baseline.jsonl').read_text(encoding='utf8').splitlines())}
full=[]
for split in ['Real','Render']:
 path=OUT/f'mixed_full_benchmark/baseline_original/OmniDiff_{split}/OmniDiff_{split}.jsonl'
 full += [json.loads(l) for l in path.read_text(encoding='utf8').splitlines() if l.strip()]
longest=sorted(full,key=lambda r:(-len(r['caption'].split()),r['id']))[:4];assert all(len(r['caption'].split())>=500 for r in longest)
fullq={q['id']:q for q in json.loads((OUT/'mixed_full_benchmark/results/all_questions.json').read_text(encoding='utf8'))}
selected=[questions[rid] for rid in ids]+[fullq[r['id']] for r in longest]
reference=[cached[rid] for rid in ids]+longest
protocol={'model':'published M3Diff base, no LoRA','revision':'d6a8880dc789b0816660278c087ac9ebdfe18dd0','allowed_caps_frozen':[256,128],'default_unchanged':1024,'selection':'19 previously fact-rated natural pilot pairs excluding uncertain clothesline, plus4 longest whitespace captions in published baseline full1570. Known failure cases, not an unbiased quality sample. Both caps frozen before reading either base-cap output.','reference':'Cached1024 outputs; no paired1024 generation timings available. Do not infer a speed ratio from cross-job timing.','n':23,'ids':[q['id'] for q in selected],'natural_ids':ids,'long_ids':[r['id'] for r in longest],'adoption':'Characterization only. Do not change full scores or default1024. Inspect changed natural captions for fact loss.'}
for name,obj in [('base_questions.json',selected),('cached_base_1024.json',reference),('base_protocol.json',protocol)]:
 p=HERE/name
 if p.exists():assert json.loads(p.read_text(encoding='utf8'))==obj,'Frozen base probe changed'
 else:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
print({'n':len(selected),'caps_frozen':[256,128],'long_cases':[(r['id'],len(r['caption'].split())) for r in longest]})
