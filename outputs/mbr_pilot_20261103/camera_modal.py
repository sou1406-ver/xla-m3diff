"""One GPU attempt, no resume/retry; score after releasing A10."""
from pathlib import Path
import modal
H=Path(__file__).parent;P=H/'camera240';V=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr-camera240')
ROOT='/mnt/m3diff/mbr_pilot_20261103/camera240'
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv')
image=image.add_local_file(str(P/'evaluate_camera.py'),'/root/evaluate_camera.py',copy=True)
cpu_image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap','pandas','scipy')
for n in ['utility.py','score_camera.py','score_captions.py','ft_common.py','camera_detector.py']:cpu_image=cpu_image.add_local_file(str(P/n),'/root/'+n,copy=True)
cpu_image=cpu_image.add_local_file(str(H/'camera240_score.py'),'/root/score.py',copy=True)

@app.function(image=image,gpu='A10',cpu=(4,4),memory=(32768,32768),timeout=4200,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def generate():
 import os,time,json,subprocess,signal,shutil,threading,hashlib
 V.reload();p=Path(ROOT);assert (p/'ADMISSION.json').exists();assert not (p/'GPU_ATTEMPT.json').exists(),'No retry'
 start=time.time();deadline=start+4080;(p/'GPU_ATTEMPT.json').write_text(json.dumps({'started':start,'deadline':deadline,'cap':2}));V.commit()
 procs=[];expired=threading.Event()
 def stop():
  expired.set()
  for proc in procs:
   if proc.poll() is None:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
 timer=threading.Timer(4080,stop);timer.daemon=True;timer.start()
 result={'status':'STOP_ERROR_NO_RETRY'}
 try:
  hashes=json.loads((p/'ARTIFACT_SHA256.json').read_text())
  assert hashlib.sha256(Path('/root/evaluate_camera.py').read_bytes()).hexdigest()==hashes['evaluate_camera.py']
  repo='/root/M3Diff';shutil.copytree('/mnt/m3diff/baseline_reproduction_v1/repo',repo,ignore=shutil.ignore_patterns('.git','__pycache__'))
  env=dict(os.environ,PYTHONPATH=repo+':/root',HF_HOME='/mnt/m3diff/baseline_cache/huggingface',HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',PYTHONWARNINGS='ignore',MBR_SOFT_DEADLINE_UNIX=str(deadline))
  def run(cmd):
   assert not expired.is_set()
   with (p/'generation.log').open('a') as log:
    proc=subprocess.Popen(cmd,env=env,cwd=repo,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);procs.append(proc)
    if expired.is_set():stop()
    last=''
    while proc.poll() is None:
     try:proc.wait(timeout=10)
     except subprocess.TimeoutExpired:pass
     V.commit()
     if (p/'PROGRESS.json').exists():
      msg=(p/'PROGRESS.json').read_text()
      if msg!=last:print('CAMERA_PROGRESS',msg,flush=True);last=msg
    assert proc.returncode==0,f'exit{proc.returncode}'
  py='/root/venv/bin/python';run(['uv','venv','/root/venv','--python','3.10','-q'])
  run(['uv','pip','install','-q','--python',py,'-e',repo+'[eval]','numpy<2','accelerate==0.29.1','peft==0.4.0','setuptools','pandas','scipy','opencv-python-headless<4.12'])
  run([py,'/root/evaluate_camera.py']);done=json.loads((p/'GEN_DONE.json').read_text());result={'status':'GENERATED' if done['complete'] else 'STOP_PARTIAL_NO_RETRY',**done}
 except Exception as e:result['error']=repr(e)
 finally:
  timer.cancel();stop();result['gpu_worker_seconds']=time.time()-start;(p/'GPU_DONE.json').write_text(json.dumps(result,indent=2));V.commit()
 return result

@app.function(image=cpu_image,cpu=(4,4),memory=(8192,8192),timeout=240,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def score():
 import subprocess,sys,json
 V.reload();p=Path(ROOT)
 try:
  assert json.loads((p/'GEN_DONE.json').read_text())['complete']
  subprocess.run([sys.executable,'/root/score.py'],check=True,timeout=220)
  return json.loads((p/'METRICS.json').read_text())
 finally:V.commit()

@app.function(image=modal.Image.debian_slim(python_version='3.12'),cpu=(.25,.25),memory=(512,512),timeout=4590,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def pipeline():
 import json,time,traceback
 V.reload();p=Path(ROOT);assert not (p/'PIPELINE_ATTEMPT.json').exists(),'No pipeline retry'
 p.joinpath('PIPELINE_ATTEMPT.json').write_text(json.dumps({'started':time.time()}));V.commit()
 result={}
 try:
  for n,h in json.loads((p/'ARTIFACT_SHA256.json').read_text()).items():
   import hashlib
   assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
  qs=json.loads((p/'questions.json').read_text());assert len(qs)==240
  for q in qs:
   assert all(c['from']=='human' for c in q['conversations'])
   for name in q['image']:assert (Path('/mnt/m3diff/ft/camtest')/name).is_file()
  (p/'CPU_READY.json').write_text('{}');V.commit()
  result=generate.remote();V.reload()
  if result.get('complete'):result={'status':'COMPLETE_SCORED','generation':result,'metrics':score.remote()}
 except Exception:result={'status':'STOP_ERROR_NO_RETRY','error':traceback.format_exc()}
 result['finished_unix']=time.time();V.reload();(p/'PIPELINE_DONE.json').write_text(json.dumps(result,indent=2));V.commit();print(json.dumps(result),flush=True);return result

@app.local_entrypoint()
def main():pipeline.remote()
