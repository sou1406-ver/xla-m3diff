"""Frozen-gate audit on new scenes. All functions are CPU-only and bounded."""
from pathlib import Path
import modal
HERE=Path(__file__).parent;OLD=HERE.parent/'viewpoint_diagnostic'
app=modal.App('m3diff-viewpoint-extension-cpu')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').pip_install('numpy<2','Pillow==11.1.0','opencv-python-headless==4.10.0.84')
 .add_local_file(str(OLD/'registration_gate.py'),'/root/registration_gate.py',copy=True)
 .add_local_file(str(OLD/'registration_protocol.json'),'/root/registration_protocol.json',copy=True))
if (HERE/'selection_locked.json').exists():image=image.add_local_file(str(HERE/'selection_locked.json'),'/root/selection_locked.json',copy=True)
if (HERE/'composed_locked.json').exists():image=image.add_local_file(str(HERE/'composed_locked.json'),'/root/composed_locked.json',copy=True)

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def gallery():
 import json,random,hashlib,zipfile
 import numpy as np
 from PIL import Image,ImageOps,ImageDraw
 root=Path('/mnt/m3diff');base=root/'baseline_cache/OmniDiff';out=root/'viewpoint_extension_v1';out.mkdir(exist_ok=True)
 prior=json.loads((root/'viewpoint_diagnostic_v1/dataset/manifest.json').read_text())
 exclude={p for r in prior for p in r.get('source_dataset_images',[])};selected=[];rng=random.Random(2026102721)
 for split in ['Real','Render']:
  paths=[p for p in sorted((base/split/'test/images').glob('*')) if p.is_file() and p.suffix.lower() in ['.jpg','.png','.jpeg'] and p.relative_to(base).as_posix() not in exclude]
  rng.shuffle(paths);paths=paths[:64];vectors=[]
  print('READ CANDIDATES',split,len(paths),flush=True)
  for j,p in enumerate(paths):
   vectors.append(np.asarray(Image.open(p).convert('RGB').resize((12,12)),np.float32).ravel()/255)
   if j%16==15:print('READ',split,j+1,flush=True)
  vec=np.stack(vectors);indices=[0];distance=((vec-vec[0])**2).mean(axis=1)
  for _ in range(15):
   i=int(np.argmax(distance));indices.append(i);distance=np.minimum(distance,((vec-vec[i])**2).mean(axis=1));distance[indices]=-1
  board=Image.new('RGB',(1600,1640),'#eeeeee');draw=ImageDraw.Draw(board)
  for j,i in enumerate(indices):
   p=paths[i];r={'index':len(selected),'split':split,'image':p.relative_to(base).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};selected.append(r)
   x=(j%4)*400;y=(j//4)*410
   im=ImageOps.contain(Image.open(p).convert('RGB'),(392,375));board.paste(im,(x+(392-im.width)//2,y+30+(375-im.height)//2));draw.text((x+4,y+6),f"{r['index']:02d} {p.name}",fill='black')
  board.save(out/f'gallery_{split}.jpg',quality=95)
 (out/'candidates.json').write_text(json.dumps(selected,indent=2))
 with zipfile.ZipFile(out/'gallery.zip','w',zipfile.ZIP_DEFLATED) as z:
  for n in ['candidates.json','gallery_Real.jpg','gallery_Render.jpg']:z.write(out/n,n)
 volume.commit();print('GALLERY DONE; no gate outcomes computed.',flush=True)

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,math,hashlib,zipfile
 import numpy as np
 from PIL import Image,ImageOps,ImageDraw
 root=Path('/mnt/m3diff');base=root/'baseline_cache/OmniDiff';out=root/'viewpoint_extension_v1'
 lock=json.loads(Path('/root/selection_locked.json').read_text());(out/'selection_locked.json').write_text(json.dumps(lock,indent=2))
 data=out/'dataset';data.mkdir(exist_ok=True);boards=out/'natural_boards';boards.mkdir(exist_ok=True);manifest=[]
 def transformed(im,angle,zoom):
  w,h=im.size;t=math.radians(angle);c,s=math.cos(t),math.sin(t);safe=max(abs(c)+h/w*abs(s),abs(c)+w/h*abs(s))*(1.002 if angle else 1)
  scale=safe*zoom;a,b,d,e=c/scale,-s/scale,s/scale,c/scale;x0=w/2-a*w/2-b*h/2;y0=h/2-d*w/2-e*h/2
  return im.transform(im.size,Image.Transform.AFFINE,(a,b,x0,d,e,y0),resample=Image.Resampling.BICUBIC)
 for row in lock['selection']:
  source=base/row['image'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
  scene=row['scene'];im=Image.open(source).convert('RGB');arr=np.array(im);h,w=arr.shape[:2];src=scene+'_source.png';im.save(data/src)
  files={}
  for condition,angle,zoom in [('identity',0,1),('zoom_in_1p10',0,1.1),('roll_8_safe',8,1),('roll_minus8_zoom',-8,1.1)]:
   name=scene+'_'+condition+'.png';pic=transformed(im,angle,zoom);pic.save(data/name);files[condition]=name
   manifest.append({'id':scene+'__'+condition,'scene':scene,'split':row['split'],'condition':condition,'kind':'nochange','image':[src,name]})
  manifest.append({'id':scene+'__zoom_out_reverse_1p10','scene':scene,'split':row['split'],'condition':'zoom_out_reverse_1p10','kind':'nochange','image':[files['zoom_in_1p10'],src]})
  for condition in lock['primary_stress']+lock['sensitivity_stress']:
   changed=arr.copy()
   if condition.startswith('brightness_'):changed=np.minimum(arr.astype(np.int16)+(8 if condition.endswith('8') else 1),255).astype(np.uint8)
   else:
    ph,pw={'square32_delta16':(32,32),'square8_invert':(8,8),'thin2x32_invert':(32,2),'square16_delta4':(16,16),'one_pixel_invert':(1,1)}[condition]
    y,x=h//2-ph//2,w//2-pw//2;patch=changed[y:y+ph,x:x+pw]
    if 'invert' in condition:patch[:]=255-patch
    else:
     delta=16 if condition.endswith('16') else 4;delta=-delta if patch.mean()>127 else delta
     patch[:]=np.clip(patch.astype(np.int16)+delta,0,255).astype(np.uint8)
   n=int(np.any(changed!=arr,axis=2).sum());assert n>0
   name=scene+'_'+condition+'.png';Image.fromarray(changed).save(data/name)
   manifest.append({'id':scene+'__'+condition,'scene':scene,'split':row['split'],'condition':condition,
    'kind':'primary_stress' if condition in lock['primary_stress'] else 'sensitivity_stress','image':[src,name],'changed_native_pixels':n,'native_size':[w,h]})
  qs=json.loads((root/'baseline_reproduction_v1/repo'/f"data/evaluation/prompt/OmniDiff_{row['split']}_test.json").read_text())
  matches=sorted([q for q in qs if row['image'] in q['image']],key=lambda q:(q['image'][0]!=row['image'],q['id']))
  if matches:
   q=matches[0];paths=[]
   board=Image.new('RGB',(1500,800),'#eeeeee');draw=ImageDraw.Draw(board)
   for k,rel in enumerate(q['image']):
    p=scene+f'_natural_{k}.png';pic=Image.open(base/rel).convert('RGB');pic.save(data/p);paths.append(p)
    thumb=ImageOps.contain(pic,(740,750));board.paste(thumb,(750*k+(740-thumb.width)//2,40+(750-thumb.height)//2));draw.text((750*k+8,10),scene+(' BEFORE' if k==0 else ' AFTER'),fill='black')
   board.save(boards/(scene+'.jpg'),quality=95)
   manifest.append({'id':scene+'__natural','scene':scene,'split':row['split'],'condition':'natural','kind':'natural_pending_review','image':paths,'official_pair_id':q['id'],'original_images':q['image']})
  print('PREPARED',scene,flush=True)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(data/'manifest.json').write_text(json.dumps(manifest,indent=2))
 with zipfile.ZipFile(out/'natural_review.zip','w',zipfile.ZIP_DEFLATED) as z:
  z.write(out/'manifest.json','manifest.json')
  for p in boards.glob('*.jpg'):z.write(p,'natural_boards/'+p.name)
 volume.commit();print('PREPARED',len(manifest),'pairs; no gate outcomes computed.',flush=True)

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def audit():
 import sys,json,hashlib,zipfile
 sys.path.insert(0,'/root');from registration_gate import features,decide
 root=Path('/mnt/m3diff/viewpoint_extension_v1');lock=json.loads(Path('/root/selection_locked.json').read_text())
 assert json.loads((root/'selection_locked.json').read_text())==lock
 assert hashlib.sha256(Path('/root/registration_gate.py').read_bytes()).hexdigest()==lock['frozen_registration_source_sha256']
 manifest=json.loads((root/'manifest.json').read_text());rows=[]
 for r in manifest:
  f=features(*(root/'dataset'/im for im in r['image']));d=decide(f,lock['frozen_thresholds']);rows.append({**r,'features':f,'decision':d})
  print('AUDITED',r['id'],flush=True)
 (root/'audit.json').write_text(json.dumps(rows,indent=2));(root/'AUDIT_SUCCESS.json').write_text(json.dumps({'n':len(rows),'GPU_used':False,'source_and_thresholds_match_frozen_v1':True}))
 from PIL import Image,ImageOps,ImageDraw
 import numpy as np
 proofs=root/'failure_previews';proofs.mkdir(exist_ok=True)
 picked=sorted([r for r in rows if r['kind']=='primary_stress' and r['decision']['accept_no_scene_change']],key=lambda r:r['id'])[:4]
 for r in picked:
  a=Image.open(root/'dataset'/r['image'][0]).convert('RGB');b=Image.open(root/'dataset'/r['image'][1]).convert('RGB')
  diff=np.minimum(np.abs(np.asarray(a).astype(np.int16)-np.asarray(b).astype(np.int16))*12,255).astype(np.uint8)
  board=Image.new('RGB',(1800,690),'#eeeeee');draw=ImageDraw.Draw(board)
  for k,(pic,label) in enumerate([(a,'BEFORE'),(b,'AFTER'),(Image.fromarray(diff),'ABS DIFFERENCE x12')]):
   thumb=ImageOps.contain(pic,(590,630));board.paste(thumb,(k*600+(590-thumb.width)//2,45+(630-thumb.height)//2));draw.text((k*600+8,8),r['id']+' '+label,fill='black')
  board.save(proofs/(r['id']+'.jpg'),quality=96)
 with zipfile.ZipFile(root/'failure_previews.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in proofs.glob('*.jpg'):z.write(p,p.name)
 with zipfile.ZipFile(root/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for n in ['manifest.json','selection_locked.json','audit.json','AUDIT_SUCCESS.json']:z.write(root/n,n)
 volume.commit();print('AUDIT DONE',len(rows),flush=True)

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def composed():
 import sys,json,hashlib,zipfile
 import numpy as np
 from PIL import Image
 sys.path.insert(0,'/root');from registration_gate import features,decide
 root=Path('/mnt/m3diff/viewpoint_extension_v1');lock=json.loads(Path('/root/selection_locked.json').read_text());recipe=json.loads(Path('/root/composed_locked.json').read_text())
 assert hashlib.sha256(Path('/root/registration_gate.py').read_bytes()).hexdigest()==lock['frozen_registration_source_sha256']
 rows=[]
 for r in lock['selection']:
  scene=r['scene'];source=root/'dataset'/(scene+'_source.png')
  for kind in ['zoom_in_1p10','roll_8_safe','zoom_out_1p10']:
   before=root/'dataset'/(scene+'_zoom_in_1p10.png') if kind=='zoom_out_1p10' else source
   target_source=source if kind=='zoom_out_1p10' else root/'dataset'/(scene+'_'+kind+'.png')
   a=np.array(Image.open(target_source).convert('RGB'));h,w=a.shape[:2];original=a.copy();patch=a[h//2-16:h//2+16,w//2-16:w//2+16]
   delta=-16 if patch.mean()>127 else 16;patch[:]=np.clip(patch.astype(np.int16)+delta,0,255).astype(np.uint8)
   target=root/'dataset'/(scene+'_'+kind+'_edited.png');Image.fromarray(a).save(target)
   n=int(np.any(a!=original,axis=2).sum());assert n>0
   f=features(before,target);d=decide(f,lock['frozen_thresholds']);rows.append({'id':scene+'__'+kind+'_plus_square32_delta16','scene':scene,'split':r['split'],'kind':'composed_primary_stress','condition':kind,'changed_native_pixels':n,'features':f,'decision':d})
   print('COMPOSED',scene,kind,flush=True)
 (root/'composed_audit.json').write_text(json.dumps(rows,indent=2));(root/'composed_locked.json').write_text(json.dumps(recipe,indent=2))
 with zipfile.ZipFile(root/'composed_results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for n in ['composed_audit.json','composed_locked.json']:z.write(root/n,n)
 volume.commit();print('COMPOSED DONE',len(rows),flush=True)

@app.local_entrypoint()
def main(stage:str='gallery'):
 if stage=='gallery':gallery.remote()
 elif stage=='prepare':prepare.remote()
 elif stage=='audit':audit.remote()
 elif stage=='composed':composed.remote()
 else:raise ValueError('Unknown stage')
