from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import modal
P=Path(__file__).parent/'evaluation';P.mkdir(exist_ok=True)
v=modal.Volume.from_name('m3diff');prefix='r64_v2_final_round/evaluation/'
assert b''.join(v.read_file(prefix+'JOB_TIMING.json')), 'Wait for evaluation to finish'
files=[x.path for x in v.listdir(prefix,recursive=True) if Path(x.path).suffix in ['.json','.jsonl','.csv','.txt','.ipynb','.png']]
def get(name):
    b=b''.join(v.read_file(name));p=P/name.removeprefix(prefix);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return name,len(b)
with ThreadPoolExecutor(max_workers=4) as ex:
    for n,size in ex.map(get,files):print(n,size,flush=True)
