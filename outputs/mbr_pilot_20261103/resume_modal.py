"""Bounded continuation of the locked full benchmark; no model/config tuning."""
from pathlib import Path
import modal
H=Path(__file__).parent;V=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr-resume1020')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv')
for n in ['evaluate_resume.py','resume_store.py']:image=image.add_local_file(str(H/n),'/root/'+n,copy=True)
score_image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap')
for n in ['score_resume.py','resume_store.py','utility.py']:score_image=score_image.add_local_file(str(H/n),'/root/'+n,copy=True)
ROOT='/mnt/m3diff/mbr_pilot_20261103';DEST=ROOT+'/resume1020_v1'

@app.function(image=image,gpu='A100-80GB',cpu=(4,4),memory=(32768,32768),timeout=11400,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def generate(deadline):
 import os,json,time,uuid,threading,subprocess,signal,shutil,sys
 from datetime import datetime,timezone
 sys.path.insert(0,'/root');from resume_store import prefix
 V.reload();p=Path(DEST);q=json.loads((p/'questions1020.json').read_text());ad=json.loads((p/'ADMISSION.json').read_text());assert ad['authorized'] and ad['cap_usd']==11
 state=json.loads((p/'STATE.json').read_text());assert deadline==state['gpu_deadline_unix']
 saved=prefix(q,p/'pairs')
 if len(saved)==1020:return {'status':'ALREADY_COMPLETE','pairs':1020}
 if time.time()>=deadline-120:return {'status':'GLOBAL_BUDGET_STOP','pairs':len(saved)}
 sessions=p/'sessions';sessions.mkdir(exist_ok=True)
 if len(list(sessions.glob('*_start.json')))>=3:return {'status':'MAX_3_GPU_SESSIONS','pairs':len(saved)}
 sid=uuid.uuid4().hex;(sessions/f'{sid}_start.json').write_text(json.dumps({'session_id':sid,'utc':datetime.now(timezone.utc).isoformat(),'resume_after_new_pairs':len(saved),'next_id':q[len(saved)]['id'],'deadline_unix':deadline}));V.commit()
 expired=threading.Event();processes=[]
 def stop():
  expired.set()
  for proc in list(processes):
   if proc.poll() is None:
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:pass
  time.sleep(2)
  for proc in list(processes):
   if proc.poll() is None:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
 timer=threading.Timer(max(0,deadline-time.time()),stop);timer.daemon=True;timer.start()
 log=(sessions/f'{sid}.log').open('a');started=time.time();result={'session_id':sid}
 def run(cmd,env=None,cwd=None):
  assert not expired.is_set(),'Global budget deadline'
  proc=subprocess.Popen(cmd,env=env,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);processes.append(proc)
  if expired.is_set():stop()
  last=-1
  while proc.poll() is None:
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:pass
   V.commit()
   if (p/'PROGRESS.json').exists():
    try:
     progress=json.loads((p/'PROGRESS.json').read_text())
     if progress['completed_pairs']!=last:print('RESUME_PROGRESS',json.dumps(progress),flush=True);last=progress['completed_pairs']
    except (json.JSONDecodeError,FileNotFoundError):pass
  if proc.returncode:raise RuntimeError(f'Process exited{proc.returncode};deadline_expired={expired.is_set()}')
 try:
  repo='/root/M3Diff';venv='/root/m3diff-venv';py=venv+'/bin/python'
  if not Path(repo).exists():shutil.copytree(ROOT+'/../baseline_reproduction_v1/repo',repo,ignore=shutil.ignore_patterns('.git','__pycache__'))
  env=dict(os.environ,HF_HOME='/mnt/m3diff/baseline_cache/huggingface',HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',PYTHONPATH=repo+':/root',PYTHONWARNINGS='ignore',MBR_SESSION_ID=sid,MBR_SOFT_DEADLINE_UNIX=str(deadline))
  if not Path(py).exists():
   run([shutil.which('uv'),'venv',venv,'--python','3.10','-q'],env=env)
   run([shutil.which('uv'),'pip','install','-q','--python',py,'-e',repo+'[eval]','numpy<2','accelerate==0.29.1','peft==0.4.0','setuptools','pandas','scipy','opencv-python-headless<4.12'],env=env)
  run([py,'/root/evaluate_resume.py'],env=env,cwd=repo)
  result['status']='RETURNED'
 except Exception as exc:result.update(status='GLOBAL_BUDGET_STOP' if expired.is_set() else 'STOP_ERROR',error=repr(exc))
 finally:
  timer.cancel()
  if any(proc.poll() is None for proc in processes):stop()
  log.close();result['wall_seconds']=time.time()-started
  result['pairs']=len(prefix(q,p/'pairs'));(sessions/f'{sid}_result.json').write_text(json.dumps(result,indent=2));V.commit()
 return result

@app.function(image=score_image,cpu=(4,4),memory=(8192,8192),timeout=900,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def assemble_score(deadline):
 import sys,time,json,hashlib,subprocess,os,shutil
 sys.path.insert(0,'/root');from resume_store import prefix
 V.reload();p=Path(DEST);old=Path(ROOT+'/full1570');combined=p/'combined_full1570';combined.mkdir(exist_ok=True)
 try:
  assert time.time()<deadline-10
  base=(old/'results1570.jsonl').read_bytes();assert hashlib.sha256(base).hexdigest()=='9c2d55ad4d4cf6cb556255340c2cf2f7894d838d4eec7cf4f7d21089e4aa47fe'
  q=json.loads((p/'questions1020.json').read_text());new=prefix(q,p/'pairs');assert len(new)==1020
  target=combined/'results1570.jsonl';tmp=combined/'results1570.tmp'
  with tmp.open('wb') as fp:
   fp.write(base)
   if not base.endswith(b'\n'):fp.write(b'\n')
   for r in new:fp.write((json.dumps(r)+'\n').encode())
  os.replace(tmp,target)
  for n in ['questions1570.json','selection1570.json','OmniDiff_Real.json','OmniDiff_Render.json']:shutil.copyfile(old/n,combined/n)
  (combined/'FULL_DONE.json').write_text(json.dumps({'complete':True,'pairs':1570,'source_original_pairs':550,'source_resumed_pairs':1020,'multi_session':True,'old_raw_sha256':hashlib.sha256(base).hexdigest()}))
  assignment={r['id']:'original_full_attempt' for r in map(json.loads,base.splitlines())};assignment.update({r['id']:r['session_id'] for r in new})
  (combined/'SESSION_ASSIGNMENTS.json').write_text(json.dumps(assignment,indent=2));V.commit()
  remaining=max(1,deadline-time.time()-5)
  if not all((combined/n).exists() for n in ['METRICS.json','PER_PAIR.json','SELECTION.json']):subprocess.run([sys.executable,'/root/score_resume.py'],check=True,timeout=remaining)
  rows=json.loads((combined/'PER_PAIR.json').read_text());by_session={}
  for row in rows:
   key=assignment[row['id']]+'|'+row['domain'];by_session.setdefault(key,[]).append(row)
  analysis={k:{'n':len(rs),'greedy_CIDEr_x100':sum(r['greedy_CIDEr_x100'] for r in rs)/len(rs),'MBR_CIDEr_x100':sum(r['MBR_CIDEr_x100'] for r in rs)/len(rs),'delta':sum(r['delta'] for r in rs)/len(rs)} for k,rs in by_session.items()}
  (combined/'SESSION_ANALYSIS.json').write_text(json.dumps({'groups':analysis,'note':'Descriptive subsets of the fixed full-domain-reference DF;not isolated session causal effects or separate benchmarks.'},indent=2))
  return {'status':'COMPLETE_SCORED','metrics':json.loads((combined/'METRICS.json').read_text())}
 finally:V.commit()

@app.function(image=modal.Image.debian_slim(python_version='3.12'),cpu=(.25,.25),memory=(512,512),timeout=12600,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def pipeline():
 import json,time,traceback
 from datetime import datetime,timezone
 p=Path(DEST);V.reload();assert json.loads((p/'ADMISSION.json').read_text())['authorized']
 if (p/'PIPELINE_DONE.json').exists():return json.loads((p/'PIPELINE_DONE.json').read_text())
 if (p/'STATE.json').exists():state=json.loads((p/'STATE.json').read_text())
 else:
  state={'started_utc':datetime.now(timezone.utc).isoformat(),'gpu_deadline_unix':time.time()+11220,'cap_usd':11};(p/'STATE.json').write_text(json.dumps(state));V.commit()
 def wait(call,deadline):
  while True:
   if time.time()>=deadline:
    call.cancel(terminate_containers=True);raise TimeoutError('Shared global deadline reached')
   try:return call.get(timeout=min(10,deadline-time.time()))
   except TimeoutError:continue
 try:
  if 'gpu_call_id' in state:call=modal.FunctionCall.from_id(state['gpu_call_id'])
  else:
   call=generate.spawn(state['gpu_deadline_unix']);state['gpu_call_id']=call.object_id;(p/'STATE.json').write_text(json.dumps(state));V.commit()
  result=wait(call,state['gpu_deadline_unix']+5);V.reload()
  from_count=len(list((p/'pairs').glob('*.json')))
  if from_count!=1020:result={'status':'STOP_INCOMPLETE','saved_new_pairs':from_count,'gpu_result':result}
  else:
   if 'score_call_id' in state:call=modal.FunctionCall.from_id(state['score_call_id'])
   else:
    if 'score_deadline_unix' not in state:
     state['score_deadline_unix']=time.time()+900;(p/'STATE.json').write_text(json.dumps(state));V.commit()
    call=assemble_score.spawn(state['score_deadline_unix']);state['score_call_id']=call.object_id;(p/'STATE.json').write_text(json.dumps(state));V.commit()
   result=wait(call,state['score_deadline_unix']+5)
 except Exception:
  result={'status':'STOP_ERROR_OR_GLOBAL_BUDGET','error':traceback.format_exc()}
 result['finished_utc']=datetime.now(timezone.utc).isoformat();(p/'PIPELINE_DONE.json').write_text(json.dumps(result,indent=2));V.commit();print(json.dumps(result),flush=True);return result

@app.local_entrypoint()
def main():pipeline.remote()
