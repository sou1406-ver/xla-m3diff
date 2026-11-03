"""Credit-only admission/upload for the explicitly approved18USD full run.

This script does not launch GPU. It refuses a used output directory and leaves
the frozen pilot and proposal files intact.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import ast, hashlib, json
import modal

P = Path(__file__).parent
F = P / 'full1570'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
budget = json.loads((P / 'latest_budget.json').read_text())
assert (datetime.now(timezone.utc)-datetime.fromisoformat(budget['time_utc'])).total_seconds()<600
assert Decimal(budget['billing'].get('billed_cost','0')) == 0
assert Decimal(budget['billing'].get('adjustments',{}).get('Plan Cost','0')) == 0
rates = json.loads((P / 'rates.json').read_text())['rates']
D = Decimal
ceil = lambda v: v.quantize(D('.01'),rounding=ROUND_CEILING)
rate = lambda cpu,mem,gpu='0': ceil((D(gpu)+D(str(cpu))*D(rates['cpu_hour_cost'])+D(str(mem))*D(rates['mem_gib_hour_cost']))*D('1.10'))
gpu_rate = rate(4,32,max(D(rates['gpu_hour_cost_a100_40gb']),D(rates['gpu_hour_cost_a100_80gb'])))
score_rate = rate(4,8)
coordinator_rate = rate(.25,.5)
gpu = ceil(D(19200+180)*gpu_rate/3600)
score = ceil(D(900+180)*score_rate/3600)
coordinator = ceil(D(21060+180)*coordinator_rate/3600)
misc = D('.04')
reserved = gpu+score+coordinator+misc
assert reserved<=D('18') and reserved<=D(budget['remaining_guarded'])
assert not (F/'ADMISSION.json').exists()

functions=lambda path:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
val,full=functions(P/'evaluate200.py'),functions(P/'evaluate1570.py')
for name in ['generate','clean','measured']:assert val[name]==full[name]
q=json.loads((F/'questions1570.json').read_text())
assert len(q)==len({x['id'] for x in q})==1570
assert all(len(x['conversations'])==1 and x['conversations'][0]['from']=='human' for x in q)
assert all(set(x)=={'id','subset'} for x in json.loads((F/'selection1570.json').read_text()))
assert json.loads((P/'val200/METRICS.json').read_text())['all_gates_passed']
for domain in ['REAL','RENDER']:
    s=json.loads((P/'val200'/f'ASSISTANT_REVIEW_{domain}_SEAL.json').read_text())
    assert sha(P/'val200'/f'ASSISTANT_REVIEW_{domain}_MASKED.json')==s.get('sha256',s.get('masked_assessment_sha256'))

proposal=json.loads((F/'PROPOSED_PROTOCOL.json').read_text())
for name,h in proposal['source_file_hashes'].items():assert sha(F/name)==h
assert sha(P/'PROTOCOL.json')==proposal['sampling_protocol_sha256']
assert sha(F/'questions1570.json')==proposal['questions_sha256']
protocol=dict(proposal,status='ADMITTED_BEFORE_PREDICTIONS',budget_cap_usd=18,
              user_authorization='Explicit user answer: Chay full, tran18do. No training or feature loss.',
              runner_sha256=sha(P/'full1570_modal.py'),
              durable_pipeline='CPU coordinator calls GPU inference then CPU scoring;no retry;GPU not retained for scoring.',
              coordinator_hard_timeout_seconds=21060,scoring_hard_timeout_seconds=900)
for field,name in [('generator_sha256','evaluate1570.py'),('notebook_sha256','full1570.ipynb'),('scorer_sha256','score1570_cpu.py')]:assert sha(P/name)==proposal[field]
files={n:sha(P/n) for n in ['evaluate1570.py','full1570_modal.py','full1570.ipynb','score1570_cpu.py','utility.py']}
admission={'authorized':True,'approved_utc':datetime.now(timezone.utc).isoformat(),'cap_usd':18,
           'user_answer':'Chạy full, trần 18 đô','generator_sha256':sha(P/'evaluate1570.py'),
           'questions_sha256':sha(F/'questions1570.json'),'files':files,
           'sampling_protocol_sha256':sha(P/'PROTOCOL.json'),'budget_snapshot':budget,
           'rate_upper_hour':{'GPU':str(gpu_rate),'score':str(score_rate),'coordinator':str(coordinator_rate)},
           'reservation_usd':{'GPU_including180startup':str(gpu),'CPU_score_including180startup':str(score),'coordinator_including180startup':str(coordinator),'misc':str(misc),'total':str(reserved)},
           'no_automatic_retry':True,'full_protocol_sha256':None}
(F/'FULL_PROTOCOL.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
admission['full_protocol_sha256']=sha(F/'FULL_PROTOCOL.json')
v=modal.Volume.from_name('m3diff')
remote='mbr_pilot_20261103/full1570'
try:existing=v.listdir(remote,recursive=True)
except modal.exception.NotFoundError:existing=[]
assert not existing,'Refuse to overwrite an existing full-run directory.'
assert json.loads(b''.join(v.read_file('mbr_pilot_20261103/CPU_READY.json')))['train_idf_sha256']==json.loads((P/'CPU_READY.json').read_text())['train_idf_sha256']
(F/'ADMISSION.json').write_text(json.dumps(admission,indent=2,ensure_ascii=False),encoding='utf-8')
with v.batch_upload(force=False) as batch:
    for name in ['questions1570.json','selection1570.json','OmniDiff_Real.json','OmniDiff_Render.json','FULL_PROTOCOL.json','ADMISSION.json']:
        batch.put_file(F/name,remote+'/'+name)
    for name in ['PROTOCOL.json','CPU_READY.json']:
        batch.put_file(P/name,remote+'/'+name)
ledger=json.loads((P/'budget_ledger.json').read_text())
assert not any(j['label']=='MBR_full1570_all_stages' for j in ledger['jobs'])
ledger['authorization']='User explicitly approved full1570 MBR,18USD cap;one fixed config,no retries/training.'
ledger['jobs'].append({'label':'MBR_full1570_all_stages','reservation':str(reserved),'cap':'18','profile':'A10080_4CPU32GiB_plus_CPU_pipeline','seconds':19200,'settlement_kind':'Reserved upper bound,not actual invoice'})
(P/'budget_ledger.json').write_text(json.dumps(ledger,indent=2))
print(json.dumps({'admitted':True,'reserved_upper_usd':str(reserved),'cap_usd':18,'remaining_guarded_before':budget['remaining_guarded'],'uploaded':True,'launched':False},indent=2))
