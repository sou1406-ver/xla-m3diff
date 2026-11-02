"""Check completeness and adapter/runtime consistency before reporting full scores."""
from pathlib import Path
import json,hashlib,collections
ROOT=Path(__file__).parent;out=ROOT/'results';expected='6b8d81729b03f83e9c03de9a78fb1aa895a47088c32c4435115ac39b77a1fb5f'
questions=json.loads((out/'all_questions.json').read_text(encoding='utf8'));wanted={q['id'] for q in questions};assert len(questions)==len(wanted)==1570
rows=[];batches=[];environment_hashes=[]
for i in range(5):
 name=f'batch_{i:02d}';status=json.loads((out/(name+'_status.json')).read_text(encoding='utf8'))
 assert status['complete'] and status['exit_code']==0 and status['adapter_sha256']==expected
 assert status['n_expected']==(290 if i==4 else 320)==status['n_completed']
 load=json.loads((out/(name+'_load_audit.json')).read_text(encoding='utf8'))
 assert load['all_saved_keys_loaded'] and load['saved_values_restored_exactly_after_fp32_cast']
 batch=[json.loads(l) for l in (out/(name+'.jsonl')).read_text(encoding='utf8').splitlines() if l.strip()]
 assert len(batch)==status['n_completed'];assert {r['id'] for r in batch}=={q['id'] for q in questions[i*320:(i+1)*320]}
 assert all(r['image_id']==r['id'] and isinstance(r['caption'],str) and r['caption'].strip() for r in batch)
 rows+=batch;batches.append(status)
 environment_hashes.append(hashlib.sha256((out/(name+'_environment.txt')).read_bytes()).hexdigest())
assert len(rows)==len({r['id'] for r in rows})==1570 and {r['id'] for r in rows}==wanted
assert len(set(environment_hashes))==1,'Inference environments changed between chunks'
prior=[json.loads(p.read_text(encoding='utf8')) for p in out.glob('batch_*_prior_attempt_*.json')]
audit={'full_test_complete':True,'n':1570,'unique_IDs':True,'official_order_and_chunk_IDs_match':True,'nonempty_captions':True,'all_adapter_hashes_match':True,'adapter_sha256':expected,'all_chunks_exact_FP32_adapter_restore':True,'all5_environment_freezes_identical':True,'environment_freeze_sha256':environment_hashes[0],'batches':batches,'prior_partial_attempts':prior,'total_recorded_GPU_function_elapsed_seconds_including_prior_attempts':sum(s['elapsed_seconds'] for s in batches+prior)}
(out/'FULL_RUN_VALIDATED.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in audit.items() if k!='batches'},indent=2))
