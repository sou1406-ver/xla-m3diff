from pathlib import Path
import modal
app=modal.App('m3diff-curated-review-preparation')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0')
 .add_local_file(str(Path(__file__).with_name('review_manifest.json')),'/root/review_manifest.json',copy=True))

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,zipfile
 from PIL import Image,ImageDraw,ImageOps
 root=Path('/mnt/m3diff');out=root/'curated_sft_v1';out.mkdir(exist_ok=True)
 rows=json.loads(Path('/root/review_manifest.json').read_text());(out/'review_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(out/'review_images.zip','w',zipfile.ZIP_DEFLATED) as z:
  for start in range(0,len(rows),2):
   sheet=Image.new('RGB',(1800,1300),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for j,r in enumerate(rows[start:start+2]):
    y=j*650;draw.text((10,y+5),f"PAIR {r['index']:02d}  {r['id']}  LEFT=A before / RIGHT=B after",fill='black')
    for k,rel in enumerate(r['image']):
     src=root/'baseline_cache/OmniDiff'/rel
     z.write(src,'originals/'+rel)
     im=ImageOps.contain(Image.open(src).convert('RGB'),(890,610))
     sheet.paste(im,(k*900+(890-im.width)//2,y+32+(610-im.height)//2))
   path=out/f'review_{start//2:02d}.jpg';sheet.save(path,quality=95);z.write(path,path.name)
 volume.commit();print('48 pairs / 24 contact sheets archived. CPU only.')

@app.local_entrypoint()
def main():prepare.remote()
