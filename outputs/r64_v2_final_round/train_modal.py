from pathlib import Path
import modal
HERE=Path(__file__).parent;app=modal.App('m3diff-r64-v2-final-train');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv','nbformat','nbclient','ipykernel','pandas')
 .add_local_file(str(HERE/'train-v2.ipynb'),'/root/train-v2.ipynb',copy=True)
 .add_local_file(str(HERE/'train_audited.py'),'/root/train_audited.py',copy=True)
 .add_local_file(str(HERE.parents[1]/'work/train.py') if modal.is_local() else '/root/train_source.py','/root/train_source.py',copy=True))
@app.function(image=image,gpu='A100-80GB',cpu=(4,4),memory=(32768,32768),timeout=5220,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':volume})
def train():
    import nbformat,json,time,os,traceback,subprocess,threading
    from nbclient import NotebookClient
    out=Path('/mnt/m3diff/r64_v2_final_round');assert (out/'DATA_APPROVED.json').exists()
    assert not (out/'TRAIN_ATTEMPT.json').exists(),'Only one training attempt allowed'
    start=time.time();os.environ['V2_SOFT_DEADLINE_UNIX']=str(start+5040)
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader,nounits'],text=True).strip()
    assert 'A100' in gpu and int(gpu.split(',')[-1])>=75000,gpu
    (out/'TRAIN_ATTEMPT.json').write_text(json.dumps({'started':start,'gpu':gpu,'timeout_seconds':5220,'soft_stop_seconds':5040,'cpu_limit':4,'memory_limit_mib':32768}));volume.commit()
    nb=nbformat.read('/root/train-v2.ipynb',as_version=4)
    finished=threading.Event()
    def monitor():
        while not finished.wait(30):
            try:
                if (out/'TRAIN_PROGRESS.json').exists():print('TRAIN_PROGRESS',(out/'TRAIN_PROGRESS.json').read_text(),flush=True)
                volume.commit()
            except Exception as e:print('MONITOR',type(e).__name__,flush=True)
    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
    def done(cell,cell_index,**kwargs):
        nbformat.write(nb,out/'train_executed.ipynb');volume.commit();print('CELL_DONE',cell_index,flush=True)
    try:NotebookClient(nb,timeout=5300,kernel_name='python3',allow_errors=False,on_cell_executed=done,resources={'metadata':{'path':'/root'}}).execute()
    except Exception:
        (out/'TRAIN_ERROR.txt').write_text(traceback.format_exc());raise
    finally:
        finished.set();watcher.join(timeout=5)
        nbformat.write(nb,out/'train_executed.ipynb');(out/'TRAIN_JOB_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-start,'gpu':gpu}));volume.commit()
@app.local_entrypoint()
def main():train.remote()
