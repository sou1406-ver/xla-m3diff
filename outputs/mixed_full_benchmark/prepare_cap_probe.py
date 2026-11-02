"""Freeze a small exploratory runtime probe before full metric scoring."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).parent;OUT=HERE.parent;dest=OUT/'caption_cap_probe';dest.mkdir(exist_ok=True)
pilot=OUT/'invariance_ablation/results'
meta=json.loads((pilot/'eval_manifest.json').read_text(encoding='utf8'))
ids=[r['id'] for r in meta if r['condition']=='natural' and r['scene']!='clothesline'];assert len(ids)==19
questions={q['id']:q for q in json.loads((pilot/'eval_questions.json').read_text(encoding='utf8'))}
cached={r['id']:r for r in map(json.loads,(pilot/'mixed_objective.jsonl').read_text(encoding='utf8').splitlines())}
rows=[]
for i in [0,3,1]:rows += [json.loads(l) for l in (HERE/f'results/batch_{i:02d}.jsonl').read_text(encoding='utf8').splitlines() if l.strip()]
longest=sorted(rows,key=lambda r:(-len(r['caption'].split()),r['id']))[:4]
assert all(len(r['caption'].split())>=500 for r in longest)
fullq={q['id']:q for q in json.loads((HERE/'results/all_questions.json').read_text(encoding='utf8'))}
selected=[questions[rid] for rid in ids]+[fullq[r['id']] for r in longest]
reference=[cached[rid] for rid in ids]+longest
protocol={'selection':'19 previously fact-rated pilot natural pairs (uncertain clothesline excluded), then4 longest whitespace captions from completed official chunks0,3,1. Selection uses known outputs, before full metrics; exploratory, not unbiased generalization or a new full score.',
'max_new_tokens':256,'reference_max_new_tokens':1024,'reference':'Cached outputs of exactly the selected old mixed FP32 unmerged adapter; per-case paired speed comparison is not available from cache.',
'changed_options':'Only max_new_tokens1024->256; add synchronized generation timing/output token count fields. Same model, dtype, prompt, question, images.',
'adoption':'Do not change default1024 or official benchmark based on this probe. Report truncation and lost facts; exact-match natural captions inherit earlier ratings, changed captions require inspection.',
'hard_timeout_seconds':360,'soft_subprocess_timeout_seconds':260,'n':len(selected),'ids':[q['id'] for q in selected],
'adapter_sha256':'6b8d81729b03f83e9c03de9a78fb1aa895a47088c32c4435115ac39b77a1fb5f'}
for n,v in [('questions.json',selected),('cached_1024.json',reference),('protocol.json',protocol)]:
 p=dest/n
 if p.exists():assert json.loads(p.read_text(encoding='utf8'))==v,'Frozen selection changed'
 else:p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
code=dest/'code';code.mkdir(exist_ok=True)
for name in ['run_caption.py','input_guard.py']:shutil.copy2(OUT/'m3diff_portable/code'/name,code/name)
source=(OUT/'m3diff_portable/code/baseline_eval.py').read_text(encoding='utf8')
source='import time\n'+source
source=source.replace('        with torch.inference_mode():','        torch.cuda.synchronize()\n        gen_started = time.monotonic()\n        with torch.inference_mode():')
source=source.replace('        outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]','        torch.cuda.synchronize()\n        gen_seconds = time.monotonic() - gen_started\n        outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]')
source=source.replace('"caption": outputs,','"caption": outputs,\n                    "generated_token_slots": int(output_ids.shape[-1]),\n                    "last_token_id": int(output_ids[0, -1]),\n                    "tokenizer_eos_token_id": tokenizer.eos_token_id,\n                    "generation_seconds": gen_seconds,\n                    "max_new_tokens": args.max_new_tokens,')
compile(source,'timed_baseline_eval.py','exec');(code/'baseline_eval.py').write_text(source,encoding='utf8')
(dest/'source_audit.json').write_text(json.dumps({'instrumentation':'CUDA synchronization and monotonic timestamps around generate; additional JSON fields. Generation arguments except cap unchanged.','source_sha256':hashlib.sha256(source.encode()).hexdigest()},indent=2),encoding='utf8')
print({'n':len(selected),'long_cases':[(r['id'],len(r['caption'].split())) for r in longest],'selection_locked':True})
