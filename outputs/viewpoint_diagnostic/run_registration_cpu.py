"""CPU-only feature extraction; thresholds are selected on dev and locked before validation."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-registration-cpu-v1')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').pip_install('numpy<2','Pillow==11.1.0','opencv-python-headless==4.10.0.84')
 .add_local_file(str(HERE/'registration_gate.py'),'/root/registration_gate.py',copy=True)
 .add_local_file(str(HERE/'registration_protocol.json'),'/root/registration_protocol.json',copy=True))

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def extract(partition:str):
 import sys,json,hashlib
 sys.path.insert(0,'/root');from registration_gate import features
 root=Path('/mnt/m3diff/viewpoint_diagnostic_v1');manifest=json.loads((root/'dataset/manifest.json').read_text());rows=[]
 if partition=='validation':
  protocol=json.loads(Path('/root/registration_protocol.json').read_text());assert protocol['registration_source_sha256']==hashlib.sha256(Path('/root/registration_gate.py').read_bytes()).hexdigest()
  (root/'registration_protocol.json').write_text(json.dumps(protocol,indent=2))
 for r in manifest:
  if r['partition']!=partition:continue
  f=features(*(root/'dataset'/im for im in r['image']));row={k:r[k] for k in ['id','scene','split','partition','condition']};row['features']=f;rows.append(row)
  print(r['id'],json.dumps(f),flush=True)
 (root/f'registration_{partition}_features.json').write_text(json.dumps(rows,indent=2)+'\n')
 (root/'registration_gate_source_sha256.txt').write_text(hashlib.sha256(Path('/root/registration_gate.py').read_bytes()).hexdigest())
 if partition=='validation':
  import numpy as np
  from PIL import Image
  stress=[];folder=root/'registration_stress';folder.mkdir(exist_ok=True)
  for r in manifest:
   if r['partition']!='validation' or r['condition']!='identity':continue
   source=root/'dataset'/r['image'][0];original=np.array(Image.open(source).convert('RGB'));h,w=original.shape[:2]
   for kind in ['square8','thin2x32','brightness_plus8']:
    altered=original.copy()
    if kind=='brightness_plus8':altered=np.minimum(altered.astype(np.int16)+8,255).astype(np.uint8)
    else:
     ph,pw=(8,8) if kind=='square8' else (32,2)
     y,x=h//2-ph//2,w//2-pw//2;altered[y:y+ph,x:x+pw]=255-altered[y:y+ph,x:x+pw]
    target=folder/(r['scene']+'_'+kind+'.png');Image.fromarray(altered).save(target)
    f=features(source,target);stress.append({'id':r['scene']+'__'+kind,'scene':r['scene'],'kind':kind,'expected':'Appearance changed; must not route to no-change. Synthetic stress, not a realistic object-change benchmark.','features':f})
  (root/'registration_stress_features.json').write_text(json.dumps(stress,indent=2))
  print('STRESS DONE',len(stress),flush=True)
 volume.commit();print('CPU EXTRACTION DONE',partition,len(rows),flush=True)

@app.local_entrypoint()
def main(partition:str='dev'):
 assert partition in ['dev','validation'];extract.remote(partition)
