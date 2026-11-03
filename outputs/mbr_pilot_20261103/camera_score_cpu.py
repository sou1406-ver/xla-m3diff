"""CPU packaging correction only: frozen synth_common imports cv2 at module load.
No inference, no new candidates, same selector and scorer bytes as admitted.
"""
from pathlib import Path
import modal
H=Path(__file__).parent;P=H/'camera240';V=modal.Volume.from_name('m3diff');app=modal.App('m3diff-camera240-cpu-dependency-fix')
image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap','pandas','scipy','opencv-python-headless<4.12')
for n in ['utility.py','score_camera.py','score_captions.py','ft_common.py','camera_detector.py']:image=image.add_local_file(str(P/n),'/root/'+n,copy=True)
image=image.add_local_file(str(H/'camera240_score.py'),'/root/score.py',copy=True)
@app.function(image=image,cpu=(4,4),memory=(8192,8192),timeout=240,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def score():
 import subprocess,sys,json,time,hashlib
 V.reload();p=Path('/mnt/m3diff/mbr_pilot_20261103/camera240')
 assert json.loads((p/'GEN_DONE.json').read_text())['complete']
 assert not (p/'CPU_DEPENDENCY_FIX_ATTEMPT.json').exists()
 assert hashlib.sha256(Path('/root/score.py').read_bytes()).hexdigest()==json.loads((p/'ADMISSION.json').read_text())['code_sha256']['camera240_score.py']
 (p/'CPU_DEPENDENCY_FIX_ATTEMPT.json').write_text(json.dumps({'started':time.time(),'reason':'opencv runtime import dependency only','no_gpu':True}));V.commit()
 try:
  subprocess.run([sys.executable,'/root/score.py'],check=True,timeout=220)
  result={'status':'COMPLETE_SCORED','cpu_dependency_fix':True,'metrics':json.loads((p/'METRICS.json').read_text()),'finished_unix':time.time()}
  (p/'FINAL_OUTCOME.json').write_text(json.dumps(result,indent=2));return result
 finally:V.commit()
@app.local_entrypoint()
def main():print(score.remote())
