from pathlib import Path
from decimal import Decimal,ROUND_CEILING
import csv,json,hashlib,collections,datetime
from camera_detector import camera_motion_claim
P=Path(__file__).parent;E=P/'evaluation'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def csvrows(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def yes(x):return str(x).lower()=='true'
for n,h in read(P/'LOCK.json')['files'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
gate=read(E/'GATE_RESULT.json');done=read(E/'EVALUATION_DONE.json');assert done['complete'] and not gate['all_gates_passed']
cam=rows(E/'camera_v2.jsonl');synth=rows(E/'synth_v2.jsonl');assert len(cam)==len({x['id'] for x in cam})==240;assert len(synth)==len({x['id'] for x in synth})==600
assert [x['id'] for x in cam]==[x['id'] for x in read(P.parent/'r64_camera_eval_20261102/questions.json')]
assert [x['id'] for x in synth]==[x['id'] for x in read(P.parent/'r64_synth_eval_20261102/questions.json')]
assert all(x['caption'].strip() for x in cam+synth)
flags=[x for x in synth if camera_motion_claim(x['caption'])];assert len(flags)==124==gate['stages']['synth']['camera_motion_flags']
assert [x['id'] for x in flags]==[x['id'] for x in read(E/'synth_camera_flags.json')]
sc=csvrows(E/'synth_scores/per_pair.csv');byid={x['pair_id']:x for x in sc}
counts={k:sum(yes(x['type_ok']) for x in sc if x['cond']==k) for k in gate['stages']['synth']['type_counts']};assert counts==gate['stages']['synth']['type_counts']
models={}
for arm,file in [('base',P.parent/'r64_synth_eval_20261102/base.jsonl'),('r64',P.parent/'r64_synth_eval_20261102/r64.jsonl'),('v2',E/'synth_v2.jsonl')]:
 rr=rows(file);ff=[x for x in rr if camera_motion_claim(x['caption'])]
 models[arm]={'frozen_camera_motion_flags':len(ff),'by_condition':dict(collections.Counter(byid[x['id']]['cond'] for x in ff))}
assert models['base']['frozen_camera_motion_flags']==0 and models['r64']['frozen_camera_motion_flags']==33
controls={k:{'n':sum(x['cond']==k for x in sc),'false_alarm':sum(yes(x['false_alarm']) for x in sc if x['cond']==k),'nochange_words':sum(yes(x['m_nochange']) for x in sc if x['cond']==k)} for k in ['same','jpeg']}
assert not (E/'base.jsonl').exists() and not (E/'v2.jsonl').exists(),'Val must not have run after failed synthetic gates'
for n in ['camera_v2.jsonl.generation_audit.json','synth_v2.jsonl.generation_audit.json']:
 a=read(E/n);assert a['overrides']=={'do_sample':False,'temperature':0,'max_new_tokens':1024,'repetition_penalty':1.05,'num_beams':1};assert a['mdp_projector_dtype_counts']=={'torch.bfloat16':86}
D=Decimal
def cost(seconds,rate):return ((D(str(seconds))+180)*D(rate)/3600).quantize(D('.01'),rounding=ROUND_CEILING)
train_upper=cost(read(P/'TRAIN_JOB_TIMING.json')['wall_seconds'],'3.24');eval_upper=cost(read(E/'JOB_TIMING.json')['wall_seconds'],'1.70');upper=train_upper+eval_upper+D('.15')+D('.15')+D('.04');assert upper<=7
bill=read(P/'latest_budget.json');start=read(P/'budget_ledger.json')['initial_consumption'];delta=D(bill['api_consumption'])-D(start)
budget={'cap_usd':7,'train_upper_including180s':'%s'%train_upper,'evaluation_upper_including180s':'%s'%eval_upper,'cpu_preparation_upper':'0.15','failed_pretraining_startup_upper':'0.15','other_overhead_allowance':'0.04','whole_round_conservative_upper':str(upper),'api_observed_consumption_delta':str(delta),'api_observation_time_utc':bill['time_utc'],'interpretation':'Upper bounds are not actual billed costs. API delta is a lagging workspace snapshot, not a final per-job invoice. No paid plan or credit purchase.'}
(P/'FINAL_BUDGET.json').write_text(json.dumps(budget,indent=2))
summary={'decision':'REJECT_V2_AND_STOP; keep original base as default; no v3','train_complete_steps':450,'camera':gate['stages']['camera'],'synth_type_counts':counts,'synth_motion_detector_same_frozen_rule':models,'controls':controls,'failed_gates':done['failed_gates'],'val200_run':False,'full1570_run':False,'gates_and_scorers_unchanged':True,'raw_captions':840,'gate_is_regex_proxy':True,'cost_upper_usd':str(upper)}
(P/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(json.dumps(budget,indent=2))
