from pathlib import Path
import modal
app=modal.App('m3diff-blind-image-preparation')
volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0')

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,random,zipfile
 from PIL import Image,ImageDraw,ImageOps
 root=Path('/mnt/m3diff');out=root/'curated_sft_v4'
 qs=json.loads((out/'eval_questions.json').read_text());rng=random.Random(20261031);selected=[]
 for split in ['Real','Render']:
  pool=[q for q in qs if q['split']==split and q['all_images_unseen_in_previous_pilots']]
  rng.shuffle(pool)
  for q in pool[:8]:
   dummy=[0,1,2];rng.shuffle(dummy)  # Same RNG consumption as the later 3-way caption masking.
   selected.append({'index':len(selected),'id':q['id'],'split':split,'images':q['image']})
 (out/'blind_image_selection.json').write_text(json.dumps(selected,indent=2))
 with zipfile.ZipFile(out/'blind_audit_images.zip','w',zipfile.ZIP_DEFLATED) as z:
  seen=set()
  for r in selected:
   sheet=Image.new('RGB',(1800,950),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for k,rel in enumerate(r['images']):
    p=root/'baseline_cache/OmniDiff'/rel
    if rel not in seen:z.write(p,'originals/'+rel);seen.add(rel)
    im=ImageOps.contain(Image.open(p).convert('RGB'),(890,900));sheet.paste(im,(k*900+(890-im.width)//2,35+(900-im.height)//2))
    draw.text((k*900+10,8),f"AUDIT {r['index']:02d} "+('BEFORE' if k==0 else 'AFTER'),fill='black')
   p=out/f"blind_{r['index']:02d}.jpg";sheet.save(p,quality=96);z.write(p,p.name)
 volume.commit();print('16 fixed image-clean pairs prepared without showing any model captions or reference labels.')

@app.local_entrypoint()
def main():prepare.remote()
