"""Only adapt the audited generator's dataset, output directory and stage bounds."""
from pathlib import Path
import json,ast,hashlib
P=Path(__file__).parent;metrics=json.loads((P/'METRICS20.json').read_text());assert metrics['chosen_generation_method_by_runtime_only']=='batch8'
assert not metrics['operational_low_promise_stop'];source=(P/'benchmark.py').read_text()
changes={
 "P=Path('/mnt/m3diff/mbr_pilot_20261103')":"P=Path('/mnt/m3diff/mbr_pilot_20261103/val200')",
 "batch_size=8":"batch_size=2",
 "questions20.json":"questions200.json",
 "selection20.json":"selection200.json",
 "results20.jsonl":"results200.jsonl",
 "BENCHMARK_":"VAL_",
 "MBR20_PROGRESS":"MBR200_PROGRESS",
 "'budget_cap_usd':1":"'budget_cap_usd':3.60",
 "order=['sequential8','batch8'] if index%2==0 else ['batch8','sequential8']":"order=['batch8']",
 "'planned':20":"'planned':200",
 "len(records)==20":"len(records)==200",
}
for old,new in changes.items():assert old in source,old;source=source.replace(old,new)
ast.parse(source);(P/'evaluate200.py').write_text(source,encoding='utf-8')
nb=json.loads((P/'benchmark.ipynb').read_text());s=''.join(nb['cells'][-1]['source']);assert '/root/benchmark.py' in s;nb['cells'][-1]['source']=s.replace('/root/benchmark.py','/root/evaluate200.py').splitlines(True);(P/'val200.ipynb').write_text(json.dumps(nb,indent=1))
protocol={'stage':'single_fixed_config_val200','questions_sha256':hashlib.sha256((P.parent/'r64_val_precheck_20261102/questions.json').read_bytes()).hexdigest(),'n_real':100,'n_render':100,'generation_method':'batch8 via4chunks of2,chosen by20pair runtime only','sampling_protocol_sha256':hashlib.sha256((P/'PROTOCOL.json').read_bytes()).hexdigest(),'inference':'Fresh greedy and8samples on sameGPU/session/cacheembeddings perpair. No reuse of prior captions.','max_candidates':9,'selector_unchanged':True,'gate_delta_CIDEr_x100_each_domain':1.0,'oracle_diagnostic_only':True,'budget_cap_usd':3.60,'hard_timeout_seconds':7200,'soft_timeout_seconds':6900,'gpu_rate_upper_hour':'1.70','gpu_reservation_with180startup':'3.49','cpu_scoring_reservation':'.05','other_allowance':'.03','total_reserved':'3.57','full_test_budget_admitted':False,'qualitative_review_if_pass':'Up to40 changed pairs,20/domain seeded20261106; selection based only on changed status and IDs, never favourable score. Review facts against images before claiming factual improvement. Assistant review must not be labelled independent human annotation.','no_hyperparameter_tuning':True,'no_training':True}
(P/'VAL_PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
print('Created val200 generator from unchanged benchmark source; fixed sampling; cap3.60USD.')
