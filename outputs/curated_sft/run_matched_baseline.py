"""Re-evaluate the published checkpoint on the same A100/dtype/prompt setup as SFT."""
from pathlib import Path
import modal
app=modal.App('m3diff-curated-matched-baseline')
volume=modal.Volume.from_name('m3diff')
image=modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')

@app.function(image=image,gpu='A100-40GB',cpu=8,memory=65536,timeout=2400,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def evaluate():
 import os,json,subprocess,time
 root=Path('/mnt/m3diff');out=root/'curated_sft_v4';base=root/'baseline_reproduction_v1';repo=base/'repo'
 assert (out/'prepared.json').exists()
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 py='/root/matched-venv/bin/python';uv='/usr/local/bin/uv'
 def run(args,name,env=None):
  print('START',name,flush=True)
  with open(out/'logs'/(name+'.log'),'a') as log:
   p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in p.stdout:
    log.write(line);log.flush()
    if any(t in line for t in ['%|','Error','Traceback','Loading']):print(line.strip()[-300:],flush=True)
   rc=p.wait()
  volume.commit()
  if rc:raise RuntimeError(f'{name} failed {rc}')
 run([uv,'venv','/root/matched-venv','--python','3.10'],'matched_venv')
 run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0',
      'accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'matched_setup')
 env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo))
 run([py,base/'code/baseline_eval.py','--model-path',root/'baseline_cache/M3Diff',
  '--question-file',out/'eval_questions.json','--answers-file',out/'matched_baseline.jsonl',
  '--image-folder',root/'baseline_cache/OmniDiff','--num-chunks','1','--chunk-idx','0',
  '--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2',
  '--torch-dtype','bfloat16','--no-flash-attention'],'matched_baseline',env)
 rows=[json.loads(l) for l in (out/'matched_baseline.jsonl').read_text().splitlines() if l.strip()]
 assert len(rows)==len({r['id'] for r in rows})==256
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip()
 (out/'MATCHED_BASELINE_SUCCESS.json').write_text(json.dumps({'n':256,'gpu':gpu,'completed_at':time.time(),
  'reason':'Published baseline rerun on same requested A100-40GB type and BF16/greedy settings as SFT; old cached A10 baseline kept as secondary comparison.'},indent=2))
 volume.commit();print('MATCHED BASELINE DONE',gpu,flush=True)

@app.local_entrypoint()
def main():evaluate.remote()
