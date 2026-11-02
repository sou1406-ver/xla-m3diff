from pathlib import Path
import json,re,sys,importlib.util
HERE=Path(__file__).parent
from deduplicate_caption_v2 import deduplicate_caption,sentence_spans
spec=importlib.util.spec_from_file_location('old_dedup',HERE.parent/'curated_sft/deduplicate_caption.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
joined='The black chair is missing.The red cup disappears.The black chair is missing.The black chair is missing.'
assert old.deduplicate_caption(joined)[0]==joined
assert deduplicate_caption(joined)[0]=='The black chair is missing. The red cup disappears.'
preserve=['The left chair disappears. The right chair disappears.','The sign reads "Go.Go." The person\'s hat changes to blue.',"The text changes to 'YES'. The text changes to 'yes'.",'The size changes to1.5 meters. The blue box remains.','The U.S. flag appears. The U.S. flag disappears.','Dr. Li moves left. Dr. Li returns right.','The chair in the third row disappears.The chair in the fourth row disappears.','A. The chair disappears. A. The cup appears.']
for text in preserve:assert deduplicate_caption(text)[0]==text,text
files=[]
for split in ['Real','Render']:files.append(HERE.parent/f'mixed_full_benchmark/baseline_original/OmniDiff_{split}/OmniDiff_{split}.jsonl')
for folder,arms in [('invariance_ablation',['baseline','positive_control','mixed_objective']),('prompt_balanced_sft',['baseline','balanced']),('invariance_confirmation',['baseline','positive_control','mixed_objective']),('prompt_probe',['baseline','old_mixed','balanced'])]:
 for arm in arms:files.append(HERE.parent/folder/'results'/(arm+'.jsonl'))
include_full='--include-full' in sys.argv
if include_full:
 for i in range(5):
  path=HERE.parent/f'mixed_full_benchmark/results/batch_{i:02d}.jsonl'
  if path.exists():files.append(path)
audit=[];examples=[]
for path in files:
 rows=[json.loads(l) for l in path.read_text(encoding='utf8').splitlines() if l.strip()];c1=c2=0;removed=0
 for row in rows:
  text=row['caption'];one=old.deduplicate_caption(text)[0];two,info=deduplicate_caption(text);c1+=one!=text;c2+=two!=text;removed+=info['removed_exact_sentences']
  before=re.findall(r'\w+|[^\w\s]',text);after=re.findall(r'\w+|[^\w\s]',two);cursor=iter(before)
  assert all(any(t==x for t in cursor) for x in after),'New lexical content introduced'
  normalized=lambda s:re.sub(r'\s+',' ',s).strip()
  complete={normalized(s) for s in sentence_spans(text) if s[-1:] in '.!?"\''};remaining={normalized(s) for s in sentence_spans(two)}
  assert complete<=remaining,'Distinct complete claim dropped'
  if two!=one:examples.append({'file':str(path.relative_to(HERE.parent)),'id':row['id'],'v1':one,'v2':two,'v2_info':info})
 audit.append({'file':str(path.relative_to(HERE.parent)),'n':len(rows),'changed_v1':c1,'changed_v2':c2,'exact_sentences_removed_v2':removed})
result={'n_captions_checked':sum(r['n'] for r in audit),'all_lexical_subsequence':True,'all_distinct_complete_claims_retained':True,'joined_loop_fixed':True,'quoted_case_decimal_abbreviation_location_ordinal_checks_pass':True,'by_file':audit,'n_v1_v2_differences':len(examples),'limits':'Text cleanup, not image verification or model rotation understanding. Corpus properties do not prove perfect sentence parsing on arbitrary external text.'}
audit_name='corpus_audit_with_full.json' if include_full else 'corpus_audit.json';diff_name='differences_with_full.json' if include_full else 'differences.json'
(HERE/audit_name).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');(HERE/diff_name).write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
