from pathlib import Path
import modal
HERE=Path(__file__).parent;DIAG=HERE.parent/'viewpoint_diagnostic'
app=modal.App('m3diff-unmerged-lora-comparison');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
 .add_local_file(str(HERE/'load_wrapper.py'),'/root/load_wrapper.py',copy=True)
 .add_local_file(str(HERE/'comparison_protocol.json'),'/root/comparison_protocol.json',copy=True)
 .add_local_file(str(DIAG/'deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))

@app.function(image=image,gpu='A100-40GB',cpu=8,memory=65536,timeout=900,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def compare():
 import os,json,subprocess,shutil,sys,random,time,zipfile,hashlib
 root=Path('/mnt/m3diff');out=root/'precision_comparison_v1';out.mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
 source=root/'invariance_sft_v1';base=root/'baseline_reproduction_v1';repo=base/'repo';ckpt=root/'baseline_cache/M3Diff';adapter=source/'m3diff-invariance-lora'
 assert (source/'SUCCESS.json').exists()
 shutil.copy2(source/'eval_questions.json',out/'eval_questions.json');shutil.copy2(source/'eval_manifest.json',out/'eval_manifest.json');shutil.copy2('/root/comparison_protocol.json',out/'protocol.json')
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip()
 assert 'A100' in gpu,'Unexpected GPU class; stop rather than exceed planned cost'
 (out/'gpu.json').write_text(json.dumps({'gpu':gpu,'same_container_for_both_modes':True}))
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8')
 py='/root/precision-venv/bin/python';uv='/usr/local/bin/uv'
 def run(cmd,name):
  print('START',name,flush=True)
  with (out/'logs'/(name+'.log')).open('a') as log:
   p=subprocess.Popen(list(map(str,cmd)),cwd=repo,env=dict(os.environ,PYTHONPATH=str(repo),M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in p.stdout:
    log.write(line);log.flush()
    if any(k in line for k in ['%|','Error','Traceback','ADAPTER LOAD','Loading']):print(line.strip()[-320:],flush=True)
   rc=p.wait()
  volume.commit()
  if rc:raise RuntimeError(name+' failed')
 run([uv,'venv','/root/precision-venv','--python','3.10'],'venv')
 run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'setup')
 (out/'environment_freeze.txt').write_text(subprocess.check_output([uv,'pip','freeze','--python',py],text=True))
 raw={}
 for mode in ['merged_bf16','unmerged_fp32']:
  run([py,'/root/load_wrapper.py','--adapter-mode',mode,'--load-audit',out/(mode+'_load_audit.json'),
   '--model-path',adapter,'--model-base',ckpt,'--question-file',out/'eval_questions.json','--answers-file',out/(mode+'.jsonl'),
   '--image-folder',root,'--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention'],mode)
  rows=[json.loads(l) for l in (out/(mode+'.jsonl')).read_text().splitlines() if l.strip()]
  assert len(rows)==len({r['id'] for r in rows})==108;raw[mode]={r['id']:r for r in rows}
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 meta=json.loads((out/'eval_manifest.json').read_text());rng=random.Random(2026102801);masked=[];key={}
 for r in meta:
  modes=['merged_bf16','unmerged_fp32'];rng.shuffle(modes)
  masked.append({**{k:r[k] for k in ['id','cohort','scene','split','condition']},'candidate_1':deduplicate_caption(raw[modes[0]][r['id']]['caption'])[0],'candidate_2':deduplicate_caption(raw[modes[1]][r['id']]['caption'])[0]})
  key[r['id']]={f'candidate_{i+1}':m for i,m in enumerate(modes)}
 for name,obj in [('masked_predictions.json',masked),('mask_key.json',key),('SUCCESS.json',{'n_pairs':108,'n_generations':216,'gpu':gpu,'same_checkpoint':True,'weights_updated':False,'time':time.time()})]:
  (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.log']:z.write(p,str(p.relative_to(out)))
 volume.commit();print('PRECISION COMPARISON DONE; GPU returning',flush=True)

@app.local_entrypoint()
def main():compare.remote()
