"""Visually reviewed caption correction versus original labels on identical train pairs."""
from pathlib import Path
import modal

HERE=Path(__file__).parent
app=modal.App('m3diff-curated-caption-sft')
volume=modal.Volume.from_name('m3diff')
cpu_image=(modal.Image.debian_slim(python_version='3.10')
 .add_local_file(str(HERE/'annotations.json'),'/root/annotations.json',copy=True)
 .add_local_file(str(HERE/'train_seeded.py'),'/root/train_seeded.py',copy=True)
 .add_local_file(str(HERE/'review_manifest.json'),'/root/review_manifest.json',copy=True))
gpu_image=modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless').pip_install('uv')
RUN='curated_sft_v4'

@app.function(image=cpu_image,cpu=2,memory=4096,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
 import json,copy,random,hashlib
 root=Path('/mnt/m3diff');out=root/RUN;out.mkdir(exist_ok=True)
 repo=root/'baseline_reproduction_v1/repo';prior=root/'real_sft_pilot_v1'
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 manifest=json.loads(Path('/root/review_manifest.json').read_text());audit=json.loads(Path('/root/annotations.json').read_text())
 (out/'train_seeded.py').write_text(Path('/root/train_seeded.py').read_text())
 accepted=[r for r in audit['reviews'] if r['status']=='accept']
 assert len(audit['reviews'])==48 and len(accepted)==44
 assert {r['index'] for r in audit['reviews']}==set(range(48))
 originals=[];corrected=[]
 for r in accepted:
  item=manifest[r['index']];assert r['corrected_caption'] and r['evidence']
  q={'id':item['id'],'image':item['image'],'conversations':[{'from':'human','value':item['prompt']},
      {'from':'gpt','value':item['original_caption']}]}
  originals.append(q);q=copy.deepcopy(q);q['conversations'][-1]['value']=r['corrected_caption'];corrected.append(q)
 replay=json.loads((prior/'replay_train.json').read_text())
 assert len(replay)==128
 for arm,rows in [('original_labels',originals),('corrected_labels',corrected)]:
  # Exactly the same examples/order and exposure in both arms; only target captions differ.
  train=copy.deepcopy(rows)+copy.deepcopy(rows)+copy.deepcopy(replay)
  random.Random(20261030).shuffle(train);save(arm+'_train.json',train)
  assert len(train)==216
 save('annotations.json',audit);save('review_manifest.json',manifest)
 excluded=set();prior_pairs=set();prior_ids=set()
 paths=[root/'grounded_caption_pilot_v1/selection.json',root/'caption_verifier_validation_v1/selection.json',prior/'eval_questions.json']
 for path in paths:
  for r in json.loads(path.read_text()):
   ims=r.get('images',r.get('image',[]));excluded.update(ims)
   if len(ims)==2:prior_pairs.add(tuple(sorted(ims)))
   if 'id' in r:prior_ids.add(r['id'])
 for r in json.loads((root/'locateanything_demo_v1/results.json').read_text()):excluded.add(r['source_image'])
 used=set();evaluation=[];split_counts={}
 for split in ['Real','Render']:
  qs=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text())
  qs=sorted(qs,key=lambda q:q['id']);random.Random(20261030).shuffle(qs)
  qs.sort(key=lambda q:bool(set(q['image'])&excluded));take=[]
  for q in qs:
   if q['id'] in prior_ids or tuple(sorted(q['image'])) in prior_pairs:continue
   q=copy.deepcopy(q);q['split']=split
   q['all_images_unseen_in_previous_pilots']=not bool(set(q['image'])&excluded)
   take.append(q);used.update(q['image'])
   if len(take)==128:break
  assert len(take)==128,(split,len(take));evaluation+=take;split_counts[split]=len(take)
 train_images={im for r in originals+replay for im in r['image']}
 assert not train_images&used
 assert [(q['id'],q['image']) for q in evaluation]==[(q['id'],q['image']) for q in json.loads((root/'curated_sft_v3/eval_questions.json').read_text())]
 assert all('/train/' in im for im in train_images)
 for im in train_images:assert (root/'baseline_cache/OmniDiff'/im).exists(),im
 save('eval_questions.json',evaluation)
 config={'reviewer':audit['reviewer'],'reviewed_pairs':48,'accepted_unique_pairs':44,'rejected_indices':[r['index'] for r in audit['reviews'] if r['status']!='accept'],
  'unique_replay_pairs':128,'corrected_pair_exposure':2,'train_records_per_arm':216,'steps_per_arm':27,
  'eval_pairs':len(evaluation),'per_split':split_counts,'eval_selection_seed':20261030,'train_order_seed':20261030,'training_seed':42,
  'image_clean_eval_counts':{s:sum(q['split']==s and q['all_images_unseen_in_previous_pilots'] for q in evaluation) for s in split_counts},
  'annotations_sha256':hashlib.sha256(Path('/root/annotations.json').read_bytes()).hexdigest(),
  'initialization_control':'set_seed(42) before model/LoRA creation; initialization hashes saved and compared across arms',
  'sample_order_control':'Length grouping disabled; actual sampled record indices saved and compared across arms',
  'trainer_wrapper_sha256':hashlib.sha256(Path('/root/train_seeded.py').read_bytes()).hexdigest(),
  'training':{'lora_r':16,'lora_alpha':32,'lr':1e-5,'epochs':1,'batch':1,'accum':8,'vision':'frozen','projector':'frozen','MDP':'trainable'},
  'comparison':'Original labels versus visually reviewed corrected labels on identical image pairs, same order/replay/updates. Both start from published base. Previous random-SFT checkpoint evaluated separately.',
  'holdout':'128 new unordered image pairs per domain, excluding all earlier pilot/validation/SFT question IDs and unordered pairs. Prior-unseen images prioritized, but not enough exist in Render: some evaluation images were viewed in earlier pilots. Explicit per-pair freshness flags and image-clean counts saved. Pairs may share images within this batch; use shared-image connected components for clustered uncertainty. Official train paths only for fitting. Not guaranteed scene-disjoint or fully independent of development.',
  'limits':'Review performed by Codex assistant, not independently human adjudicated. Targets describe supported visible changes and may differ in length/wording from originals. Small single-seed study; no claim of general rotation/zoom robustness.'}
 if (out/'prepared.json').exists():assert json.loads((out/'prepared.json').read_text())==config,'Configuration changed; use new run name'
 save('prepared.json',config);volume.commit();print('PREPARED',json.dumps(config),flush=True)

@app.function(image=gpu_image,gpu='A100-40GB',cpu=8,memory=65536,timeout=7200,
 volumes={'/mnt/m3diff':volume},scaledown_window=2)
def experiment(lora_only: bool=False):
 import os,json,subprocess,zipfile,time
 root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo'
 volume.reload();assert (out/'prepared.json').exists();(out/'logs').mkdir(exist_ok=True)
 os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
 py='/root/curated-venv/bin/python';uv='/usr/local/bin/uv'
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 def run(args,name,env=None):
  print('START',name,flush=True)
  with open(out/'logs'/(name+'.log'),'a') as log:
   p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in p.stdout:
    log.write(line);log.flush()
    if any(k in line for k in ["'loss'",'train_runtime','Traceback','Error','%|','Loading','Saving']):print(line.strip()[-400:],flush=True)
   rc=p.wait()
  volume.commit()
  if rc:raise RuntimeError(f'{name} failed {rc}; see persisted log')
 prefix='lora_only_' if lora_only else ''
 run([uv,'venv','/root/curated-venv','--python','3.10'],prefix+'venv')
 run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1',
      'bitsandbytes==0.43.3','setuptools','pycocoevalcap==1.2'],prefix+'setup')
 env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo),ATTN='sdpa')
 ckpt=root/'baseline_cache/M3Diff';images=root/'baseline_cache/OmniDiff'
 def evaluate(arm,model):
  run([py,base/'code/baseline_eval.py','--model-path',model,'--model-base',ckpt,
      '--question-file',out/'eval_questions.json','--answers-file',out/(arm+'.jsonl'),'--image-folder',images,
      '--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024',
      '--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention'],arm,env)
 try:
  wrapper=out/'train_seeded.py'
  if lora_only:
   (out/'corrected_lora_only_train.json').write_text((out/'corrected_labels_train.json').read_text())
   save('lora_only_config.json',{'data':'corrected_labels_train.json, identical order and labels',
    'train_records':216,'steps':27,'lora_r':16,'lora_alpha':32,'lr':1e-5,'epochs':1,'seed':42,
    'vision':'frozen','projector':'frozen','MDP':'frozen','comparison':'Only MDP freezing differs from corrected_labels arm. Planned before reading current evaluation scores.'})
  for arm in (['corrected_lora_only'] if lora_only else ['original_labels','corrected_labels']):
   model=out/f'm3diff-{arm}-lora'
   if not (model/'adapter_config.json').exists():
    args=[py,wrapper,'--model_name_or_path',ckpt,'--version','qwen_2','--output_dir',model,
     '--data_path',out/(arm+'_train.json'),'--image_folder',images,'--image_aspect_ratio','pad',
     '--vision_tower','google/siglip-so400m-patch14-384','--mm_vision_select_layer','[-11,-8,-5,-2]',
     '--unfreeze_mm_vision_tower','False','--mm_projector_type','mlp2x_gelu','--mm_patch_merge_type','flat',
     '--mm_resampler_type','mdp','--mdp_args','{"num_refinement_layers":2,"feature_dim":1152,"ffn_hidden_dim":4608,"attention_downsample_rate":1}',
     '--tune_mm_vision_resampler','True','--freeze_mm_mlp_adapter','True','--mm_use_im_start_end','False',
     '--mm_use_im_patch_token','False','--lora_enable','True','--lora_r','16','--lora_alpha','32',
     '--num_train_epochs','1','--per_device_train_batch_size','1','--gradient_accumulation_steps','8',
     '--learning_rate','1e-5','--weight_decay','0','--warmup_ratio','.03','--lr_scheduler_type','cosine',
     '--logging_steps','3','--model_max_length','4096','--gradient_checkpointing','True',
     '--group_by_modality_length','False','--dataloader_num_workers','2','--lazy_preprocess','True',
     '--bf16','True','--tf32','True','--report_to','none','--save_strategy','no','--seed','42']
    if lora_only:
     args[args.index('--tune_mm_vision_resampler')+1]='False'
     args+=['--freeze_reasmpler','True']
    run(args,'train_'+arm,env)
   if lora_only:
    check="import torch,json,sys; s=torch.load(sys.argv[1],map_location='cpu'); json.dump(list(s),open(sys.argv[2],'w')); assert not s, 'Unexpected non-LoRA trainable weights'"
    run([py,'-c',check,model/'non_lora_trainables.bin',out/'lora_only_non_lora_keys.json'],'check_lora_only_freeze',env)
   evaluate(arm,model)
  if lora_only:
   save('LORA_ONLY_SUCCESS.json',{'completed_at':time.time(),'n_eval':256,'non_lora_trainable_keys':[], 'gpu_released_on_return':True})
   print('LORA ONLY DONE',flush=True)
   return
  evaluate('previous_random',root/'real_sft_pilot_v1/m3diff-random_sft-lora')
  questions=json.loads((out/'eval_questions.json').read_text());metrics={};comparison=[]
  arms=['baseline','previous_random','original_labels','corrected_labels']
  predictions={arm:{r['id']:r for r in map(json.loads,(out/(arm+'.jsonl')).read_text().splitlines())}
               for arm in arms if arm!='baseline'}
  for split in ['Real','Render']:
   qs=[q for q in questions if q['split']==split];ids={q['id'] for q in qs}
   ref=json.loads((repo/f'data/evaluation/reference/OmniDiff_{split}.json').read_text())
   ref['images']=[r for r in ref['images'] if r['id'] in ids]
   ref['annotations']=[r for r in ref['annotations'] if r['image_id'] in ids]
   assert {r['id'] for r in ref['images']}==ids;save(split+'_reference.json',ref);metrics[split]={}
   baseline={r['id']:r for r in map(json.loads,(base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl').read_text().splitlines())}
   for arm in arms:
    rows=[(baseline if arm=='baseline' else predictions[arm])[q['id']] for q in qs]
    name=f'{split}_{arm}.jsonl';(out/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
    scorefile=f'{split}_{arm}_scores.json'
    run([py,base/'code/score_baseline.py','--reference',out/(split+'_reference.json'),
         '--prediction',out/name,'--output',out/scorefile],scorefile,env)
    metrics[split][arm]=json.loads((out/scorefile).read_text())
   for q in qs:
    comparison.append({'id':q['id'],'split':split,'images':q['image'],'baseline':baseline[q['id']]['caption'],
      **{arm:predictions[arm][q['id']]['caption'] for arm in arms if arm!='baseline'},
      'references':[r['caption'] for r in ref['annotations'] if r['image_id']==q['id']]})
  save('metrics.json',metrics);save('comparison.json',comparison)
  save('SUCCESS.json',{'completed_at':time.time(),'n_eval':len(questions),'gpu_released_on_return':True})
  print('DONE',json.dumps(metrics),flush=True)
 finally:
  volume.commit()
  with zipfile.ZipFile(out/('curated_sft_lora_only_results.zip' if lora_only else 'curated_sft_results.zip'),'w',zipfile.ZIP_DEFLATED) as z:
   for p in out.rglob('*'):
    if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py'] and p.stat().st_size<20_000_000:z.write(p,str(p.relative_to(out)))
  volume.commit()

@app.function(image=cpu_image,cpu=1,memory=1024,timeout=8000,scaledown_window=2)
def pipeline():
 prepare.remote()
 experiment.remote()

@app.local_entrypoint()
def main(lora_only: bool=False):
 if lora_only:experiment.remote(lora_only=True)
 else:pipeline.remote()
