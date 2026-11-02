import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent;prior=ROOT.parent/'invariance_sft'
source=prior/'results/train.json';assert hashlib.sha256(source.read_bytes()).hexdigest()==json.loads((prior/'data_audit.json').read_text())['train_sha256']
train=json.loads(source.read_text());assert len(train)==256
for r in train:r['is_invariance_negative']=r['id'].startswith('negative_')
assert sum(r['is_invariance_negative'] for r in train)==64
(ROOT/'train.json').write_text(json.dumps(train,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
questions=json.loads((prior/'results/eval_questions.json').read_text());meta=json.loads((prior/'results/eval_manifest.json').read_text());selected=[r for r in meta if r['cohort']=='new' or r['condition'] in ['identity','natural']]
ids={r['id'] for r in selected};q=[r for r in questions if r['id'] in ids]
assert len(q)==len(selected)==72
for n,v in [('eval_questions.json',q),('eval_manifest.json',selected)]: (ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audit={'training_records':256,'negative_records':64,'positive_records':192,'same_original_images_prompts_targets':True,'source_train_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'train_with_flags_sha256':hashlib.sha256((ROOT/'train.json').read_bytes()).hexdigest(),'n_eval':72}
(ROOT/'data_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf8');print(json.dumps(audit))
