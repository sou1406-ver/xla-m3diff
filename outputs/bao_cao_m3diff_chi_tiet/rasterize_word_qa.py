"""Use packaged DOCX renderer rasterization with a native Word PDF backend."""
from pathlib import Path
import importlib.util,shutil,os,json
HERE=Path(__file__).parent
skill=Path('C:/Users/phuc1/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents')
spec=importlib.util.spec_from_file_location('packaged_docx_renderer',skill/'render_docx.py');renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
poppler=Path('C:/Users/phuc1/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')
os.environ['PATH']=str(poppler)+os.pathsep+os.environ.get('PATH','')
pdf=HERE/'qa_render/BAO_CAO_M3DIFF_CHI_TIET.pdf';assert pdf.is_file() and pdf.stat().st_size>0
def word_pdf_backend(*args,**kwargs):return str(pdf),'Native Word ExportAsFixedFormat; no LibreOffice executable used.'
renderer.convert_to_pdf=word_pdf_backend
pages=renderer.rasterize(str(HERE/'BAO_CAO_M3DIFF_CHI_TIET.docx'),str(HERE/'qa_render'),150,verbose=False,emit_pdf=False)
from PIL import Image,ImageOps,ImageDraw
tiles=[]
for index,p in enumerate(pages,1):
 im=Image.open(p).convert('RGB');im.thumbnail((248,351));tile=Image.new('RGB',(270,385),'#e6e6e6');tile.paste(im,((270-im.width)//2,20));ImageDraw.Draw(tile).text((8,365),f'Page {index}',fill='black');tiles.append(tile)
contacts=[]
for start in range(0,len(tiles),12):
 group=tiles[start:start+12];sheet=Image.new('RGB',(270*4,385*3),'white')
 for j,tile in enumerate(group):sheet.paste(tile,((j%4)*270,(j//4)*385))
 path=HERE/'qa_render'/f'contact_{start//12+1:02d}.jpg';sheet.save(path,quality=90);contacts.append(str(path))
(HERE/'RENDER_MANIFEST.json').write_text(json.dumps({'backend':'Native Microsoft Word PDF plus packaged render_docx.py rasterize','dpi':150,'page_count':len(pages),'pages':pages,'contacts':contacts},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':len(pages),'contacts':contacts},ensure_ascii=False))
