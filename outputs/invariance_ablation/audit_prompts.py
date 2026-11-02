import json,collections
from pathlib import Path
HERE=Path(__file__).parent
rows=json.loads((HERE/'train.json').read_text())
counts={k:dict(collections.Counter(r['conversations'][0]['value'] for r in rows if r['is_invariance_negative']==v)) for k,v in [('positive',False),('negative',True)]}
(HERE/'prompt_distribution_audit.json').write_text(json.dumps(counts,indent=2))
print(json.dumps(counts,indent=2))
root=HERE.parent/'mixed_full_benchmark';old={};baseline={}
for split in ['Real','Render']:
 old.update({q['id']:q for q in json.loads((root/f'questions_{split}.json').read_text())})
 baseline.update({r['id']:r for r in map(json.loads,(root/f'baseline_original/OmniDiff_{split}/OmniDiff_{split}.jsonl').read_text().splitlines())})
confirm=HERE.parent/'invariance_confirmation';sel=json.loads((confirm/'selection_locked.json').read_text())['selected'];pred={r['id']:r for r in map(json.loads,(confirm/'baseline_probe.jsonl').read_text().splitlines())}
new_questions={q['id']:q for q in json.loads((confirm/'eval_questions.json').read_text())}
same=[r for r in sel if old[r['original_id']]['conversations']==new_questions[r['scene']+'__natural']['conversations']]
result=json.loads((confirm/'baseline_reproducibility.json').read_text());result.update(same_question_prompt_pairs=len(same),same_prompt_exact_matches=sum(pred[r['scene']+'__natural']['caption']==baseline[r['original_id']]['caption'] for r in same),n_changed_prompts=16-len(same),interpretation='Legacy official benchmark has multiple prompts; confirmation fixes one.5/16 raw matches is not a matched-prompt reproducibility failure. Full benchmark must preserve every official question.')
(confirm/'baseline_reproducibility.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
