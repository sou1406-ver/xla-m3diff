"""Read selected image bytes from the existing Volume; creates no Modal app."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,shutil
import modal
H=Path(__file__).parent;cs=json.loads((H/'CASES.json').read_text(encoding='utf-8'));v=modal.Volume.from_name('m3diff');dest=H/'source_images';dest.mkdir(exist_ok=True)
jobs=[]
for c in cs:
 c['local_images']=[]
 for j,name in enumerate(c['source_images']):
  p=dest/(c['id']+f'_{j}'+Path(name).suffix);c['local_images'].append(str(p.resolve()))
  if c['remote_root']:jobs.append((c['remote_root']+'/'+name,p))
  else:shutil.copyfile(Path(c['local_root'])/name,p)
def get(item):
 name,p=item
 if not p.exists():p.write_bytes(b''.join(v.read_file(name)))
 return {'volume_path':name,'local_path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:manifest=list(pool.map(get,jobs))
(H/'IMAGE_SOURCES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(H/'CASES.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2),encoding='utf-8');print('Downloaded',len(manifest),'selected image files; no compute job.')
