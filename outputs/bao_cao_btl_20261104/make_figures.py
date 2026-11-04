from pathlib import Path
import json,hashlib
from PIL import Image,ImageOps,ImageDraw,ImageFont
H=Path(__file__).parent;cases=json.loads((H/'CASES.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28)
for c in cases:
 if c['existing_board']:
  im=Image.open(c['existing_board']).convert('RGB');im.save(H/c['figure_file'],quality=95)
 else:
  board=Image.new('RGB',(1440,650),'white');dr=ImageDraw.Draw(board)
  for j,name in enumerate(c['local_images']):
   im=Image.open(name).convert('RGB');im.thumbnail((698,588))
   x=j*720+(720-im.width)//2;y=56+(588-im.height)//2;board.paste(im,(x,y));dr.text((j*720+20,12),'BEFORE' if j==0 else 'AFTER',font=font,fill='#15243a')
  board.save(H/c['figure_file'],quality=95)
 # Store image integrity without redistributing source pixels in Git.
 c['figure_sha256']=hashlib.sha256((H/c['figure_file']).read_bytes()).hexdigest()
tiles=[]
for k,c in enumerate(cases,1):
 im=Image.open(H/c['figure_file']).convert('RGB');im.thumbnail((700,340));tile=Image.new('RGB',(720,390),'#f0f2f4');tile.paste(im,((720-im.width)//2,35));ImageDraw.Draw(tile).text((12,5),f"{k}  {c['id']}",font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20),fill='black');tiles.append(tile)
for offset in [0,4]:
 sheet=Image.new('RGB',(1440,780),'white')
 for j,t in enumerate(tiles[offset:offset+4]):sheet.paste(t,((j%2)*720,(j//2)*390))
 sheet.save(H/f'case_contact_{offset//4+1}.jpg',quality=95)
(H/'CASES.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
print('8 evidence figures prepared.')
