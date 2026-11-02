"""One camera-invariance SFT pilot; no held-out images used for training."""
from pathlib import Path
import modal
HERE=Path(__file__).parent;OLD=HERE.parent/'curated_sft';DIAG=HERE.parent/'viewpoint_diagnostic'
app=modal.App('m3diff-invariance-sft-v1');volume=modal.Volume.from_name('m3diff')
cpu_image=(modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0','numpy<2')
 .add_local_file(str(HERE/'protocol.json'),'/root/protocol.json',copy=True)
 .add_local_file(str(OLD/'train_seeded.py'),'/root/train_seeded.py',copy=True))
gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
 .add_local_file(str(DIAG/'deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))
RUN='invariance_sft_v1'

@app.function(image=cpu_image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,random,math,hashlib,copy
 from PIL import Image
 root=Path('/mnt/m3diff');out=root/RUN;out.mkdir(exist_ok=True);aug=out/'negative_images';aug.mkdir(exist_ok=True)
 protocol=json.loads(Path('/root/protocol.json').read_text())
 if (out/'protocol.json').exists():assert json.loads((out/'protocol.json').read_text())==protocol
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));(out/'train_seeded.py').write_bytes(Path('/root/train_seeded.py').read_bytes())
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 old=json.loads((root/'viewpoint_diagnostic_v1/dataset/manifest.json').read_text());new=json.loads((root/'viewpoint_extension_v1/manifest.json').read_text())
 questions=[];meta=[];test_source_paths=set()
 prompt="What's the difference between 2 images?  <image><image>Difference:"
 for cohort,rows,folder in [('old',old,'viewpoint_diagnostic_v1/dataset'),('new',new,'viewpoint_extension_v1/dataset')]:
  for r in rows:
   if cohort=='new' and r['kind'] not in ['nochange','natural_pending_review']:continue
   rid=cohort+'__'+r['id'];images=[folder+'/'+im for im in r['image']]
   assert all((root/im).exists() for im in images)
   questions.append({'id':rid,'image':images,'conversations':[{'from':'human','value':prompt}]})
   meta.append({'id':rid,'cohort':cohort,'scene':r['scene'],'split':r['split'],'condition':r['condition'],'image':images})
   test_source_paths.update(r.get('source_dataset_images',r.get('original_images',[])))
 # The extension source originals are also held out even when not in the chosen natural pair.
 for r in json.loads((root/'viewpoint_extension_v1/selection_locked.json').read_text())['selection']:test_source_paths.add(r['image'])
 assert len(questions)==len({q['id'] for q in questions})==108
 save('eval_questions.json',questions);save('eval_manifest.json',meta)
 manifest=json.loads((root/'curated_sft_v4/review_manifest.json').read_text());ann=json.loads((root/'curated_sft_v4/annotations.json').read_text())
 reviewed=[]
 for r in ann['reviews']:
  if r['status']!='accept':continue
  m=manifest[r['index']];reviewed.append({'id':m['id'],'image':m['image'],'conversations':[{'from':'human','value':m['prompt']},{'from':'gpt','value':r['corrected_caption']}]})
 replay=json.loads((root/'real_sft_pilot_v1/replay_train.json').read_text());assert len(reviewed)==44 and len(replay)==128
 positives=[copy.deepcopy(r) for r in replay+reviewed+random.Random(2026102722).sample(reviewed,20)];assert len(positives)==192
 positive_images={im for r in positives for im in r['image']};base=root/'baseline_cache/OmniDiff'
 assert all('/train/' in im for im in positive_images)
 def decoded_hash(p):
  im=Image.open(p).convert('RGB');h=hashlib.sha256();h.update(str(im.size).encode());h.update(im.tobytes());return h.hexdigest()
 heldout_hashes={decoded_hash(base/p) for p in sorted(test_source_paths)}
 rng=random.Random(2026102722);sources=[]
 for split in ['Real','Render']:
  pool=[p for p in sorted((base/split/'train/images').glob('*')) if p.is_file() and p.suffix.lower() in ['.png','.jpg','.jpeg'] and p.relative_to(base).as_posix() not in positive_images]
  rng.shuffle(pool);take=0
  for p in pool:
   h=decoded_hash(p)
   if h in heldout_hashes or any(r['decoded_sha256']==h for r in sources):continue
   sources.append({'path':p.relative_to(base).as_posix(),'split':split,'decoded_sha256':h});take+=1
   if take==8:break
  assert take==8,(split,take)
 print('SOURCES SELECTED',len(sources),flush=True)
 negatives=[]
 def transformed(im,angle,zoom):
  w,h=im.size;t=math.radians(angle);c,s=math.cos(t),math.sin(t);scale=max(abs(c)+h/w*abs(s),abs(c)+w/h*abs(s))*(1.002 if angle else 1)*zoom
  a,b,d,e=c/scale,-s/scale,s/scale,c/scale
  return im.transform(im.size,Image.Transform.AFFINE,(a,b,w/2-a*w/2-b*h/2,d,e,h/2-d*w/2-e*h/2),resample=Image.Resampling.BICUBIC)
 for i,r in enumerate(sources):
  im=Image.open(base/r['path']).convert('RGB');src=aug/f'{i:02d}_source.png'
  if src.exists():assert decoded_hash(src)==r['decoded_sha256'],'Cached source mismatch'
  else:im.save(src)
  for condition,angle,zoom in [('identity',0,1),('zoom_in_1p10',0,1.1),('roll_8_safe',8,1),('zoom_out_reverse_1p10',0,1.1)]:
   target=aug/f'{i:02d}_{condition}.png'
   if not target.exists():transformed(im,angle,zoom).save(target)
   paths=[src.relative_to(root).as_posix(),target.relative_to(root).as_posix()]
   if condition.startswith('zoom_out'):paths=paths[::-1]
   caption=('There is no visible difference between the two images.' if condition=='identity' else
    'The second image shows a wider view of the same scene. No object changes are visible in the shared area.' if condition.startswith('zoom_out') else
    'Only the camera framing or image orientation changes; no object changes are visible in the shared area.')
   negatives.append({'id':f'negative_{i:02d}_{condition}','image':paths,'conversations':[{'from':'human','value':prompt},{'from':'gpt','value':caption}]})
  print('NEGATIVE SOURCE',i+1,flush=True)
 for r in positives:
  assert all(im.startswith(('Real/train/','Render/train/')) for im in r['image'])
  r['image']=['baseline_cache/OmniDiff/'+im for im in r['image']]
 # Enforce exact decoded-content separation, not merely distinct path strings.
 train_original_paths={p.removeprefix('baseline_cache/OmniDiff/') for r in positives for p in r['image']}|{s['path'] for s in sources}
 collisions=[]
 for i,p in enumerate(sorted(train_original_paths)):
  if decoded_hash(base/p) in heldout_hashes:collisions.append(p)
  if i%64==63:print('AUDITED TRAIN IMAGES',i+1,flush=True)
 assert not collisions,collisions
 train=positives+negatives;assert len(train)==256 and len(negatives)==64
 random.Random(2026102723).shuffle(train);save('train.json',train);save('negative_sources.json',sources)
 save('data_audit.json',{'records':256,'negative_records':64,'positive_records':192,'negative_original_sources':16,'heldout_original_images':len(test_source_paths),'train_original_images':len(train_original_paths),'exact_decoded_hash_collisions':collisions,'all_original_train_paths_official_train':all('/train/' in p for p in train_original_paths),'train_sha256':hashlib.sha256((out/'train.json').read_bytes()).hexdigest(),'eval_questions_sha256':hashlib.sha256((out/'eval_questions.json').read_bytes()).hexdigest(),'limits':'Exact decoded duplicates excluded, not a guarantee of scene independence. Published checkpoint has already seen official train.'})
 save('PREPARED.json',{'n_train':256,'n_eval':108,'training_recipe':protocol['training']});volume.commit();print('PREPARATION DONE',flush=True)

@app.function(image=gpu_image,gpu='A100-40GB',cpu=8,memory=65536,timeout=3600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def experiment():
 import os,json,subprocess,time,sys,random,zipfile,math
 root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo';assert (out/'PREPARED.json').exists();(out/'logs').mkdir(exist_ok=True)
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
  if lora:args+=['--model-base',ckpt]
  args+=['--question-file',out/'eval_questions.json','--answers-file',out/(arm+'.jsonl'),'--image-folder',root,
   '--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention']
  run(args,arm,env)
 evaluate('baseline',ckpt)
 if not (out/'TRAIN_DONE.json').exists():
  args=[py,out/'train_seeded.py','--model_name_or_path',ckpt,'--version','qwen_2','--output_dir',model,
   '--data_path',out/'train.json','--image_folder',root,'--image_aspect_ratio','pad','--vision_tower','google/siglip-so400m-patch14-384',
   '--mm_vision_select_layer','[-11,-8,-5,-2]','--unfreeze_mm_vision_tower','False','--mm_projector_type','mlp2x_gelu','--mm_patch_merge_type','flat',
   '--mm_resampler_type','mdp','--mdp_args','{"num_refinement_layers":2,"feature_dim":1152,"ffn_hidden_dim":4608,"attention_downsample_rate":1}',
   '--tune_mm_vision_resampler','False','--freeze_reasmpler','True','--freeze_mm_mlp_adapter','True','--mm_use_im_start_end','False','--mm_use_im_patch_token','False',
   '--lora_enable','True','--lora_r','16','--lora_alpha','32','--num_train_epochs','1','--per_device_train_batch_size','1','--gradient_accumulation_steps','8',
   '--learning_rate','5e-6','--weight_decay','0','--warmup_ratio','.03','--lr_scheduler_type','cosine','--logging_steps','3','--model_max_length','4096',
   '--gradient_checkpointing','True','--group_by_modality_length','False','--dataloader_num_workers','2','--lazy_preprocess','True','--bf16','True','--tf32','True',
   '--report_to','none','--save_strategy','no','--seed','42']
  run(args,'train',env)
  audit=json.loads((model/'initialization_audit.json').read_text());assert all('lora_' in n for n in audit['trainable_names'])
  state=json.loads((model/'trainer_state.json').read_text());assert state['global_step']==32
  assert all(math.isfinite(r['loss']) for r in state['log_history'] if 'loss' in r)
  run([py,'-c',"import torch,sys; assert not torch.load(sys.argv[1],map_location='cpu')",model/'non_lora_trainables.bin'],'verify_frozen',env)
  save('TRAIN_DONE.json',{'steps':32,'only_lora_trainable':True,'finite_losses':True});volume.commit()
 evaluate('invariance',model,True)
 raw={}
 for arm in ['baseline','invariance']:
  rows=[json.loads(l) for l in (out/(arm+'.jsonl')).read_text().splitlines() if l.strip()]
  assert len(rows)==len({r['id'] for r in rows})==108
  raw[arm]={r['id']:r for r in rows}
  assert set(raw[arm])=={r['id'] for r in json.loads((out/'eval_questions.json').read_text())}
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 meta=json.loads((out/'eval_manifest.json').read_text());rng=random.Random(2026102724);masked=[];key={}
 for r in meta:
  arms=['baseline','invariance'];rng.shuffle(arms);masked.append({**{k:r[k] for k in ['id','cohort','scene','split','condition']},
    'candidate_1':deduplicate_caption(raw[arms[0]][r['id']]['caption'])[0],'candidate_2':deduplicate_caption(raw[arms[1]][r['id']]['caption'])[0]})
  key[r['id']]={f'candidate_{i+1}':a for i,a in enumerate(arms)}
 save('masked_predictions.json',masked);save('mask_key.json',key);save('SUCCESS.json',{'n_eval':108,'generations':216,'gpu':gpu,'completed_at':time.time(),'GPU_released_on_return':True})
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.txt'] and p.stat().st_size<20_000_000:z.write(p,str(p.relative_to(out)))
 volume.commit();print('INVARIANCE PILOT DONE; GPU returning',flush=True)

@app.local_entrypoint()
def main(stage:str='prepare'):
 if stage=='prepare':prepare.remote()
 elif stage=='experiment':experiment.remote()
 else:raise ValueError('Choose prepare or experiment')
