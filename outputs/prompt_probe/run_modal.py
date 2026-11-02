"""One camera-invariance SFT pilot; no held-out images used for training."""
from pathlib import Path
import modal
HERE=Path(__file__).parent;OLD=HERE.parent/'curated_sft';DIAG=HERE.parent/'viewpoint_diagnostic'
app=modal.App('m3diff-ten-prompt-probe-v1');volume=modal.Volume.from_name('m3diff')
gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
 .pip_install_from_requirements(str(HERE.parent/'mixed_full_benchmark/requirements.txt'))
 .add_local_file(str(HERE.parent/'curated_sft/deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True)
 .add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/load_wrapper.py',copy=True))
for name in ['eval_questions.json','eval_manifest.json','protocol.json']:
 gpu_image=gpu_image.add_local_file(str(HERE/name),'/root/probe/'+name,copy=True)
RUN='invariance_prompt_probe_v1'

@app.function(image=gpu_image,gpu='A10',cpu=4,memory=32768,timeout=1200,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def experiment():
 import os,json,subprocess,time,sys,random,zipfile,math
 root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo';out.mkdir(exist_ok=True);
 for p in Path('/root/probe').iterdir():(out/p.name).write_bytes(p.read_bytes())
 (out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())
 (out/'logs').mkdir(exist_ok=True)
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 py=sys.executable
 def run(args,name,env=None):
  print('START',name,flush=True)
  with open(out/'logs'/(name+'.log'),'a') as log:
   p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in p.stdout:
    log.write(line);log.flush()
    if any(t in line for t in ['%|','Error','Traceback','Loading',"'loss'",'train_runtime']):print(line.strip()[-300:],flush=True)
   rc=p.wait()
  volume.commit()
  if rc:raise RuntimeError(f'{name} failed {rc}')
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip();save('gpu.json',{'actual_gpu':gpu,'all_generations_same_container':True});
 import re
 assert re.search(r'\bA10(?:G)?\b',gpu),'Unexpected GPU class; stop before inference'
 (out/'environment_freeze.txt').write_text(subprocess.check_output([py,'-m','pip','freeze'],text=True))
 (out/'repo_commit.txt').write_text(subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True))
 env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo),ATTN='sdpa')
 ckpt=root/'baseline_cache/M3Diff';model=out/'m3diff-invariance-lora'
 def evaluate(arm,path,lora=False):
  args=[py,base/'code/baseline_eval.py','--model-path',path]
  if lora:args=[py,out/'load_wrapper.py','--adapter-mode','unmerged_fp32','--load-audit',out/(arm+'_load_audit.json'),'--model-path',path,'--model-base',ckpt]
  args+=['--question-file',out/'eval_questions.json','--answers-file',out/(arm+'.jsonl'),'--image-folder',root,
   '--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention']
  run(args,arm,env)
 evaluate('baseline',ckpt)
 for arm,path in [('old_mixed',root/'invariance_ablation_v1/m3diff-mixed-objective-lora'),('balanced',root/'invariance_prompt_balanced_v1/m3diff-balanced-lora')]:
  evaluate(arm,path,True)

 raw={}
 for arm in ['baseline','old_mixed','balanced']:
  rows=[json.loads(l) for l in (out/(arm+'.jsonl')).read_text().splitlines() if l.strip()]
  assert len(rows)==len({r['id'] for r in rows})==40
  raw[arm]={r['id']:r for r in rows}
  assert set(raw[arm])=={r['id'] for r in json.loads((out/'eval_questions.json').read_text())}
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 meta=json.loads((out/'eval_manifest.json').read_text());rng=random.Random(2026102806);masked=[];key={}
 for r in meta:
  arms=['baseline','old_mixed','balanced'];rng.shuffle(arms);masked.append({**r,
    **{f'candidate_{i+1}':deduplicate_caption(raw[a][r['id']]['caption'])[0] for i,a in enumerate(arms)}})
  key[r['id']]={f'candidate_{i+1}':a for i,a in enumerate(arms)}
 save('masked_predictions.json',masked);save('mask_key.json',key);save('SUCCESS.json',{'n_eval':40,'generations':120,'gpu':gpu,'completed_at':time.time(),'GPU_released_on_return':True})
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.txt'] and p.stat().st_size<20_000_000:z.write(p,str(p.relative_to(out)))
 volume.commit();print('INVARIANCE PILOT DONE; GPU returning',flush=True)

@app.local_entrypoint()
def main():
 experiment.remote()
