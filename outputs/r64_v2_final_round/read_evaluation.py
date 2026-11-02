from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import modal,json
P=Path(__file__).parent/'evaluation';P.mkdir(exist_ok=True);v=modal.Volume.from_name('m3diff')
names=['EVAL_ATTEMPT.json','TIMINGS.json','GATE_RESULT.json','EVALUATION_DONE.json','EVALUATION_ERROR.txt','JOB_TIMING.json','camera_v2.jsonl','synth_v2.jsonl','base.jsonl','v2.jsonl']
def get(n):
    try:
        b=b''.join(v.read_file('r64_v2_final_round/evaluation/'+n));(P/n).write_bytes(b)
        return n,{'captions':len(b.splitlines())} if n.endswith('.jsonl') else json.loads(b) if n.endswith('.json') else b.decode()[-2500:]
    except FileNotFoundError:return n,'not yet'
with ThreadPoolExecutor(max_workers=4) as ex:
    for n,x in ex.map(get,names):print(n,json.dumps(x,ensure_ascii=False),flush=True)
