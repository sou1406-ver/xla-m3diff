"""End-to-end CLI check against the saved frozen-policy predictions. CPU only."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-registration-cli-check')
volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.10').pip_install('numpy<2','Pillow==11.1.0','opencv-python-headless==4.10.0.84')
for name in ['registration_gate.py','apply_registration_gate.py','registration_protocol.json','registration_guarded.jsonl','baseline_clean.jsonl']:
 image=image.add_local_file(str(HERE/name),'/root/'+name,copy=True)

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def check():
 import json,subprocess,sys
 root=Path('/mnt/m3diff/viewpoint_diagnostic_v1')
 subprocess.run([sys.executable,'/root/apply_registration_gate.py','--manifest',str(root/'dataset/manifest.json'),'--image-root',str(root/'dataset'),
  '--input','/root/baseline_clean.jsonl','--output',str(root/'cli_guarded.jsonl'),'--audit',str(root/'cli_audit.json'),
  '--mode','registration','--protocol','/root/registration_protocol.json'],check=True)
 rows=lambda p:[json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
 actual=rows(root/'cli_guarded.jsonl');expected=rows('/root/registration_guarded.jsonl');orig=rows('/root/baseline_clean.jsonl')
 assert len(actual)==len(expected)==60
 assert {r['id']:r for r in actual}=={r['id']:r for r in expected}
 assert [{k:v for k,v in r.items() if k!='caption'} for r in actual]==[{k:v for k,v in r.items() if k!='caption'} for r in orig]
 (root/'CLI_CHECK_SUCCESS.json').write_text(json.dumps({'rows':60,'all_predictions_match_frozen_policy':True,'metadata_and_input_order_preserved':True,'GPU_used':False},indent=2))
 volume.commit();print('END-TO-END CLI PASS, 60 predictions',flush=True)

@app.local_entrypoint()
def main():check.remote()
