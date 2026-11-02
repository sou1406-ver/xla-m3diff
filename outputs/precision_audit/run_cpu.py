from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-lora-precision-cpu');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').pip_install('uv').add_local_file(str(HERE/'audit_math.py'),'/root/audit_math.py',copy=True))

@app.function(image=image,cpu=8,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def audit():
 import subprocess,json,zipfile
 out=Path('/mnt/m3diff/precision_audit_v1');out.mkdir(exist_ok=True)
 subprocess.run(['uv','venv','/root/audit-venv','--python','3.10'],check=True)
 py='/root/audit-venv/bin/python'
 subprocess.run(['uv','pip','install','--python',py,'torch==2.1.2','safetensors==0.4.5','numpy<2'],check=True)
 with (out/'audit.log').open('w') as log:
  p=subprocess.Popen([py,'/root/audit_math.py'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  for line in p.stdout:log.write(line);log.flush();print(line.strip(),flush=True)
  rc=p.wait()
 volume.commit()
 if rc:raise RuntimeError('Numerical audit failed')
 (out/'SUCCESS.json').write_text(json.dumps({'GPU_used':False,'checkpoint':'invariance_sft_v1/m3diff-invariance-lora'}))
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.glob('*'):
   if p.suffix in ['.json','.log']:z.write(p,p.name)
 volume.commit()

@app.local_entrypoint()
def main():audit.remote()
