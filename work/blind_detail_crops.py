import json,random
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parents[1]/'outputs/curated_sft'
qs=json.loads((root/'eval_questions.json').read_text(encoding='utf8'));rng=random.Random(20261031);selected=[]
for split in ['Real','Render']:
    pool=[q for q in qs if q['split']==split and q['all_images_unseen_in_previous_pilots']]
    rng.shuffle(pool)
    for q in pool[:8]:
        dummy=[0,1,2];rng.shuffle(dummy)
        selected.append({'index':len(selected),'id':q['id'],'split':split,'images':q['image']})
(root/'blind_image_selection.json').write_text(json.dumps(selected,indent=2),encoding='utf8')
regions={0:(0,0,.35,.25),6:(.52,.43,.93,.83),8:(.02,.48,.48,.86),11:(.10,.40,.58,.77),12:(.28,.54,.58,.83)}
for index,box in regions.items():
    sheet=Image.new('RGB',(1600,650),'white');draw=ImageDraw.Draw(sheet)
    for k,rel in enumerate(selected[index]['images']):
        im=Image.open(root/'blind_images/originals'/rel).convert('RGB');w,h=im.size
        im=im.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(box)))
        im=ImageOps.contain(im,(790,610));sheet.paste(im,(k*800,30));draw.text((k*800+5,5),f'AUDIT {index}: '+('BEFORE' if k==0 else 'AFTER'),fill='black')
    sheet.save(root/'blind_images'/f'detail_{index}.jpg',quality=98)
