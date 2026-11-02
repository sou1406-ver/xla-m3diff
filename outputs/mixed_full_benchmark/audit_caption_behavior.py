"""Descriptive matched-ID caption audit; no visual correctness labels inferred."""
from pathlib import Path
import json,statistics,collections,re
ROOT=Path(__file__).parent;out=ROOT/'results'
candidate=[]
for i in range(5):
 p=out/f'batch_{i:02d}.jsonl'
 if p.exists():candidate.extend(json.loads(l) for l in p.read_text(encoding='utf8').splitlines() if l.strip())
assert len(candidate)==len({r['id'] for r in candidate})
records={r['id']:r for r in candidate};report=[]
manifest=json.loads((out/'all_manifest.json').read_text(encoding='utf8'))
for split in ['Real','Render']:
 ids=[r['id'] for r in manifest if r['split']==split and r['id'] in records]
 original=ROOT/f'baseline_original/OmniDiff_{split}/OmniDiff_{split}.jsonl'
 baseline={r['id']:r for r in map(json.loads,original.read_text(encoding='utf8').splitlines())}
 for arm,source in [('baseline',baseline),('mixed_objective',records)]:
  texts=[source[rid]['caption'] for rid in ids];lengths=sorted(len(re.findall(r'\S+',t)) for t in texts)
  counts=collections.Counter(texts)
  report.append({'split':split,'arm':arm,'n':len(ids),'mean_whitespace_words':statistics.mean(lengths),'median_whitespace_words':statistics.median(lengths),'p95_whitespace_words':lengths[int((len(lengths)-1)*.95)],'captions_at_least_500_whitespace_words':sum(n>=500 for n in lengths),'exact_more_visible_sentence_count':sum(t.strip()=='The scene has become more visible.' for t in texts),'top5_exact_captions':counts.most_common(5)})
result={'n_candidate':len(candidate),'expected':1570,'full_test_complete':len(candidate)==1570,'matched_IDs':True,'interpretation':'Descriptive output behavior only. Shorter or repeated generic captions do not establish image correctness. Whitespace words are not model tokens.','by_split_arm':report}
(out/'caption_behavior_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
