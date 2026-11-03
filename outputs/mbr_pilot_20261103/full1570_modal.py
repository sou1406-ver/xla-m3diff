from pathlib import Path
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr-full1570')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv','nbformat','nbclient','ipykernel')
for n in ['evaluate1570.py','full1570.ipynb']:image=image.add_local_file(str(HERE/n),'/root/'+n,copy=True)
score_image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap')
for n in ['score1570_cpu.py','utility.py']:score_image=score_image.add_local_file(str(HERE/n),'/root/'+n,copy=True)
@app.function(image=image,gpu='A100-80GB',cpu=(4,4),memory=(32768,32768),timeout=19200,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def evaluate():
 import os,time,json,threading,traceback,nbformat
 from nbclient import NotebookClient
 p=Path('/mnt/m3diff/mbr_pilot_20261103/full1570');assert (p/'ADMISSION.json').exists();assert not (p/'FULL_ATTEMPT.json').exists()
 start=time.time();os.environ['MBR_SOFT_DEADLINE_UNIX']=str(start+18900);finished=threading.Event();nb=nbformat.read('/root/full1570.ipynb',as_version=4)
 def monitor():
  while not finished.wait(30):
   try:
    if (p/'PROGRESS.json').exists():print('PROGRESS',(p/'PROGRESS.json').read_text(),flush=True)
    v.commit()
   except Exception as e:print('MONITOR',type(e).__name__,flush=True)
 watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
 try:NotebookClient(nb,timeout=19170,kernel_name='python3',allow_errors=False,resources={'metadata':{'path':'/root'}}).execute()
 except Exception:
  (p/'FULL_ERROR.txt').write_text(traceback.format_exc());raise
 finally:
  finished.set();watcher.join(timeout=5);nbformat.write(nb,p/'executed.ipynb');(p/'FULL_JOB_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-start}));v.commit()
@app.function(image=score_image,cpu=(4,4),memory=(8192,8192),timeout=900,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def score():
 import runpy
 try:runpy.run_path('/root/score1570_cpu.py',run_name='__main__')
 finally:v.commit()

# A durable CPU coordinator chains inference and scoring even after the local
# client disconnects. It does not reserve a GPU while scoring or waiting.
@app.function(image=modal.Image.debian_slim(python_version='3.12'),cpu=(.25,.25),memory=(512,512),timeout=21060,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def pipeline():
 import json,time,traceback
 from datetime import datetime,timezone
 p=Path('/mnt/m3diff/mbr_pilot_20261103/full1570')
 assert json.loads((p/'ADMISSION.json').read_text())['authorized'] is True
 assert not (p/'PIPELINE_ATTEMPT.json').exists(),'No automatic retry'
 started=time.time()
 (p/'PIPELINE_ATTEMPT.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'cap_usd':18,'no_training':True}))
 v.commit()
 try:
  evaluate.remote()
  v.reload()
  done=json.loads((p/'FULL_DONE.json').read_text())
  if not done['complete']:
   result={'status':'STOP_PARTIAL_NO_RETRY','pairs':done['pairs'],'full_benchmark_complete':False}
  else:
   score.remote()
   v.reload()
   metrics=json.loads((p/'METRICS.json').read_text())
   result={'status':'COMPLETE_SCORED','pairs':1570,'full_benchmark_complete':True,'domains':metrics['domains']}
 except Exception:
  result={'status':'STOP_ERROR_NO_RETRY','full_benchmark_complete':False,'error':traceback.format_exc()}
 finally:
  result['wall_seconds']=time.time()-started
  result['finished_utc']=datetime.now(timezone.utc).isoformat()
  (p/'PIPELINE_DONE.json').write_text(json.dumps(result,indent=2));v.commit()
 print(json.dumps(result,indent=2),flush=True)
 return result

@app.local_entrypoint()
def main():pipeline.remote()
