from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff')
files=['SUCCESS.json','timings.json','job_timing.json','base.jsonl','r64.jsonl','manifest.jsonl','questions.json','executed.ipynb']
for arm in ['base','r64']:
    files += [f'{arm}_scores/{name}.csv' for name in ['per_pair','summary_by_level','mention_matrix']]
def get(name):
    b=b''.join(v.read_file('r64_synth_eval_20261102/'+name));p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return name,len(b)
with ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(get,files):print(*r,flush=True)
