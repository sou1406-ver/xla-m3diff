from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-safe-registration-check');volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.10').pip_install('numpy<2','Pillow==11.1.0','opencv-python-headless==4.10.0.84')
for name in ['safe_pipeline.py','registration_gate_frozen.py','registration_protocol_frozen.json']:
 image=image.add_local_file(str(HERE/name),'/root/'+name,copy=True)

@app.function(image=image,cpu=4,memory=8192,timeout=300,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def check():
 import json,subprocess,sys,zipfile
 root=Path('/mnt/m3diff/viewpoint_extension_v1');out=root/'safe_check';out.mkdir(exist_ok=True)
 manifest=json.loads((root/'manifest.json').read_text());ids=['bicycle_alley__identity','bicycle_alley__zoom_out_reverse_1p10','bicycle_alley__square32_delta16','render_kitchen__natural']
 selected=[next(r for r in manifest if r['id']==rid) for rid in ids]
 selected.append({'id':'bicycle_alley__zoom_in_edited','image':['bicycle_alley_source.png','bicycle_alley_zoom_in_1p10_edited.png']})
 (out/'manifest.json').write_text(json.dumps(selected));rows=[{'id':r['id'],'caption':'sentinel_original_caption_'+r['id'],'metadata_token':i} for i,r in enumerate(selected)]
 (out/'input.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 subprocess.run([sys.executable,'/root/safe_pipeline.py','--manifest',str(out/'manifest.json'),'--image-root',str(root/'dataset'),'--input',str(out/'input.jsonl'),
  '--output',str(out/'output.jsonl'),'--audit',str(out/'audit.json'),'--protocol','/root/registration_protocol_frozen.json','--registration-advice'],check=True)
 result=[json.loads(l) for l in (out/'output.jsonl').read_text().splitlines()];audit=json.loads((out/'audit.json').read_text())
 assert len(result)==5
 for before,after,a in zip(rows,result,audit):
  assert {k:v for k,v in before.items() if k!='caption'}=={k:v for k,v in after.items() if k!='caption'}
  assert a['replace_caption']==before['id'].endswith('__identity')
  if not a['replace_caption']:assert before==after
 assert audit[2]['v1_would_replace'] and not audit[2]['replace_caption']
 (out/'SUCCESS.json').write_text(json.dumps({'n':5,'exact_identity_only_replacement':True,'all_nonidentity_captions_unchanged':True,'metadata_order_preserved':True,'old_v1_counterexample_now_preserved':True,'GPU_used':False},indent=2))
 with zipfile.ZipFile(root/'safe_check.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.glob('*'):z.write(p,p.name)
 volume.commit();print('SAFE CLI CHECK PASSED',flush=True)

@app.local_entrypoint()
def main():check.remote()
