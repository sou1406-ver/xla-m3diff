from pathlib import Path
import json,hashlib
import modal
P=Path(__file__).parent;v=modal.Volume.from_name('m3diff')
approval=json.loads((P/'DATA_APPROVED.json').read_text());assert hashlib.sha256((P/'data/train.json').read_bytes()).hexdigest()==approval['train_json_sha256']
files=['data/train.json','data/synthetic_manifest.jsonl','DATA_APPROVED.json','DATA_AUDIT.json','VALIDATED_DATA.json','DATA_VISUAL_REVIEW.json','FINAL_LABEL_AUDIT.json','PRETRAIN_CAPTION_FIX.json','DATA_RECIPE.json','ROUND_BUDGET.json','CAPTION_POLICY.json','LOCK.json']
with v.batch_upload(force=True) as b:
    for n in files:b.put_file(P/n,'r64_v2_final_round/'+n)
assert b''.join(v.read_file('r64_v2_final_round/data/train.json'))==(P/'data/train.json').read_bytes()
print('Approved dataset uploaded and byte-verified; no GPU started')
