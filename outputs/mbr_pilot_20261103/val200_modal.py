from pathlib import Path
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr-val200')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv','nbformat','nbclient','ipykernel')
for n in ['evaluate200.py','val200.ipynb']:image=image.add_local_file(str(HERE/n),'/root/'+n,copy=True)
@app.function(image=image,gpu='A10',cpu=(4,4),memory=(32768,32768),timeout=7200,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def evaluate():
 import os,time,json,threading,traceback,nbformat
 from nbclient import NotebookClient
 p=Path('/mnt/m3diff/mbr_pilot_20261103/val200');assert (p/'ADMISSION.json').exists();assert not (p/'VAL_ATTEMPT.json').exists()
 start=time.time();os.environ['MBR_SOFT_DEADLINE_UNIX']=str(start+6900);finished=threading.Event();nb=nbformat.read('/root/val200.ipynb',as_version=4)
 def monitor():
  while not finished.wait(30):
   try:
    if (p/'PROGRESS.json').exists():print('PROGRESS',(p/'PROGRESS.json').read_text(),flush=True)
    v.commit()
   except Exception as e:print('MONITOR',type(e).__name__,flush=True)
 watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
 try:NotebookClient(nb,timeout=7170,kernel_name='python3',allow_errors=False,resources={'metadata':{'path':'/root'}}).execute()
 except Exception:
  (p/'VAL_ERROR.txt').write_text(traceback.format_exc());raise
 finally:
  finished.set();watcher.join(timeout=5);nbformat.write(nb,p/'executed.ipynb');(p/'VAL_JOB_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-start}));v.commit()
@app.local_entrypoint()
def main():evaluate.remote()
