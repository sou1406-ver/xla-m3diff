from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-invariance-v2-positive-stress')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
       .add_local_file(str(HERE/'SUPPLEMENT_PLAN.md'),'/root/SUPPLEMENT_PLAN.md',copy=True))
cpu_image=modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0').add_local_file(str(HERE/'SUPPLEMENT_PLAN.md'),'/root/SUPPLEMENT_PLAN.md',copy=True)

def setup(root,out,volume):
    import os,subprocess
    repo=root/'baseline_reproduction_v1/repo';out.mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    os.environ.update(HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false')
    py='/root/venv/bin/python'
    def run(args,name,env=None):
        print('START',name,flush=True)
        with (out/'logs'/(name+'.log')).open('a') as log:
            p=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in p.stdout:
                log.write(line);log.flush()
                if any(t in line for t in ['%|','Error','Traceback','Loading']):print(line.strip()[-260:],flush=True)
            rc=p.wait()
        volume.commit()
        if rc:raise RuntimeError(f'{name} failed {rc}')
    run(['/usr/local/bin/uv','venv','/root/venv','--python','3.10'],'venv')
    run(['/usr/local/bin/uv','pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2','peft==0.4.0','accelerate==0.29.1','bitsandbytes==0.43.3','setuptools'],'setup')
    (out/'environment_freeze.txt').write_text(subprocess.check_output(['/usr/local/bin/uv','pip','freeze','--python',py],text=True))
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='4e346e52185620ec6fa17235d93b0c26a9d47a71'
    return py,dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo),ATTN='sdpa'),run

@app.function(image=cpu_image,cpu=4,memory=8192,timeout=300,volumes={'/mnt/m3diff':volume},scaledown_window=2,retries=0)
def prepare():
    import hashlib,json
    from PIL import Image,ImageDraw
    root=Path('/mnt/m3diff');out=root/'invariance_v2_20261102';folder=out/'positive_stress';folder.mkdir(exist_ok=True)
    selected=json.loads((out/'selection_locked.json').read_text())['selected'];questions=[];meta=[]
    for i,row in enumerate(selected):
        with Image.open(root/row['image'][1]) as original:
            im=original.convert('RGB');w,h=im.size
            angle=-10 if i%2==0 else 0; scale=1. if angle else .88
            rotated=im.rotate(angle,Image.Resampling.BICUBIC,expand=True,fillcolor=(127,127,127))
            factor=min(w/rotated.width,h/rotated.height)*scale
            resized=rotated.resize((max(1,round(rotated.width*factor)),max(1,round(rotated.height*factor))),Image.Resampling.BICUBIC)
            canvas=Image.new('RGB',(w,h),(127,127,127));canvas.paste(resized,((w-resized.width)//2,(h-resized.height)//2))
            path=folder/(row['scene']+'.png');canvas.save(path)
        ims=[row['image'][0],path.relative_to(root).as_posix()];rid=row['scene']+'__positive_stress'
        questions.append({'id':rid,'image':ims,'conversations':[{'from':'human','value':"What's the difference between 2 images?  <image><image>Difference:"}]})
        meta.append({'id':rid,'scene':row['scene'],'domain':row['domain'],'angle':angle,'scale':scale,'image':ims})
    for name,value in [('questions.json',questions),('manifest.json',meta)]: (folder/name).write_text(json.dumps(value,indent=2))
    (folder/'SUPPLEMENT_PLAN.md').write_bytes(Path('/root/SUPPLEMENT_PLAN.md').read_bytes())
    (folder/'PREPARED.json').write_text(json.dumps({'n':16,'new_model_captions_used':False,'questions_sha256':hashlib.sha256((folder/'questions.json').read_bytes()).hexdigest()}))
    volume.commit(); print('POSITIVE STRESS PREPARED; CPU returns',flush=True)

@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=1200,volumes={'/mnt/m3diff':volume},scaledown_window=2,retries=0)
def evaluate():
    import hashlib,json,re,subprocess,time,zipfile
    root=Path('/mnt/m3diff');out=root/'invariance_v2_20261102';folder=out/'positive_stress'
    assert (out/'new_DONE.json').exists() and (folder/'PREPARED.json').exists()
    assert hashlib.sha256((folder/'questions.json').read_bytes()).hexdigest()==json.loads((folder/'PREPARED.json').read_text())['questions_sha256']
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip();assert re.search(r'\bA10(?:G)?\b',gpu)
    py,env,run=setup(root,folder,volume);ckpt=root/'baseline_cache/M3Diff'
    arms={'baseline':ckpt,'old_mixed':root/'invariance_ablation_v1/m3diff-mixed-objective-lora','control':out/'m3diff-control-lora','revised':out/'m3diff-revised-lora'}
    for arm,path in arms.items():
        target=folder/(arm+'.jsonl');assert not target.exists(),'Inspect existing stress outputs before retry'
        args=[py,root/'baseline_reproduction_v1/code/baseline_eval.py','--model-path',path]
        if arm!='baseline':args=[py,out/'load_wrapper.py','--adapter-mode','unmerged_fp32','--load-audit',folder/(arm+'_load_audit.json'),'--model-path',path,'--model-base',ckpt]
        args+=['--question-file',folder/'questions.json','--answers-file',target,'--image-folder',root,'--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1','--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16','--no-flash-attention']
        run(args,arm,env)
        rows=[json.loads(l) for l in target.read_text().splitlines() if l.strip()]
        assert len(rows)==16 and [r['id'] for r in rows]==[r['id'] for r in json.loads((folder/'questions.json').read_text())]
    (folder/'DONE.json').write_text(json.dumps({'generations':64,'gpu':gpu,'completed':time.time()}))
    with zipfile.ZipFile(out/'positive_stress_results.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.log','.md']:z.write(p,str(p.relative_to(out)))
    volume.commit();print('POSITIVE STRESS DONE; GPU returns',flush=True)

@app.local_entrypoint()
def main(stage:str='prepare'):
    if stage=='prepare':prepare.remote()
    elif stage=='evaluate':evaluate.remote()
    else:raise ValueError(stage)
