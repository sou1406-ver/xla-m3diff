from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import urlopen
from urllib.parse import quote
import json,time,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[1];out=root/'outputs/r64_val_precheck_20261102'
rows=json.loads((out/'selected_rows.json').read_text(encoding='utf-8'));paths=sorted({p for r in rows for p in r['image']})
base='https://huggingface.co/datasets/IVC-liuyuan/OmniDiff/resolve/ed4a84cc51912c73e3d54c8643256d9469657552/'
def get(name):
    target=out/'images'/name;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        for attempt in range(4):
            try:
                data=urlopen(base+quote(name,safe='/'),timeout=45).read();target.write_bytes(data);break
            except Exception:
                if attempt==3:raise
                time.sleep(2*(attempt+1))
    with Image.open(target) as im:
        im=im.convert('RGB');h=hashlib.sha256();h.update(str(im.size).encode());h.update(im.tobytes());rgb=h.hexdigest()
    return {'path':name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'rgb_sha256':rgb}
result=[]
with ThreadPoolExecutor(max_workers=4) as ex:
    futures=[ex.submit(get,n) for n in paths]
    for future in as_completed(futures):
        result.append(future.result())
        if len(result)%25==0:print('DOWNLOADED',len(result),'/',len(paths),flush=True)
(out/'IMAGE_MANIFEST.json').write_text(json.dumps(sorted(result,key=lambda x:x['path']),indent=2),encoding='utf-8')
print('DONE',len(result),sum(r['bytes'] for r in result),flush=True)
