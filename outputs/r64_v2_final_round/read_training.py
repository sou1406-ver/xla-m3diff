from pathlib import Path
import modal,json,concurrent.futures,time
P=Path(__file__).parent;v=modal.Volume.from_name('m3diff')
names=['TRAIN_ATTEMPT.json','TRAIN_INITIALIZATION_AUDIT.json','TRAIN_PROGRESS.json','TRAIN_END.json','TRAIN_DONE.json','TRAIN_ERROR.txt','TRAIN_JOB_TIMING.json']
def read(n):
    try:
        b=b''.join(v.read_file('r64_v2_final_round/'+n));(P/n).write_bytes(b)
        if n=='TRAIN_INITIALIZATION_AUDIT.json':
            j=json.loads(b);return n,{'fresh_lora_B_zero':j['fresh_lora_B_zero'],'total_trainable':j['total_trainable'],'max_steps':j['max_steps'],'base':j['base_model_name_or_path']}
        return n,json.loads(b) if n.endswith('.json') else b.decode()[-1800:]
    except FileNotFoundError:return n,'not yet'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for n,x in ex.map(read,names):print(n,json.dumps(x,ensure_ascii=False),flush=True)
