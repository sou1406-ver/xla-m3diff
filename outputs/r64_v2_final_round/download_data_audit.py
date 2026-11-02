from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff')
files=['DATA_AUDIT.json','DATA_REVIEW_SELECTION.json','PREPARATION_TIMING.json','TRAIN_SOURCE_RGB_HASHES.json','data/train.json','data/synthetic_manifest.jsonl','data/replay_manifest.json']+[f'data_review_{i:02d}.jpg' for i in range(8)]
def get(name):
    b=b''.join(v.read_file('r64_v2_final_round/'+name));p=HERE/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b);return name,len(b)
with ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(get,files):print(*r,flush=True)
