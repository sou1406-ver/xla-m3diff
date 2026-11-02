"""Freeze fresh image selection and previews on CPU before model outputs."""
from pathlib import Path
import modal
app=modal.App('m3diff-fresh-confirmation-prepare');volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0')
@app.function(image=image,cpu=4,memory=8192,timeout=900,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,random,hashlib,math,zipfile
 from PIL import Image,ImageDraw
 root=Path('/mnt/m3diff');out=root/'invariance_confirmation_v1';out.mkdir(exist_ok=True);(out/'images').mkdir(exist_ok=True);(out/'boards').mkdir(exist_ok=True)
 repo=root/'baseline_reproduction_v1/repo';cache=root/'baseline_cache/OmniDiff'
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 def dh(p):
  im=Image.open(p).convert('RGB');h=hashlib.sha256();h.update(str(im.size).encode());h.update(im.tobytes());return h.hexdigest()
 previous=json.loads((root/'invariance_sft_v1/train.json').read_text())+json.loads((root/'invariance_sft_v1/eval_questions.json').read_text())
 excluded_paths={str(root/p) for r in previous for p in r['image']};excluded=set()
 gallery=json.loads((root/'curated_sft_v4/blind_image_selection.json').read_text())
 excluded_paths.update(str(cache/p) for r in gallery for p in r['images'])
 for i,p in enumerate(sorted(excluded_paths)):
  excluded.add(dh(p))
  if i%64==63:print('HASHED PRIOR INPUTS',i+1,flush=True)
 selected=[];used=set();rng=random.Random(2026102802)
 for split in ['Real','Render']:
  pool=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text());rng.shuffle(pool);count=0
  for q in pool:
   assert len(q['image'])==2 and all('/test/' in p for p in q['image'])
   hashes=[dh(cache/p) for p in q['image']]
   if any(h in excluded or h in used for h in hashes) or hashes[0]==hashes[1]:continue
   selected.append({'scene':f'fresh_{split}_{count:02d}','split':split,'original_id':q['id'],'image':['baseline_cache/OmniDiff/'+p for p in q['image']],'decoded_sha256':hashes});used.update(hashes);count+=1
   if count==8:break
  assert count==8
 assert len(selected)==16
 # Selection is committed before any new caption is generated or consulted.
 save('selection_locked.json',{'seed':2026102802,'selected':selected,'n_excluded_decoded_hashes':len(excluded),'exact_hash_collision_count':0,'limits':'Different RGB does not guarantee different semantic scene. Same dataset, not outside-domain validation.'});volume.commit()
 def transformed(im,angle,zoom):
  w,h=im.size;t=math.radians(angle);c,s=math.cos(t),math.sin(t);scale=max(abs(c)+h/w*abs(s),abs(c)+w/h*abs(s))*(1.002 if angle else 1)*zoom
  a,b,d,e=c/scale,-s/scale,s/scale,c/scale
  return im.transform(im.size,Image.Transform.AFFINE,(a,b,w/2-a*w/2-b*h/2,d,e,h/2-d*w/2-e*h/2),resample=Image.Resampling.BICUBIC)
 questions=[];meta=[];prompt="What's the difference between 2 images?  <image><image>Difference:"
 for row in selected:
  src=Image.open(root/row['image'][0]).convert('RGB');paths={}
  for name,angle,zoom in [('zoom_in_1p10',0,1.1),('roll_8_safe',8,1)]:
   target=out/'images'/(row['scene']+'_'+name+'.png');transformed(src,angle,zoom).save(target);paths[name]=target.relative_to(root).as_posix()
  a,b=row['image'];pairs=[('identity',[a,a]),('zoom_in_1p10',[a,paths['zoom_in_1p10']]),('roll_8_safe',[a,paths['roll_8_safe']]),('zoom_out_reverse_1p10',[paths['zoom_in_1p10'],a]),('natural',[a,b])]
  for cond,ims in pairs:
   rid=row['scene']+'__'+cond;questions.append({'id':rid,'image':ims,'conversations':[{'from':'human','value':prompt}]});meta.append({'id':rid,'cohort':'fresh','scene':row['scene'],'split':row['split'],'condition':cond,'image':ims})
  board=Image.new('RGB',(1700,720),'white');d=ImageDraw.Draw(board)
  for i,p in enumerate(row['image']):
   im=Image.open(root/p).convert('RGB');im.thumbnail((840,660));board.paste(im,(i*850+(840-im.width)//2,40+(660-im.height)//2));d.text((i*850+10,10),row['scene']+(' BEFORE' if i==0 else ' AFTER'),fill='black')
  board.save(out/'boards'/(row['scene']+'.jpg'),quality=93);print('PREPARED SCENE',row['scene'],flush=True)
 save('eval_questions.json',questions);save('eval_manifest.json',meta);save('PREPARED.json',{'n_scenes':16,'n_pairs':80,'no_model_outputs_consulted':True})
 with zipfile.ZipFile(out/'preparation.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and (p.suffix=='.json' or p.parent.name=='boards'):z.write(p,str(p.relative_to(out)))
 volume.commit();print('FRESH PREPARATION DONE',flush=True)
@app.local_entrypoint()
def main():prepare.remote()
