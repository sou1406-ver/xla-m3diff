from pathlib import Path
import modal
HERE=Path(__file__).parent;app=modal.App('m3diff-r64-v2-final-evaluation');volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git','default-jre-headless').pip_install('uv','nbformat','nbclient','ipykernel','pandas')
for name in ['evaluate-v2.ipynb','evaluate_stages.py','score_val.py','camera_detector.py','score_camera_frozen.py','score_captions_frozen.py','ft_common_frozen.py']:
    image=image.add_local_file(str(HERE/name),'/root/'+name,copy=True)
@app.function(image=image,gpu='A10',cpu=(4,4),memory=(32768,32768),timeout=3600,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':volume})
def evaluate():
    import nbformat,json,time,traceback,subprocess,threading
    from nbclient import NotebookClient
    root=Path('/mnt/m3diff/r64_v2_final_round');out=root/'evaluation';out.mkdir(exist_ok=True)
    assert (root/'TRAIN_DONE.json').exists();assert not (out/'EVAL_ATTEMPT.json').exists()
    start=time.time();gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip();assert 'A10' in gpu
    (out/'EVAL_ATTEMPT.json').write_text(json.dumps({'started':start,'gpu':gpu,'timeout_seconds':3600}));volume.commit()
    nb=nbformat.read('/root/evaluate-v2.ipynb',as_version=4)
    finished=threading.Event()
    def monitor():
        while not finished.wait(30):
            try:
                for name in ['TIMINGS.json','GATE_RESULT.json']:
                    if (out/name).exists():print(name,(out/name).read_text(),flush=True)
                volume.commit()
            except Exception as e:print('MONITOR',type(e).__name__,flush=True)
    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
    def done(cell,cell_index,**kwargs):nbformat.write(nb,out/'executed.ipynb');volume.commit();print('CELL_DONE',cell_index,flush=True)
    try:NotebookClient(nb,timeout=3500,kernel_name='python3',allow_errors=False,on_cell_executed=done,resources={'metadata':{'path':'/root'}}).execute()
    except Exception:
        (out/'EVALUATION_ERROR.txt').write_text(traceback.format_exc());raise
    finally:
        finished.set();watcher.join(timeout=5)
        nbformat.write(nb,out/'executed.ipynb');(out/'JOB_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-start,'gpu':gpu}));volume.commit()
@app.local_entrypoint()
def main():evaluate.remote()
