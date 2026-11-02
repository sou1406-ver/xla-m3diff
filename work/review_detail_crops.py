import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parents[1]/'outputs/curated_sft'
rows=json.loads((root/'review_manifest.json').read_text(encoding='utf8'))
regions={25:(.25,.52,.65,.87),26:(.32,.28,.65,.64),28:(.35,.32,.72,.65),33:(.52,.47,.92,.82),35:(.25,.03,.85,.41),37:(.22,.42,.67,.70),38:(0,.53,.28,.82)}
for index,box in regions.items():
 sheet=Image.new('RGB',(1600,650),'white');draw=ImageDraw.Draw(sheet)
 for k,rel in enumerate(rows[index]['image']):
  im=Image.open(root/'images/originals'/rel).convert('RGB');w,h=im.size
  crop=im.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(box)))
  crop=ImageOps.contain(crop,(790,610));sheet.paste(crop,(k*800,30));draw.text((k*800+5,5),f'{index}: '+('A before' if k==0 else 'B after'),fill='black')
 sheet.save(root/'images'/f'detail_{index}.jpg',quality=98)
