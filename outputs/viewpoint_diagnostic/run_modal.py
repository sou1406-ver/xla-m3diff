"""One bounded published-model comparison, no persistent deployment."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-viewpoint-diagnostic-v1')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
 .add_local_dir(str(HERE/'dataset'),'/root/diagnostic',copy=True)
 .add_local_file(str(HERE/'protocol_locked.json'),'/root/protocol_locked.json',copy=True)
 .add_local_file(str(HERE.parent/'curated_sft/deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))

@app.function(image=image,gpu='A100-40GB',cpu=8,memory=65536,timeout=3600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def evaluate():
 import os,json,subprocess,shutil,time,hashlib,random,sys,zipfile
 root=Path('/mnt/m3diff');out=root/'viewpoint_diagnostic_v1';out.mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
 lock=json.loads(Path('/root/protocol_locked.json').read_text())
 if (out/'protocol_locked.json').exists():assert json.loads((out/'protocol_locked.json').read_text())==lock
 else:shutil.copy2('/root/protocol_locked.json',out/'protocol_locked.json')
 shutil.copytree('/root/diagnostic',out/'dataset',dirs_exist_ok=True)
 for rel,sha in lock['file_sha256'].items():assert hashlib.sha256((out/'dataset'/rel.replace('\\','/')).read_bytes()).hexdigest()==sha
 base=root/'baseline_reproduction_v1';repo=base/'repo'
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 def run(args,name,env=None):
  print('START',name,flush=True)
  with open(out/'logs'/(name+'.log'),'a') as log:
   p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in p.stdout:
    log.write(line);log.flush()
    if any(t in line for t in ['%|','Error','Traceback','Loading']):print(line.strip()[-260:],flush=True)
   rc=p.wait()
  volume.commit()
  if rc:raise RuntimeError(f'{name} failed {rc}')
 py='/root/diag-venv/bin/python';uv='/usr/local/bin/uv'
 run([uv,'venv','/root/diag-venv','--python','3.10'],'venv')
 run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'setup')
 env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo))
 manifest=json.loads((out/'dataset/manifest.json').read_text());ids={r['id'] for r in manifest};raw={}
 for arm in ['baseline','camera_aware']:
  run([py,base/'code/baseline_eval.py','--model-path',root/'baseline_cache/M3Diff','--question-file',out/'dataset'/f'{arm}_questions.json',
   '--answers-file',out/f'{arm}.jsonl','--image-folder',out/'dataset','--num-chunks','1','--chunk-idx','0','--temperature','0',
   '--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention'],arm,env)
  rows=[json.loads(l) for l in (out/f'{arm}.jsonl').read_text().splitlines() if l.strip()]
  assert len(rows)==len({r['id'] for r in rows})==60 and {r['id'] for r in rows}==ids
  raw[arm]={r['id']:r for r in rows}
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 rng=random.Random(2026102719);masked=[];key={}
 for r in manifest:
  arms=['baseline','camera_aware'];rng.shuffle(arms)
  masked.append({'id':r['id'],'scene':r['scene'],'partition':r['partition'],'split':r['split'],'condition':r['condition'],
    'candidate_1':deduplicate_caption(raw[arms[0]][r['id']]['caption'])[0],
    'candidate_2':deduplicate_caption(raw[arms[1]][r['id']]['caption'])[0]})
  key[r['id']]={f'candidate_{i+1}':a for i,a in enumerate(arms)}
 (out/'masked_predictions.json').write_text(json.dumps(masked,ensure_ascii=False,indent=2))
 (out/'mask_key.json').write_text(json.dumps(key,indent=2))
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip()
 (out/'SUCCESS.json').write_text(json.dumps({'generations':120,'gpu':gpu,'time':time.time(),'checkpoint':'published M3Diff','weights_updated':False},indent=2))
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.log']:z.write(p,str(p.relative_to(out)))
 volume.commit();print('DONE: 120 generations; GPU function returning.',flush=True)

@app.local_entrypoint()
def main():evaluate.remote()
