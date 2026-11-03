"""Upload a new continuation directory;never overwrite or score the old550."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,ROUND_CEILING
import hashlib,json,modal
P=Path(__file__).parent;R=P/'resume1020_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((R/'RESUME_PROTOCOL.json').read_text());budget=json.loads((P/'latest_budget.json').read_text());D=Decimal
assert (datetime.now(timezone.utc)-datetime.fromisoformat(budget['time_utc'])).total_seconds()<600
assert D(budget['billing']['billed_cost'])==0 and D(budget['billing']['adjustments'].get('Plan Cost','0'))==0
rates=json.loads((P/'rates.json').read_text())['rates'];ceil=lambda v:v.quantize(D('.01'),rounding=ROUND_CEILING)
rate=lambda cpu,mem,gpu=D(0):ceil((gpu+D(str(cpu))*D(rates['cpu_hour_cost'])+D(str(mem))*D(rates['mem_gib_hour_cost']))*D('1.10'))
gpu_rate=rate(4,32,max(D(rates['gpu_hour_cost_a100_40gb']),D(rates['gpu_hour_cost_a100_80gb'])));cpu_rate=rate(4,8);controller_rate=rate(.25,.5)
parts={'GPU':ceil(D(11220+4*180)*gpu_rate/3600),'CPU_score':ceil(D(900+180)*cpu_rate/3600),'controller':ceil(D(12600+180)*controller_rate/3600),'misc':D('.03')};total=sum(parts.values())
assert total<=D('11') and total<=D(budget['remaining_guarded'])
for n,h in protocol['files'].items():assert sha(P/n)==h
for n,h in protocol['input_hashes'].items():assert sha(R/n)==h
v=modal.Volume.from_name('m3diff');remote='mbr_pilot_20261103/resume1020_v1'
try:exists=v.listdir(remote,recursive=True)
except modal.exception.NotFoundError:exists=[]
assert not exists,'Refuse to overwrite existing continuation.'
raw=b''.join(v.read_file('mbr_pilot_20261103/full1570/results1570.jsonl'));assert hashlib.sha256(raw).hexdigest()==protocol['old_raw_sha256']
names={Path(x.path).name for x in v.listdir('mbr_pilot_20261103/full1570')};assert not names.intersection({'METRICS.json','PER_PAIR.json','SELECTION.json'})
admission={'authorized':True,'user_authorization':'Continue remaining1020,11USD cap,predefined resume;user supersedes no-resume rule.','utc':datetime.now(timezone.utc).isoformat(),'cap_usd':11,'generator_sha256':sha(P/'evaluate_resume.py'),'questions_sha256':sha(R/'questions1020.json'),'sampling_protocol_sha256':sha(P/'PROTOCOL.json'),'resume_protocol_sha256':sha(R/'RESUME_PROTOCOL.json'),'budget_snapshot':budget,'rates_upper_hour':{'GPU':str(gpu_rate),'CPU_score':str(cpu_rate),'controller':str(controller_rate)},'reservations_usd':{k:str(v) for k,v in parts.items()},'total_reserved_usd':str(total),'files':protocol['files'],'old_raw_verified_remote_before_any_scores':True}
(R/'ADMISSION.json').write_text(json.dumps(admission,indent=2))
with v.batch_upload(force=False) as batch:
 for n in ['questions1020.json','selection1020.json','RESUME_PROTOCOL.json','ADMISSION.json']:batch.put_file(R/n,remote+'/'+n)
 for n in ['PROTOCOL.json','CPU_READY.json']:batch.put_file(P/n,remote+'/'+n)
ledger=json.loads((P/'budget_ledger.json').read_text());assert not any(j['label']=='MBR_resume1020_v1' for j in ledger['jobs'])
ledger['authorization']='User explicitly authorized remaining1020 continuation,11USD cap with predefined interruption resume. No training/config tuning.';ledger['jobs'].append({'label':'MBR_resume1020_v1','reservation':str(total),'cap':'11','global_GPU_deadline_seconds':11220,'profile':'A10080_4CPU32GiB_plus_bounded_CPU','status':'ADMITTED_NOT_LAUNCHED'});(P/'budget_ledger.json').write_text(json.dumps(ledger,indent=2))
print(json.dumps({'admitted':True,'total_reserved_usd':str(total),'cap_usd':11,'old550_remote_hash_verified':True,'old550not_scored':True,'launched':False}))
