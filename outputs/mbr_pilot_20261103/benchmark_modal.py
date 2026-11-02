from pathlib import Path
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr20-benchmark')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv','nbformat','nbclient','ipykernel')
for n in ['benchmark.py','benchmark.ipynb']:image=image.add_local_file(str(HERE/n),'/root/'+n,copy=True)
@app.function(image=image,gpu='A10',cpu=(4,4),memory=(32768,32768),timeout=1740,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def benchmark():
 import os,time,json,threading,traceback,nbformat
 from nbclient import NotebookClient
 p=Path('/mnt/m3diff/mbr_pilot_20261103');assert (p/'CPU_READY.json').exists();assert not (p/'BENCHMARK_ATTEMPT.json').exists()
 start=time.time();os.environ['MBR_SOFT_DEADLINE_UNIX']=str(start+1500);finished=threading.Event()
 nb=nbformat.read('/root/benchmark.ipynb',as_version=4)
 def monitor():
  while not finished.wait(30):
   try:
    if (p/'PROGRESS.json').exists():print('PROGRESS',(p/'PROGRESS.json').read_text(),flush=True)
    v.commit()
   except Exception as e:print('MONITOR',type(e).__name__,flush=True)
 watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
 try:NotebookClient(nb,timeout=1710,kernel_name='python3',allow_errors=False,resources={'metadata':{'path':'/root'}}).execute()
 except Exception:
  (p/'BENCHMARK_ERROR.txt').write_text(traceback.format_exc());raise
 finally:
  finished.set();watcher.join(timeout=5);nbformat.write(nb,p/'benchmark_executed.ipynb');(p/'BENCHMARK_JOB_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-start}));v.commit()
@app.local_entrypoint()
def main():benchmark.remote()
