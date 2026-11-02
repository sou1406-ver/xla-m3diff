from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-r64-v2-final-prepare')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').pip_install('numpy<2','opencv-python-headless<4.12','pandas','Pillow')
 .add_local_file(str(HERE/'prepare_data.py'),'/root/prepare_data.py',copy=True)
 .add_local_file(str(HERE/'DATA_RECIPE.json'),'/root/DATA_RECIPE.json',copy=True)
 .add_local_file(str(HERE/'CAPTION_POLICY.json'),'/root/CAPTION_POLICY.json',copy=True)
 .add_local_file(str(HERE/'camera_detector.py'),'/root/camera_detector.py',copy=True)
 .add_local_file(str(HERE.parent/'checkpoint_audit_20261102/ft/code/make_ft_data.py'),'/root/make_ft_data.py',copy=True)
 .add_local_file(str(HERE.parent/'r64_val_precheck_20261102/SOURCE_annotation.jsonl'),'/root/annotation.jsonl',copy=True)
 .add_local_file(str(HERE.parent/'r64_val_precheck_20261102/IMAGE_MANIFEST.json'),'/root/IMAGE_MANIFEST.json',copy=True))
@app.function(image=image,cpu=(4,4),memory=(8192,8192),timeout=1800,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':volume})
def prepare():
    import runpy,time,json,traceback
    out=Path('/mnt/m3diff/r64_v2_final_round');out.mkdir(exist_ok=True)
    assert not (out/'DATA_AUDIT.json').exists(),'Do not silently regenerate frozen data'
    t=time.time()
    try:runpy.run_path('/root/prepare_data.py',run_name='__main__',init_globals={'commit':volume.commit})
    except Exception:
        (out/'PREPARATION_ERROR.txt').write_text(traceback.format_exc());raise
    finally:
        (out/'PREPARATION_TIMING.json').write_text(json.dumps({'wall_seconds':time.time()-t}));volume.commit()
@app.local_entrypoint()
def main():prepare.remote()
