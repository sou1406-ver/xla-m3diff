"""Locked V4 minimal checker: CPU planning -> optional A10 grounding -> CPU scoring.

Uses cached M3Diff captions from the completed baseline, never reference captions at inference.
Run: modal run --detach modal_app.py
"""
from pathlib import Path
import modal

APP_DIR=Path(__file__).parent
app=modal.App('m3diff-caption-verifier-validation')
volume=modal.Volume.from_name('m3diff',create_if_missing=False)
cpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless')
    .pip_install('numpy==1.25.0','Pillow==11.1.0','opencv-python-headless==4.11.0.86','pycocoevalcap==1.2','pycocotools')
    .add_local_file(str(APP_DIR/'caption_verifier.py'),'/root/caption_verifier.py',copy=True))
gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
    .pip_install('torch==2.6.0','torchvision==0.21.0','transformers==4.57.1','tokenizers==0.22.0',
        'numpy==1.25.0','Pillow==11.1.0','peft==0.12.0','accelerate==1.5.2',
        'opencv-python-headless==4.11.0.86','decord==0.6.0','lmdb==1.7.5','timm>=1.0.11','einops','sentencepiece','uv'))


@app.function(image=gpu_image,gpu='A10',cpu=4,memory=32768,timeout=1800,
              volumes={'/mnt/m3diff':volume},scaledown_window=2)
def locate(run_name):
    import os,json,re,torch
    from transformers import AutoModel,AutoTokenizer,AutoProcessor
    from PIL import Image
    root=Path('/mnt/m3diff');out=root/run_name
    tasks=json.loads((out/'locator_tasks.json').read_text())
    cache=json.loads((out/'grounding.json').read_text()) if (out/'grounding.json').exists() else {}
    pending=[t for t in tasks if t['key'] not in cache]
    if not pending:return len(cache)
    os.environ['HF_HOME']=str(root/'locateanything_cache/hf');os.environ['HF_HUB_DISABLE_XET']='1'
    model_dir=root/'locateanything_cache/model'
    tokenizer=AutoTokenizer.from_pretrained(model_dir,trust_remote_code=True)
    processor=AutoProcessor.from_pretrained(model_dir,trust_remote_code=True)
    model=AutoModel.from_pretrained(model_dir,torch_dtype=torch.bfloat16,
                                  attn_implementation='sdpa',trust_remote_code=True).cuda().eval()
    try:
        for i,task in enumerate(pending):
            im=Image.open(root/'baseline_cache/OmniDiff'/task['image']).convert('RGB');im.thumbnail((768,768))
            prompt=f"Locate all the instances that match the following description: {task['label']}."
            msgs=[{'role':'user','content':[{'type':'image','image':im},{'type':'text','text':prompt}]}]
            text=processor.py_apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
            ims,vids=processor.process_vision_info(msgs)
            inp=processor(text=[text],images=ims,videos=vids,return_tensors='pt').to('cuda')
            torch.manual_seed(42)
            with torch.inference_mode():
                response=model.generate(pixel_values=inp['pixel_values'].to(torch.bfloat16),input_ids=inp['input_ids'],
                    attention_mask=inp['attention_mask'],image_grid_hws=inp.get('image_grid_hws'),tokenizer=tokenizer,
                    max_new_tokens=8192,use_cache=True,generation_mode='hybrid',temperature=.7,do_sample=True,
                    top_p=.9,repetition_penalty=1.1,verbose=False)
            answer=response[0] if isinstance(response,tuple) else response
            boxes=[list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',answer)]
            valid=[b for b in boxes if all(0<=v<=1000 for v in b) and b[2]>b[0] and b[3]>b[1]]
            none=bool(re.search(r'<box>\s*None\s*</box>',answer,re.I))
            cache[task['key']]={**task,'boxes':valid,'explicit_none':none,
                'format_ok':len(boxes)==len(valid) and bool(valid or none),'raw':answer,'prompt':prompt}
            tmp=out/'grounding.tmp';tmp.write_text(json.dumps(cache,indent=2));tmp.replace(out/'grounding.json')
            print(f'LOCATE {i+1}/{len(pending)}: {task["label"]} boxes={len(valid)}',flush=True)
            if (i+1)%8==0:volume.commit()
    finally:volume.commit()
    print('GPU grounding complete; releasing container.',flush=True)
    return len(cache)


@app.function(image=cpu_image,cpu=4,memory=8192,timeout=3600,
              volumes={'/mnt/m3diff':volume},scaledown_window=2)
def pipeline(run_name='caption_verifier_validation_v1',per_split=12):
    import sys,json,re,hashlib,random,csv,subprocess,zipfile,textwrap,datetime
    import numpy as np
    from PIL import Image,ImageDraw
    sys.path.insert(0,'/root')
    from caption_verifier import extract_claims,align_pair,stable_region,verify_color_transition
    assert re.fullmatch(r'[a-zA-Z0-9_-]+',run_name),'run_name must be one directory name'
    assert 1<=per_split<=20,'Small validation jobs only'
    root=Path('/mnt/m3diff');out=root/run_name;out.mkdir(exist_ok=True)
    base=root/'baseline_reproduction_v1';repo=base/'repo';imgroot=root/'baseline_cache/OmniDiff'
    def save(name,obj):
        tmp=out/(name+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2));tmp.replace(out/name)
    def rows(path):return {r['id']:r for r in [json.loads(l) for l in path.read_text().splitlines() if l.strip()]}
    def key(rel,label):return hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
    def eligible(claim):
        if claim['event']!='removed':return None
        head=re.split(r'\b(?:on|in|at|near|beside|above|below|behind|with|wearing|that|which|to|of)\b',claim['sentence'],1,flags=re.I)[0]
        colors=set(re.findall(r'\b(?:red|orange|yellow|green|blue|purple|pink|brown)\b',head,re.I))
        return next(iter(colors)).lower() if len(colors)==1 else None
    # Exclude all development/pilot images, plus earlier qualitative demo images.
    dev=json.loads((root/'grounded_caption_pilot_v1/selection.json').read_text())
    excluded_images={im for r in dev for im in r['image']}
    for r in json.loads((root/'locateanything_demo_v1/results.json').read_text()):excluded_images.add(r['source_image'])
    selected=[];used_images=set()
    for split in ['Real','Render']:
        qs=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text())
        preds=rows(base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl')
        qs=sorted(qs,key=lambda q:q['id']);random.Random(20261028).shuffle(qs)
        take=[]
        for q in qs:
            if set(q['image']) & (excluded_images|used_images):continue
            draft=preds[q['id']]['caption'];sentences,claims=extract_claims(draft)
            if not claims:continue  # claim-focused diagnostic, fixed before any reference/score lookup
            item={'id':q['id'],'split':split,'images':q['image'],'baseline':draft,
                  'sentences':sentences,'claims':claims}
            take.append(item);used_images.update(q['image'])
            if len(take)==per_split:break
        if len(take)!=per_split:raise RuntimeError(f'{split}: only {len(take)} disjoint eligible pairs; no GPU launched')
        selected+=take
    assert not (used_images & excluded_images)
    config={'version':'locked V4','selection_seed':20261028,'n_pairs':len(selected),'per_split':per_split,
      'selection':'Seeded shuffled baseline questions, at least one parsable added/removed draft clause; exclude development and demo images; no shared images within this batch.',
      'color_rule':'Only removed claims with one chromatic subject color; generic unique A/B detections, reliable SIFT homography, aligned IoU>=.80, >=30 interior source-color pixels, >=.80 dominant different target color.',
      'algorithm_sha256':hashlib.sha256(Path('/root/caption_verifier.py').read_bytes()).hexdigest(),
      'baseline_config':json.loads((base/'run_config.json').read_text()),
      'excluded_images':sorted(excluded_images),
      'limitations':'Small claim-focused diagnostic, image-disjoint but not guaranteed scene-disjoint from development. Baseline captions reused, not regenerated. Not full OmniDiff benchmark. Frozen before looking at this batch references/scores.'}
    if (out/'run_config.json').exists() and json.loads((out/'run_config.json').read_text())!=config:
        raise RuntimeError('Run config changed; use a new run_name instead of mixing outputs')
    save('run_config.json',config);save('selection.json',selected)
    print('SELECTED',[(r['id'],len(r['claims'])) for r in selected],flush=True)
    tasks={}
    for item in selected:
        images=[]
        for rel in item['images']:
            p=Image.open(imgroot/rel).convert('RGB');p.thumbnail((768,768));images.append(np.array(p))
        alignment,h=align_pair(*images)
        item['alignment']=alignment
        for c in item['claims']:
            c['subject_color']=eligible(c)
            if not alignment['ok'] or not c['subject_color']:continue
            for rel in item['images']:
                k=key(rel,c['label']);tasks[k]={'key':k,'image':rel,'label':c['label']}
    save('prepared.json',selected);save('locator_tasks.json',list(tasks.values()));volume.commit()
    print('Prepared',len(selected),'pairs;',len(tasks),'grounding queries needed.',flush=True)
    if tasks:
        locate.remote(run_name)
        volume.reload()  # all file handles closed; make child-function writes visible
    cache=json.loads((out/'grounding.json').read_text()) if tasks else {}
    results=[]
    for item in selected:
        images=[]
        for rel in item['images']:
            p=Image.open(imgroot/rel).convert('RGB');p.thumbnail((768,768));images.append(np.array(p))
        sentences=list(item['sentences']);decisions=[]
        for c in item['claims']:
            d={'claim':c,'action':'keep','reason':'outside supported scope or uncertain'};decisions.append(d)
            if not item['alignment']['ok'] or not c['subject_color']:continue
            obs=[cache[key(rel,c['label'])] for rel in item['images']]
            if any(not o['format_ok'] or len(o['boxes'])!=1 for o in obs):
                d['reason']='missing, malformed, or non-unique detections';continue
            h=np.array(item['alignment']['H']);geometry=stable_region(*images,h,obs[0]['boxes'],obs[1]['boxes'])
            d['geometry']=geometry
            if geometry.get('aligned_box_iou',0)<.80 or 'box_a' not in geometry:
                d['reason']='geometry/overlap insufficient';continue
            evidence=verify_color_transition(*images,h,geometry['box_a'],geometry['box_b_aligned'],c['subject_color'])
            d['color_evidence']=evidence
            if evidence['supported']:
                replacement=f"The {c['label']} has changed from {evidence['source_color']} to {evidence['target_color']}."
                sentences[c['sentence_index']]=replacement
                d.update(action='replace',reason='matched region has a dominant supported color transition',replacement=replacement)
            else:d['reason']='color evidence insufficient'
        caption=' '.join(sentences)
        results.append({'id':item['id'],'split':item['split'],'images':item['images'],'baseline':item['baseline'],
                        'verified':caption,'changed':caption!=item['baseline'],'decisions':decisions})
        print('CHECK',item['id'],'changed=',results[-1]['changed'],flush=True)
    save('comparison.json',results);volume.commit()
    # Reference access starts only after every editing decision is saved.
    metrics={};refs={}
    for split in ['Real','Render']:
        ids={r['id'] for r in results if r['split']==split}
        reference=json.loads((repo/f'data/evaluation/reference/OmniDiff_{split}.json').read_text())
        reference['images']=[r for r in reference['images'] if r['id'] in ids]
        reference['annotations']=[r for r in reference['annotations'] if r['image_id'] in ids]
        assert {r['id'] for r in reference['images']}==ids
        refpath=out/f'{split}_reference.json';save(refpath.name,reference)
        for r in reference['annotations']:refs.setdefault(r['image_id'],[]).append(r['caption'])
        metrics[split]={}
        for arm in ['baseline','verified']:
            pred=out/f'{split}_{arm}.jsonl'
            pred.write_text(''.join(json.dumps({'id':r['id'],'image_id':r['id'],'caption':r[arm]})+'\n' for r in results if r['split']==split))
            score=out/f'{split}_{arm}_scores.json'
            subprocess.run([sys.executable,str(base/'code/score_baseline.py'),'--reference',str(refpath),
                            '--prediction',str(pred),'--output',str(score)],check=True)
            metrics[split][arm]=json.loads(score.read_text())
    save('metrics.json',metrics)
    edits=[r for r in results if r['changed']]
    with open(out/'manual_review.csv','w',newline='') as f:
        fields=['id','split','baseline','verified','references','human_edit_correct','human_notes']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in edits:writer.writerow({k:(' | '.join(refs[r['id']]) if k=='references' else r.get(k,'')) for k in fields})
    for i,r in enumerate(edits):
        sheet=Image.new('RGB',(1200,1100),'white');draw=ImageDraw.Draw(sheet)
        for side,rel in enumerate(r['images']):
            p=Image.open(imgroot/rel).convert('RGB');p.thumbnail((580,580));sheet.paste(p,(side*600,30))
        y=620
        for title,caption in [('BASE',r['baseline']),('VERIFIED',r['verified']),('REF',' | '.join(refs[r['id']]))]:
            lines=textwrap.wrap(title+': '+caption,width=150)
            draw.multiline_text((8,y),'\n'.join(lines),fill='black',spacing=3);y+=len(lines)*14+16
        sheet.save(out/f'edit_{i+1}_{r["id"]}.jpg',quality=95)
    report=['# Locked V4 — new image-disjoint validation batch','',
      f'{len(results)} pairs; {len(tasks)} locator queries; {len(edits)} captions edited.',
      'Frozen rules, no reference/score access until inference ended. Cached M3Diff captions reused.',
      'Image-disjoint from development and within this batch; not guaranteed scene-disjoint. Claim-focused sample, not full benchmark.','',
      '|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|','|---|---|---:|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm,s in arms.items():report.append(f"|{split}|{arm}|{s['Bleu_4']*100:.2f}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    report+=['','CIDEr recomputed on each subset. Compare arms within the same split only.',
       'No-edit cases retain baseline exactly. Low coverage or a false edit must be reported, not hidden.',
       'Inspect comparison.json and every edited-image panel; manual_review.csv starts with blank human judgments.']
    (out/'REPORT.md').write_text('\n'.join(report))
    with open(out/'summary_x100.csv','w',newline='') as f:
        fields=['split','arm','Bleu_4','METEOR','ROUGE_L','CIDEr'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for split,arms in metrics.items():
            for arm,s in arms.items():writer.writerow({'split':split,'arm':arm,**{k:s[k]*100 for k in fields[2:]}})
    save('SUCCESS.json',{'n_pairs':len(results),'n_edits':len(edits),'n_locator_queries':len(tasks),
                        'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metrics':metrics})
    with zipfile.ZipFile(out/'validation_results.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    volume.commit();print('DONE',len(results),'pairs;',len(edits),'edits. METRICS',json.dumps(metrics),flush=True)


@app.local_entrypoint()
def main(run_name: str='caption_verifier_validation_v1',per_split: int=12):
    pipeline.remote(run_name,per_split)
