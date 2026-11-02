from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff')
names=['SUCCESS.json','timings.json','job_timing.json','runtime.json','base.jsonl','r64.jsonl','base.jsonl.generation_audit.json','r64.jsonl.generation_audit.json','metrics.json','per_pair_cider.json','executed.ipynb']
def get(name):
    b=b''.join(v.read_file('r64_val_precheck_20261102/'+name));(HERE/name).write_bytes(b);return name,len(b)
with ThreadPoolExecutor(max_workers=4) as ex:
    for x in ex.map(get,names):print(*x,flush=True)
