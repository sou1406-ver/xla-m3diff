"""Small controlled real-data SFT: baseline / old FT / random SFT / hard-mined SFT.
Run: modal run --detach run_real_sft_modal.py
All functions have bounded timeouts and release their GPU on return.
"""
from pathlib import Path
import modal

app=modal.App('m3diff-real-sft-pilot')
volume=modal.Volume.from_name('m3diff')
cpu_image=modal.Image.debian_slim(python_version='3.10').pip_install('huggingface_hub==0.30.2')
gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
           .pip_install('uv'))
RUN='real_sft_pilot_v1'

@app.function(image=cpu_image,cpu=4,memory=8192,timeout=1800,
              volumes={'/mnt/m3diff':volume},scaledown_window=2)
def prepare():
    import os,json,random,copy,hashlib,concurrent.futures
    from huggingface_hub import hf_hub_download
    root=Path('/mnt/m3diff');out=root/RUN;out.mkdir(exist_ok=True)
    repo=root/'baseline_reproduction_v1/repo'
    def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
    if (out/'prepared.json').exists():return json.loads((out/'prepared.json').read_text())
    rows=json.loads((root/'ft/orig/omnidiff_only.json').read_text())
    # IDs are scene labels in some training annotations and may repeat; use pair hashes.
    unique={}
    for r in rows:
        ims=[im.removeprefix('OmniDiff/') for im in r['image']]
        if not all('/train/' in im for im in ims):continue
        key=hashlib.sha256('\n'.join(ims).encode()).hexdigest()[:20]
        item=copy.deepcopy(r);item['id']='train_'+key;item['image']=ims
        if not any(c['from']=='gpt' and c['value'].strip() for c in item['conversations']):continue
        unique.setdefault(key,item)
    pool=sorted(unique.values(),key=lambda r:r['id']);random.Random(20261029).shuffle(pool)
    # No reused image between mining candidates and replay; caps balanced by split.
    groups={'mine':[],'replay':[]};used=set()
    for name,n in [('mine',128),('replay',64)]:
        for split in ['Real','Render']:
            selected=[]
            for r in pool:
                if not r['image'][0].startswith(split+'/') or set(r['image'])&used:continue
                selected.append(r);used.update(r['image'])
                if len(selected)==n:break
            if len(selected)!=n:raise RuntimeError('Insufficient disjoint train pairs')
            groups[name]+=selected
    # Freeze a fresh small test slice before mining or viewing scores.
    excluded=set()
    for path in [root/'grounded_caption_pilot_v1/selection.json',root/'caption_verifier_validation_v1/selection.json']:
        for r in json.loads(path.read_text()):excluded.update(r.get('images',r.get('image',[])))
    evaluation=[];test_used=set()
    for split in ['Real','Render']:
        qs=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text())
        random.Random(20261029).shuffle(qs);take=[]
        for q in qs:
            if set(q['image'])&(excluded|test_used):continue
            q=copy.deepcopy(q);q['split']=split;take.append(q);test_used.update(q['image'])
            if len(take)==32:break
        assert len(take)==32
        evaluation+=take
    assert not used&test_used
    save('mining_train.json',groups['mine']);save('replay_train.json',groups['replay'])
    save('eval_questions.json',evaluation)
    q=[];refs={'images':[],'annotations':[]}
    for i,r in enumerate(groups['mine']):
        q.append({**r,'conversations':[c for c in r['conversations'] if c['from']=='human']})
        refs['images'].append({'id':r['id']})
        caps=[c['value'] for c in r['conversations'] if c['from']=='gpt']
        refs['annotations'].append({'id':i,'image_id':r['id'],'caption':caps[0]})
    save('mine_questions.json',q);save('mine_reference.json',refs)
    os.environ['HF_HUB_DISABLE_XET']='1'
    files=sorted(used)
    revision='ed4a84cc51912c73e3d54c8643256d9469657552'
    def download(rel):
        for attempt in range(4):
            try:
                return hf_hub_download('IVC-liuyuan/OmniDiff',rel,repo_type='dataset',revision=revision,
                    local_dir=str(root/'baseline_cache/OmniDiff'))
            except Exception:
                if attempt==3:raise
                import time;time.sleep(5*(attempt+1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for i,_ in enumerate(executor.map(download,files)):
            if (i+1)%50==0:print('TRAIN IMAGES',i+1,'/',len(files),flush=True)
    config={'seed':20261029,'mining_candidates':256,'replay_pairs':128,'train_pairs_per_arm':256,
      'evaluation_pairs':64,'dataset_revision':revision,'selection':'Official train paths only; image-disjoint mining/replay/test; not guaranteed scene-disjoint. Hard mining uses train reference CIDEr only, not test.',
      'training':{'epochs':1,'lr':1e-5,'lora_r':16,'lora_alpha':32,'batch':1,'accum':8,
                  'vision':'frozen','MDP':'trainable','projector':'frozen'},
      'limits':'Small exploratory test slice. Automatic low-CIDEr mining is a proxy for errors, not human verified semantic error labels. No augmentation or LocateAnything.'}
    save('prepared.json',config);volume.commit();print('PREPARED',config,flush=True)
    return config

@app.function(image=gpu_image,gpu='A100-40GB',cpu=8,memory=65536,timeout=5400,
              volumes={'/mnt/m3diff':volume},scaledown_window=2)
def experiment():
    import os,json,subprocess,random,copy,zipfile,time
    root=Path('/mnt/m3diff');out=root/RUN;base=root/'baseline_reproduction_v1';repo=base/'repo'
    volume.reload();assert (out/'prepared.json').exists()
    (out/'logs').mkdir(exist_ok=True)
    os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
    py='/root/sft-venv/bin/python';uv='/usr/local/bin/uv'
    def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
    def run(args,name,env=None):
        print('START',name,flush=True)
        with open(out/'logs'/f'{name}.log','a') as log:
            proc=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                log.write(line);log.flush()
                if any(s in line for s in ["'loss'",'train_runtime','Traceback','Error','%|','Loading','Saving','merged','PAIR']):
                    print(line.strip()[-400:],flush=True)
            code=proc.wait()
        volume.commit()
        if code:raise RuntimeError(f'{name} failed ({code}), see persisted log')
    run([uv,'venv','/root/sft-venv','--python','3.10'],'venv')
    run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0',
         'accelerate==0.29.1','bitsandbytes==0.43.3','setuptools','pycocoevalcap==1.2'],'setup')
    env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo),ATTN='sdpa')
    ckpt=root/'baseline_cache/M3Diff';imgroot=root/'baseline_cache/OmniDiff'
    def evaluate(qfile,answers,model,base_model=None):
        args=[py,base/'code/baseline_eval.py','--model-path',model,'--question-file',out/qfile,
          '--answers-file',out/answers,'--image-folder',imgroot,'--num-chunks','1','--chunk-idx','0',
          '--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2',
          '--torch-dtype','bfloat16','--no-flash-attention']
        if base_model:args+=['--model-base',base_model]
        run(args,answers.replace('.jsonl',''),env)
    def score(ref,pred,target):
        run([py,base/'code/score_baseline.py','--reference',out/ref,'--prediction',out/pred,'--output',out/target],target,env)
        return json.loads((out/target).read_text())
    try:
        evaluate('eval_questions.json','old_ft.jsonl',root/'ft/m3diff-ft-lora',ckpt)
        evaluate('mine_questions.json','mine_baseline.jsonl',ckpt)
        mining=score('mine_reference.json','mine_baseline.jsonl','mining_scores.json')
        print('MINING SCORE KEYS',list(mining),flush=True)
        # COCO score script persists per-image metric records; derive CIDEr directly if needed.
        mining_code="""
import json,sys
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
r=json.load(open(sys.argv[1]));p=[json.loads(l) for l in open(sys.argv[2]) if l.strip()]
g={x['id']:[] for x in r['images']}
for x in r['annotations']:g[x['image_id']].append({'caption':x['caption']})
h={x['id']:[{'caption':x['caption']}] for x in p}
t=PTBTokenizer();g=t.tokenize(g);h=t.tokenize(h)
_,scores=Cider().compute_score(g,h)
json.dump(dict(zip(g,map(float,scores))),open(sys.argv[3],'w'))
"""
        (out/'mine_scores.py').write_text(mining_code)
        run([py,out/'mine_scores.py',out/'mine_reference.json',out/'mine_baseline.jsonl',out/'mining_cider.json'],'mine_rank',env)
        values=json.loads((out/'mining_cider.json').read_text())
        candidates=json.loads((out/'mining_train.json').read_text());replay=json.loads((out/'replay_train.json').read_text())
        hard=[];control=[]
        for split in ['Real','Render']:
            rs=[r for r in candidates if r['image'][0].startswith(split+'/')]
            hard+=sorted(rs,key=lambda r:(values[r['id']],r['id']))[:64]
            control+=random.Random(20261029).sample(rs,64)
        save('mining_ranking.json',[{'id':r['id'],'cider':values[r['id']],'images':r['image']} for r in candidates])
        arms={'random_sft':control+copy.deepcopy(replay),'hard_sft':hard+copy.deepcopy(replay)}
        # Wrapper preserves original single-GPU training behavior and removes ZeRO dependency.
        wrapper=(root/'ft/code/ft_train.py').read_text()
        (out/'ft_train.py').write_text(wrapper)
        for arm,rows in arms.items():
            random.Random(20261029).shuffle(rows);save(arm+'_train.json',rows)
            model=out/f'm3diff-{arm}-lora'
            if not (model/'adapter_config.json').exists():
                args=[py,out/'ft_train.py','--model_name_or_path',ckpt,'--version','qwen_2','--output_dir',model,
                  '--data_path',out/(arm+'_train.json'),'--image_folder',imgroot,'--image_aspect_ratio','pad',
                  '--vision_tower','google/siglip-so400m-patch14-384','--mm_vision_select_layer','[-11,-8,-5,-2]',
                  '--unfreeze_mm_vision_tower','False','--mm_projector_type','mlp2x_gelu','--mm_patch_merge_type','flat',
                  '--mm_resampler_type','mdp','--mdp_args','{"num_refinement_layers":2,"feature_dim":1152,"ffn_hidden_dim":4608,"attention_downsample_rate":1}',
                  '--tune_mm_vision_resampler','True','--freeze_mm_mlp_adapter','True',
                  '--mm_use_im_start_end','False','--mm_use_im_patch_token','False','--lora_enable','True',
                  '--lora_r','16','--lora_alpha','32','--num_train_epochs','1','--per_device_train_batch_size','1',
                  '--gradient_accumulation_steps','8','--learning_rate','1e-5','--weight_decay','0',
                  '--warmup_ratio','.03','--lr_scheduler_type','cosine','--logging_steps','4',
                  '--model_max_length','4096','--gradient_checkpointing','True','--group_by_modality_length','True',
                  '--dataloader_num_workers','2','--lazy_preprocess','True','--bf16','True','--tf32','True',
                  '--report_to','none','--save_strategy','no','--seed','42']
                run(args,'train_'+arm,env)
            evaluate('eval_questions.json',arm+'.jsonl',model,ckpt)
        metrics={};comparison=[];questions=json.loads((out/'eval_questions.json').read_text())
        pred={arm:{r['id']:r for r in [json.loads(l) for l in (out/(arm+'.jsonl')).read_text().splitlines() if l.strip()]}
              for arm in ['old_ft','random_sft','hard_sft']}
        for split in ['Real','Render']:
            qs=[r for r in questions if r['split']==split];ids={r['id'] for r in qs}
            refs=json.loads((repo/f'data/evaluation/reference/OmniDiff_{split}.json').read_text())
            refs['images']=[r for r in refs['images'] if r['id'] in ids]
            refs['annotations']=[r for r in refs['annotations'] if r['image_id'] in ids]
            save(split+'_reference.json',refs);metrics[split]={}
            basepred={r['id']:r for r in [json.loads(l) for l in (base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl').read_text().splitlines()]}
            for arm in ['baseline','old_ft','random_sft','hard_sft']:
                rows=[basepred[r['id']] if arm=='baseline' else pred[arm][r['id']] for r in qs]
                name=f'{split}_{arm}.jsonl';(out/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
                metrics[split][arm]=score(split+'_reference.json',name,f'{split}_{arm}_scores.json')
            for q in qs:
                comparison.append({'id':q['id'],'split':split,'images':q['image'],'baseline':basepred[q['id']]['caption'],
                    **{arm:pred[arm][q['id']]['caption'] for arm in pred},
                    'references':[r['caption'] for r in refs['annotations'] if r['image_id']==q['id']]})
        save('metrics.json',metrics);save('comparison.json',comparison)
        save('SUCCESS.json',{'completed_at':time.time(),'n_eval':64,'gpu_released_on_return':True})
        print('ALL DONE',json.dumps(metrics),flush=True)
    finally:
        volume.commit()
        with zipfile.ZipFile(out/'real_sft_results.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in out.rglob('*'):
                if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py'] and p.stat().st_size<20_000_000:
                    z.write(p,str(p.relative_to(out)))
        volume.commit()

@app.function(image=cpu_image,cpu=1,memory=1024,timeout=7500,scaledown_window=2)
def pipeline():
    prepare.remote()
    experiment.remote()

@app.local_entrypoint()
def main():
    pipeline.remote()
