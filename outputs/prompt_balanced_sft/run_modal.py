"""One camera-invariance SFT pilot; no held-out images used for training."""
from pathlib import Path
import modal
HERE=Path(__file__).parent;OLD=HERE.parent/'curated_sft';DIAG=HERE.parent/'viewpoint_diagnostic'
app=modal.App('m3diff-prompt-balanced-sft-v1');volume=modal.Volume.from_name('m3diff')
gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
 .add_local_file(str(DIAG/'deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))
for name in ['protocol.json','train_weighted.py','train.json','eval_questions.json','eval_manifest.json','data_audit.json']:
 gpu_image=gpu_image.add_local_file(str(HERE/name),'/root/ablation/'+name,copy=True)
gpu_image=gpu_image.add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/ablation/load_wrapper.py',copy=True)
RUN='invariance_prompt_balanced_v1'

@app.function(image=gpu_image,gpu='A100-40GB',cpu=8,memory=65536,timeout=1200,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def experiment():
 import os,json,subprocess,time,sys,random,zipfile,math
 root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo';out.mkdir(exist_ok=True);
 for p in Path('/root/ablation').iterdir():(out/p.name).write_bytes(p.read_bytes())
 (out/'logs').mkdir(exist_ok=True)
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 py='/root/invariance-venv/bin/python';uv='/usr/local/bin/uv'
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
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip();save('gpu.json',{'actual_gpu':gpu,'all_generations_same_container':True})
 run([uv,'venv','/root/invariance-venv','--python','3.10'],'venv')
 run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'setup')
 (out/'environment_freeze.txt').write_text(subprocess.check_output([uv,'pip','freeze','--python',py],text=True))
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
 for arm,weight in [('balanced',1)]:
  model=out/('m3diff-'+arm.replace('_','-')+'-lora')
  train_env=dict(env,M3DIFF_NEGATIVE_WEIGHT=str(weight))
  if not (out/(arm+'_TRAIN_DONE.json')).exists():
   args=[py,out/'train_weighted.py','--model_name_or_path',ckpt,'--version','qwen_2','--output_dir',model,
    '--data_path',out/'train.json','--image_folder',root,'--image_aspect_ratio','pad','--vision_tower','google/siglip-so400m-patch14-384',
    '--mm_vision_select_layer','[-11,-8,-5,-2]','--unfreeze_mm_vision_tower','False','--mm_projector_type','mlp2x_gelu','--mm_patch_merge_type','flat',
    '--mm_resampler_type','mdp','--mdp_args','{"num_refinement_layers":2,"feature_dim":1152,"ffn_hidden_dim":4608,"attention_downsample_rate":1}',
    '--tune_mm_vision_resampler','False','--freeze_reasmpler','True','--freeze_mm_mlp_adapter','True','--mm_use_im_start_end','False','--mm_use_im_patch_token','False',
    '--lora_enable','True','--lora_r','16','--lora_alpha','32','--num_train_epochs','2','--per_device_train_batch_size','1','--gradient_accumulation_steps','8',
    '--learning_rate','2e-5','--weight_decay','0','--warmup_ratio','.03','--lr_scheduler_type','cosine','--logging_steps','3','--model_max_length','4096',
    '--gradient_checkpointing','True','--group_by_modality_length','False','--dataloader_num_workers','2','--lazy_preprocess','True','--bf16','True','--tf32','True',
    '--report_to','none','--save_strategy','no','--seed','42']
   run(args,arm+'_train',train_env)
   audit=json.loads((model/'initialization_audit.json').read_text());assert all('lora_' in n for n in audit['trainable_names'])
   state=json.loads((model/'trainer_state.json').read_text());assert state['global_step']==64
   assert all(math.isfinite(r['loss']) for r in state['log_history'] if 'loss' in r)
   run([py,'-c',"import torch,sys; assert not torch.load(sys.argv[1],map_location='cpu')",model/'non_lora_trainables.bin'],arm+'_verify_frozen',env)
   save(arm+'_TRAIN_DONE.json',{'steps':64,'only_lora_trainable':True,'finite_losses':True});volume.commit()
  evaluate(arm,model,True)
 models=[root/'invariance_ablation_v1/m3diff-mixed-objective-lora',out/'m3diff-balanced-lora']
 audits=[json.loads((p/'initialization_audit.json').read_text()) for p in models]
 for k in ['lora_init_sha256','MDP_init_sha256']:assert audits[0][k]==audits[1][k]
 orders=[json.loads((p/'sample_orders.json').read_text()) for p in models]
 assert len(orders[0])==len(orders[1])==2
 assert all(sorted(order)==list(range(256)) for order in orders[0])
 save('matched_training_audit.json',{'initialization_matches':True,'both_epoch_orders_match':orders[0]==orders[1],'epochs':2,'steps_per_arm':64})

 raw={}
 for arm in ['baseline','balanced']:
  rows=[json.loads(l) for l in (out/(arm+'.jsonl')).read_text().splitlines() if l.strip()]
  assert len(rows)==len({r['id'] for r in rows})==72
  raw[arm]={r['id']:r for r in rows}
  assert set(raw[arm])=={r['id'] for r in json.loads((out/'eval_questions.json').read_text())}
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 meta=json.loads((out/'eval_manifest.json').read_text());rng=random.Random(2026102805);masked=[];key={}
 for r in meta:
  arms=['baseline','balanced'];rng.shuffle(arms);masked.append({**{k:r[k] for k in ['id','cohort','scene','split','condition']},
    **{f'candidate_{i+1}':deduplicate_caption(raw[a][r['id']]['caption'])[0] for i,a in enumerate(arms)}})
  key[r['id']]={f'candidate_{i+1}':a for i,a in enumerate(arms)}
 save('masked_predictions.json',masked);save('mask_key.json',key);save('SUCCESS.json',{'n_eval':72,'generations':144,'gpu':gpu,'completed_at':time.time(),'GPU_released_on_return':True})
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.txt'] and p.stat().st_size<20_000_000:z.write(p,str(p.relative_to(out)))
 volume.commit();print('INVARIANCE PILOT DONE; GPU returning',flush=True)

@app.local_entrypoint()
def main():
 experiment.remote()
