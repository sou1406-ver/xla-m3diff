"""Budget-bounded resumable full official benchmark, no persistent GPU."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-mixed-full-benchmark-v1');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
 .pip_install_from_requirements(str(HERE/'requirements.txt'))
 .add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/load_wrapper.py',copy=True)
 .add_local_file(str(HERE.parent/'curated_sft/deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True)
 .add_local_file(str(HERE/'protocol.json'),'/root/protocol.json',copy=True))
image=image.add_local_dir(str(HERE.parent/'m3diff_portable/code'),'/root/portable_code',copy=True)
image=image.add_local_file(str(HERE.parent/'caption_cleanup_v2/deduplicate_caption_v2.py'),'/root/deduplicate_caption_v2.py',copy=True)
image=image.add_local_file(str(HERE.parent/'caption_cleanup_v2/protocol.json'),'/root/cleanup_extension_locked.json',copy=True)
RUN='mixed_full_benchmark_v1'
@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=1800,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def evaluate_batch(batch:int,wall_seconds:int):
 import os,json,sys,subprocess,time,hashlib,re,zipfile
 start=time.monotonic();assert 0<=batch<5 and 360<=wall_seconds<=1800
 root=Path('/mnt/m3diff');out=root/RUN;out.mkdir(exist_ok=True);base=root/'baseline_reproduction_v1';repo=base/'repo';model=root/'invariance_ablation_v1/m3diff-mixed-objective-lora'
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 protocol=Path('/root/protocol.json').read_bytes()
 if (out/'protocol.json').exists():assert (out/'protocol.json').read_bytes()==protocol
 else:(out/'protocol.json').write_bytes(protocol)
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip();assert re.search(r'\bA10(?:G)?\b',gpu),gpu
 qs=[];meta=[]
 for split,n in [('Real',803),('Render',767)]:
  part=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text());assert len(part)==n
  qs+=part;meta += [{'id':q['id'],'split':split} for q in part]
 assert len(qs)==len({q['id'] for q in qs})==1570
 save('all_questions.json',qs);save('all_manifest.json',meta)
 chosen=qs[batch*320:(batch+1)*320];name=f'batch_{batch:02d}';qfile=out/(name+'_questions.json');save(qfile.name,chosen);pred=out/(name+'.jsonl');ids={q['id'] for q in chosen}
 previous_status=out/(name+'_status.json')
 if previous_status.exists():
  previous=json.loads(previous_status.read_text())
  if not previous['complete']:save(name+'_prior_attempt_'+str(time.time_ns())+'.json',previous)
 sha=hashlib.sha256((model/'adapter_model.bin').read_bytes()).hexdigest()
 if (out/'adapter_sha256.json').exists():assert json.loads((out/'adapter_sha256.json').read_text())['sha256']==sha
 else:save('adapter_sha256.json',{'sha256':sha,'path':str(model)})
 (out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())
 (out/(name+'_environment.txt')).write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
 env=dict(os.environ,HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo))
 portable_passed=(out/'portable_smoke_audit.json').exists() and json.loads((out/'portable_smoke_audit.json').read_text()).get('exact_caption_matches_reference_loader')==2
 if batch in [1,3] and not portable_passed:
  probe=root/'invariance_prompt_probe_v1';pq=json.loads((probe/'eval_questions.json').read_text());pm={r['id']:r for r in json.loads((probe/'eval_manifest.json').read_text())}
  chosen_smoke=[q for q in pq if q['conversations'][0]['value'].startswith("What's the difference between 2 images?") and pm[q['id']]['source_case_id'] in ['new__clothesline__zoom_in_1p10','new__bunk_bedroom__zoom_out_reverse_1p10']];assert len(chosen_smoke)==2
  save('portable_smoke_questions.json',chosen_smoke)
  cmd=[sys.executable,'/root/portable_code/run_caption.py','--model-path',model,'--model-base',root/'baseline_cache/M3Diff','--question-file',out/'portable_smoke_questions.json','--answers-file',out/'portable_smoke.jsonl','--image-folder',root,'--load-audit',out/'portable_smoke_load_audit.json']
  try:
   with (out/'portable_smoke.log').open('w') as log:subprocess.run(list(map(str,cmd)),env=env,cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
  finally:volume.commit()
  got=[json.loads(l) for l in (out/'portable_smoke.jsonl').read_text().splitlines() if l.strip()];prior={r['id']:r for r in [json.loads(l) for l in (probe/'old_mixed.jsonl').read_text().splitlines() if l.strip()]}
  matches=sum(r['caption']==prior[r['id']]['caption'] for r in got);save('portable_smoke_audit.json',{'n':len(got),'exact_caption_matches_reference_loader':matches,'portable_loader_has_no_Modal_dependency':True,'adapter_sha256':sha});volume.commit();assert len(got)==matches==2,'Portable inference differs; inspect smoke artifacts before proceeding'
 args=[sys.executable,out/'load_wrapper.py','--adapter-mode','unmerged_fp32','--load-audit',out/(name+'_load_audit.json'),'--model-path',model,'--model-base',root/'baseline_cache/M3Diff',
  '--question-file',qfile,'--answers-file',pred,'--image-folder',root/'baseline_cache/OmniDiff','--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention']
 stopped=False;last=0
 with (out/(name+'.log')).open('a') as log:
  process=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
  while process.poll() is None:
   elapsed=time.monotonic()-start
   if elapsed>wall_seconds-100:
    stopped=True;process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
    break
   if elapsed-last>20:
    last=elapsed
    tail=(out/(name+'.log')).read_text(errors='replace')[-300:]
    print(name,f'{elapsed:.0f}s',tail.strip(),flush=True)
   time.sleep(1)
 rows=[]
 if pred.exists():
  lines=pred.read_text().splitlines()
  for i,line in enumerate(lines):
   if not line.strip():continue
   try:r=json.loads(line)
   except json.JSONDecodeError:
    assert i==len(lines)-1;continue
   assert r['id'] in ids and r['image_id']==r['id'] and r['caption'].strip();rows.append(r)
  assert len(rows)==len({r['id'] for r in rows})
  pred.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 status={'batch':batch,'n_expected':len(chosen),'n_completed':len(rows),'complete':len(rows)==len(chosen),'soft_stopped':stopped,'exit_code':process.returncode,'actual_gpu':gpu,'adapter_sha256':sha,'elapsed_seconds':time.monotonic()-start,'hard_timeout_seconds':wall_seconds}
 save(name+'_status.json',status)
 with zipfile.ZipFile(out/(name+'_results.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for p in out.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.txt','.py']:z.write(p,p.name)
 volume.commit();print(json.dumps(status),flush=True)
 if process.returncode and not stopped:raise RuntimeError('Evaluation process failed; partial results/log preserved')
@app.function(image=image,cpu=4,memory=8192,timeout=900,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def score():
 import json,sys,subprocess,zipfile,csv,time,hashlib
 root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo';sys.path.insert(0,'/root')
 from deduplicate_caption import deduplicate_caption
 from deduplicate_caption_v2 import deduplicate_caption as deduplicate_v2
 (out/'cleanup_extension_locked.json').write_bytes(Path('/root/cleanup_extension_locked.json').read_bytes())
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 questions=json.loads((out/'all_questions.json').read_text());manifest=json.loads((out/'all_manifest.json').read_text());rows=[]
 for i in range(5):
  path=out/f'batch_{i:02d}.jsonl'
  if path.exists():rows += [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
 assert len(rows)==len({r['id'] for r in rows}),'Duplicate candidate IDs across batches'
 expected={q['id'] for q in questions};found={r['id'] for r in rows};assert found<=expected
 complete=found==expected;records={r['id']:r for r in rows};summary=[]
 save('completion_audit.json',{'n_expected':1570,'n_completed':len(found),'full_test_complete':complete,'missing_ids':sorted(expected-found)})
 assert found,'No candidate predictions to score'
 metric_cache={}
 for split in ['Real','Render']:
  ids=[r['id'] for r in manifest if r['split']==split and r['id'] in found]
  if not ids:continue
  original=json.loads((repo/f'data/evaluation/reference/OmniDiff_{split}.json').read_text())
  reference={**original,'images':[r for r in original['images'] if r['id'] in set(ids)],'annotations':[r for r in original['annotations'] if r['image_id'] in set(ids)]}
  save(split+'_reference.json',reference)
  bpath=base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl';baseline={r['id']:r for r in [json.loads(l) for l in bpath.read_text().splitlines() if l.strip()]}
  for arm in ['baseline','mixed_objective']:
   source=baseline if arm=='baseline' else records
   for processing in ['raw','dedup','dedup_joined_v2']:
    prefix=split+'_'+arm+'_'+processing;items=[];changed=0
    for rid in ids:
     r=dict(source[rid]);assert r['image_id']==rid
     if processing!='raw':
      fn=deduplicate_caption if processing=='dedup' else deduplicate_v2
      caption=fn(r['caption'])[0];changed+=int(caption!=r['caption']);r['caption']=caption
     items.append(r)
    (out/(prefix+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items))
    args=[sys.executable,base/'code/score_baseline.py','--reference',out/(split+'_reference.json'),'--prediction',out/(prefix+'.jsonl'),'--output',out/(prefix+'_scores.json')]
    payload=hashlib.sha256(json.dumps([(r['id'],r['caption']) for r in items],ensure_ascii=False).encode()).hexdigest();cache_key=(split,payload);reuse=None
    if cache_key in metric_cache:
     reuse,scores=metric_cache[cache_key];save(prefix+'_scores.json',scores)
    else:
     with (out/(prefix+'_metrics.log')).open('w') as log:subprocess.run(list(map(str,args)),cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
     scores=json.loads((out/(prefix+'_scores.json')).read_text());metric_cache[cache_key]=(prefix,scores)
    summary.append({'split':split,'arm':arm,'processing':processing,'n':len(ids),'captions_changed_by_cleanup':changed,'identical_prediction_metric_reuse_from':reuse,**{k:v*100 for k,v in scores.items()}})
    volume.commit();print(prefix,summary[-1],flush=True)
 save('summary_x100.json',summary)
 with (out/'summary_x100.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
 save('SCORED.json',{'full_test_complete':complete,'n_total':len(found),'same_ids_and_cleanup_for_both_arms':True,'time':time.time()})
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.txt','.py','.csv']:z.write(p,p.name)
 volume.commit();print('SCORING DONE; CPU returning',flush=True)
@app.local_entrypoint()
def main(batch:int=0,wall_seconds:int=1800,stage:str='evaluate'):
 assert 360<=wall_seconds<=1800
 if stage=='evaluate':evaluate_batch.with_options(timeout=wall_seconds).remote(batch,wall_seconds)
 elif stage=='score':score.remote()
 else:raise ValueError('stage must be evaluate or score')
