from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-r64-camera-eval-20261102')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.12').apt_install('git','default-jre-headless')
       .pip_install('uv','nbformat','nbclient','ipykernel','pandas')
       .add_local_file(str(HERE/'r64-camera-only.ipynb'),'/root/r64-camera-only.ipynb',copy=True))
@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=2400,scaledown_window=2,retries=0,volumes={'/mnt/m3diff':volume})
def evaluate():
    import nbformat,time,json,subprocess,traceback
    from nbclient import NotebookClient
    out=Path('/mnt/m3diff/r64_camera_eval_20261102');out.mkdir(exist_ok=True)
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()
    assert 'A10' in gpu,gpu
    started=time.time();nb=nbformat.read('/root/r64-camera-only.ipynb',as_version=4)
    def done(cell,cell_index,**kwargs):
        nbformat.write(nb,out/'executed.ipynb');volume.commit()
        for o in cell.get('outputs',[]):
            if o.get('output_type')=='stream':print(o.get('text','')[-3500:],flush=True)
        print('CELL DONE',cell_index,flush=True)
    client=NotebookClient(nb,timeout=1800,kernel_name='python3',allow_errors=False,on_cell_executed=done,resources={'metadata':{'path':'/root'}})
    try:client.execute()
    except Exception:
        (out/'ERROR.txt').write_text(traceback.format_exc());raise
    finally:
        nbformat.write(nb,out/'executed.ipynb')
        (out/'job_timing.json').write_text(json.dumps({'wall_seconds':time.time()-started,'gpu':gpu,'returned_at':time.time()}))
        volume.commit()
@app.local_entrypoint()
def main():evaluate.remote()
