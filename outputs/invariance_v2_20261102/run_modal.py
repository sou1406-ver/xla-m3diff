from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-invariance-v2-20261102'); volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
       .add_local_file(str(HERE/'train_audited.py'),'/root/train_audited.py',copy=True)
       .add_local_file(str(HERE/'PLAN.md'),'/root/PLAN.md',copy=True)
       .add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/load_wrapper.py',copy=True))

def setup(root,out,volume):
    import json,os,subprocess,time
    repo=root/'baseline_reproduction_v1/repo'; out.mkdir(exist_ok=True); (out/'logs').mkdir(exist_ok=True)
    os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
    py='/root/venv/bin/python'; uv='/usr/local/bin/uv'
    def run(args,name,env=None):
        print('START',name,flush=True); started=time.time()
        with (out/'logs'/(name+'.log')).open('a') as log:
            p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in p.stdout:
                log.write(line); log.flush()
                if any(t in line for t in ['%|','Error','Traceback','Loading',"'loss'",'train_runtime']): print(line.strip()[-260:],flush=True)
            rc=p.wait()
        volume.commit()
        if rc: raise RuntimeError(f'{name} failed {rc}')
        return time.time()-started
    run([uv,'venv','/root/venv','--python','3.10'],'venv')
    run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'setup')
    freeze=subprocess.check_output([uv,'pip','freeze','--python',py],text=True)
    (out/'environment_freeze.txt').write_text(freeze)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    assert commit=='4e346e52185620ec6fa17235d93b0c26a9d47a71'
    env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo),ATTN='sdpa')
    return py,env,run

@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=1800,volumes={'/mnt/m3diff':volume},scaledown_window=2,retries=0)
def evaluate(stage:str='initial'):
    import hashlib,json,re,subprocess,time,zipfile
    root=Path('/mnt/m3diff'); out=root/'invariance_v2_20261102'; assert (out/'REVIEW_APPROVED.json').exists()
    approval=json.loads((out/'REVIEW_APPROVED.json').read_text())
    assert hashlib.sha256((out/'eval_questions.json').read_bytes()).hexdigest()==approval['eval_questions_sha256']
    assert hashlib.sha256((out/'eval_rubric.json').read_bytes()).hexdigest()==approval['rubric_sha256']
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()
    assert re.search(r'\bA10(?:G)?\b',gpu)
    py,env,run=setup(root,out,volume); ckpt=root/'baseline_cache/M3Diff'
    (out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())
    arms={'baseline':ckpt,'old_mixed':root/'invariance_ablation_v1/m3diff-mixed-objective-lora'} if stage=='initial' else {
        'control':out/'m3diff-control-lora','revised':out/'m3diff-revised-lora'}
    for arm,path in arms.items():
        target=out/(arm+'.jsonl')
        # This run has immutable questions; require full ordered IDs on a reused completed file.
        questions=json.loads((out/'eval_questions.json').read_text())
        if target.exists():
            rows=[json.loads(l) for l in target.read_text().splitlines() if l.strip()]
            assert [r['id'] for r in rows]==[q['id'] for q in questions], 'Partial output must be inspected, not silently overwritten'
            continue
        args=[py,root/'baseline_reproduction_v1/code/baseline_eval.py','--model-path',path]
        if arm!='baseline': args=[py,out/'load_wrapper.py','--adapter-mode','unmerged_fp32','--load-audit',out/(arm+'_load_audit.json'),
                                  '--model-path',path,'--model-base',ckpt]
        args+=['--question-file',out/'eval_questions.json','--answers-file',target,'--image-folder',root,'--num-chunks','1','--chunk-idx','0',
               '--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention']
        run(args,arm,env)
        rows=[json.loads(l) for l in target.read_text().splitlines() if l.strip()]
        assert [r['id'] for r in rows]==[q['id'] for q in questions] and all(r['caption'].strip() for r in rows)
    (out/(stage+'_DONE.json')).write_text(json.dumps({'arms':list(arms),'n_eval':len(questions),'gpu':gpu,'completed':time.time(),'GPU_released_on_return':True}))
    with zipfile.ZipFile(out/(stage+'_results.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix in ['.json','.jsonl','.md','.txt','.py']: z.write(p,p.name)
        for p in (out/'logs').glob('*.log'): z.write(p,'logs/'+p.name)
    volume.commit(); print('EVALUATION DONE; GPU returning',flush=True)

@app.function(image=image,gpu='A100-40GB',cpu=8,memory=65536,timeout=2700,volumes={'/mnt/m3diff':volume},scaledown_window=2,retries=0)
def train():
    import hashlib,json,math,subprocess,time
    root=Path('/mnt/m3diff'); out=root/'invariance_v2_20261102'; assert (out/'TRAIN_APPROVED.json').exists()
    approval=json.loads((out/'TRAIN_APPROVED.json').read_text())
    for arm in ['control','revised']:
        assert hashlib.sha256((out/f'train_{arm}.json').read_bytes()).hexdigest()==approval['train_hashes'][arm]
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip(); assert 'A100' in gpu
    py,env,run=setup(root,out,volume); ckpt=root/'baseline_cache/M3Diff'
    (out/'train_audited.py').write_bytes(Path('/root/train_audited.py').read_bytes())
    for arm in ['control','revised']:
        model=out/('m3diff-'+arm+'-lora')
        if (model/'TRAIN_DONE.json').exists(): continue
        assert not model.exists(), 'Inspect incomplete checkpoint directory before retrying training.'
        args=[py,out/'train_audited.py','--model_name_or_path',ckpt,'--version','qwen_2','--output_dir',model,
            '--data_path',out/f'train_{arm}.json','--image_folder',root,'--image_aspect_ratio','pad','--vision_tower','google/siglip-so400m-patch14-384',
            '--mm_vision_select_layer','[-11,-8,-5,-2]','--unfreeze_mm_vision_tower','False','--mm_projector_type','mlp2x_gelu','--mm_patch_merge_type','flat',
            '--mm_resampler_type','mdp','--mdp_args','{"num_refinement_layers":2,"feature_dim":1152,"ffn_hidden_dim":4608,"attention_downsample_rate":1}',
            '--tune_mm_vision_resampler','False','--freeze_reasmpler','True','--freeze_mm_mlp_adapter','True','--mm_use_im_start_end','False','--mm_use_im_patch_token','False',
            '--lora_enable','True','--lora_r','16','--lora_alpha','32','--num_train_epochs','2','--per_device_train_batch_size','1','--gradient_accumulation_steps','8',
            '--learning_rate','1e-5','--weight_decay','0','--warmup_ratio','.03','--lr_scheduler_type','cosine','--logging_steps','8','--model_max_length','4096',
            '--gradient_checkpointing','True','--group_by_modality_length','False','--dataloader_num_workers','2','--lazy_preprocess','True','--bf16','True','--tf32','True',
            '--report_to','none','--save_strategy','no','--seed','42']
        run(args,arm+'_train',env)
        assert json.loads((model/'TRAIN_DONE.json').read_text())['steps']==128
        volume.commit()
    models=[out/('m3diff-'+a+'-lora') for a in ['control','revised']]
    audits=[json.loads((m/'initialization_audit.json').read_text()) for m in models]
    assert all(audits[0][k]==audits[1][k] for k in ['lora_init_sha256','MDP_init_sha256'])
    orders=[json.loads((m/'sample_orders.json').read_text()) for m in models]
    assert orders[0]==orders[1] and len(orders[0])==2 and all(sorted(x)==list(range(512)) for x in orders[0])
    (out/'MATCHED_TRAIN_DONE.json').write_text(json.dumps({'same_initialization':True,'same_index_orders':True,'steps_each':128,'gpu':gpu,'completed':time.time()}))
    volume.commit(); print('BOTH TRAINING ARMS SAVED; GPU returning',flush=True)

@app.function(image=image,cpu=0.25,memory=512,timeout=5400,scaledown_window=2,retries=0)
def pipeline():
    # One durable CPU call owns the sequence, so chat/client disconnection cannot
    # leave a trained checkpoint unevaluated or a GPU waiting for human review.
    train.remote()
    evaluate.remote('new')
    print('PIPELINE COMPLETE; all GPU functions returned',flush=True)

@app.local_entrypoint()
def main(stage:str='initial'):
    if stage=='train': train.remote()
    elif stage=='pipeline': pipeline.remote()
    elif stage in ['initial','new']: evaluate.remote(stage)
    else: raise ValueError(stage)
