"""Executed in the GPU notebook kernel; stop immediately on failed locked gate."""
import os,json,time,subprocess,hashlib,csv,shutil
from pathlib import Path
RUN=Path('/mnt/m3diff/r64_v2_final_round/evaluation');RUN.mkdir(exist_ok=True)
OUT='/mnt/m3diff/r64_v2_final_round/m3diff-v2-final-lora'
assert json.load(open('/mnt/m3diff/r64_v2_final_round/TRAIN_DONE.json'))['complete']
FROZEN=Path('/root/scorer');FROZEN.mkdir(exist_ok=True)
for src,dst in [('score_captions_frozen.py','score_captions.py'),('score_camera_frozen.py','score_camera.py'),('ft_common_frozen.py','ft_common.py'),('camera_detector.py','camera_detector.py')]:shutil.copy2('/root/'+src,FROZEN/dst)
shutil.copy2('/mnt/m3diff/synth/code/synth_common.py',FROZEN/'synth_common.py')
import sys
sys.path.insert(0,str(FROZEN))
from camera_detector import camera_motion_claim
truth=lambda s:str(s).lower()=='true'
timings=[];gates={};stage_data={}
def infer(qfile,answers,imagefolder,lora):
    assert not Path(answers).exists(),'No mixed previous inference caches'
    started=time.time();run_eval(str(qfile),str(answers),str(imagefolder),lora)
    q=json.load(open(qfile));r=[json.loads(l) for l in open(answers) if l.strip()]
    assert [x['id'] for x in q]==[x['id'] for x in r] and all(x['caption'].strip() for x in r)
    timings.append({'file':str(answers),'n':len(r),'wall_seconds':time.time()-started});(RUN/'TIMINGS.json').write_text(json.dumps(timings,indent=2));return r
def save():
    (RUN/'GATE_RESULT.json').write_text(json.dumps({'gates':gates,'stages':stage_data,'all_gates_passed':len(gates)==5 and all(gates.values()),'full1570_run':False,'decision':'STOP: failed locked gate' if not all(gates.values()) else 'No automatic full test; remaining7USD budget admission required.'},indent=2))
infer('/mnt/m3diff/ft/camtest/questions.json',RUN/'camera_v2.jsonl','/mnt/m3diff/ft/camtest',True)
shutil.copy2('/mnt/m3diff/ft/eval/camtest_base.jsonl',RUN/'camera_base.jsonl')
subprocess.run([PY,str(FROZEN/'score_camera.py'),'--root','/mnt/m3diff/ft/camtest','--base',str(RUN/'camera_base.jsonl'),'--ft',str(RUN/'camera_v2.jsonl'),'--synth-code',str(FROZEN),'--out',str(RUN/'camera_scores.csv')],check=True)
rows=list(csv.DictReader(open(RUN/'camera_scores.csv')));assert len(rows)==480
pure=[r for r in rows if r['model']=='ft' and r['cond'] not in ['cam_add','cam_remove']];obj=[r for r in rows if r['model']=='ft' and r['cond'] in ['cam_add','cam_remove']]
assert len(pure)==180 and len(obj)==60
fp=sum(truth(r['false_obj']) for r in pure);joint=sum(truth(r['obj_type_ok']) and truth(r['obj_name_ok']) for r in obj)
stage_data['camera']={'object_flags':fp,'joint_type_name':joint};gates['camera_object_flags_le_54']=fp<=54;gates['camera_joint_ge_35']=joint>=35;save()
if all(gates.values()):
    caps=infer('/mnt/m3diff/synth/data/questions.json',RUN/'synth_v2.jsonl','/mnt/m3diff/synth/data',True)
    subprocess.run([PY,str(FROZEN/'score_captions.py'),'--root','/mnt/m3diff/synth/data','--answers',str(RUN/'synth_v2.jsonl'),'--out',str(RUN/'synth_scores'),'--n-manual','0'],check=True)
    rows=list(csv.DictReader(open(RUN/'synth_scores/per_pair.csv')));assert len(rows)==600
    flags=[r for r in caps if camera_motion_claim(r['caption'])]
    floors={'add':84,'remove':81,'color':67,'move':39,'size':21,'light':58}
    counts={k:sum(truth(r['type_ok']) for r in rows if r['cond']==k) for k in floors}
    stage_data['synth']={'camera_motion_flags':len(flags),'type_counts':counts,'type_floors':floors};gates['synth_camera_le_30']=len(flags)<=30;gates['all_six_types_preserved_with_tolerance']=all(counts[k]>=floors[k] for k in floors)
    (RUN/'synth_camera_flags.json').write_text(json.dumps(flags,indent=2));save()
if all(gates.values()) and len(gates)==4:
    VAL=Path('/mnt/m3diff/r64_val_precheck_20261102')
    for name in ['questions.json','real_reference.json','render_reference.json']:shutil.copy2(VAL/name,RUN/name)
    infer(VAL/'questions.json',RUN/'base.jsonl',VAL/'images',False)
    infer(VAL/'questions.json',RUN/'v2.jsonl',VAL/'images',True)
    subprocess.run([PY,'/root/score_val.py'],check=True)
    metrics=json.load(open(RUN/'metrics.json'));stage_data['val']=metrics;gates['both_val_domains_delta_ge_minus_1']=all(metrics[d]['delta_v2_minus_base']>=-1 for d in ['real','render']);save()
(RUN/'EVALUATION_DONE.json').write_text(json.dumps({'complete':True,'stages_run':list(stage_data),'failed_gates':[k for k,v in gates.items() if not v],'full1570_run':False},indent=2))
print('V2_GATE_RESULT',json.dumps(stage_data),gates,flush=True)
