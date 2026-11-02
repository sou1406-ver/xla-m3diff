"""Exploratory M3Diff caption verification with LocateAnything; 24 object-focused pairs.

Three paired arms: published baseline, draft-only rewrite, locator-assisted rewrite.
References are used only after all inference, never in proposal generation or prompts.
"""
import modal

app=modal.App('m3diff-grounded-caption-pilot')
volume=modal.Volume.from_name('m3diff',create_if_missing=False)
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
       .pip_install('torch==2.6.0','torchvision==0.21.0','transformers==4.57.1','tokenizers==0.22.0',
                    'numpy==1.25.0','Pillow==11.1.0','peft==0.12.0','accelerate==1.5.2',
                    'opencv-python-headless==4.11.0.86','decord==0.6.0','lmdb==1.7.5',
                    'timm>=1.0.11','einops','sentencepiece','uv'))


@app.function(image=image,gpu='A10',cpu=4,memory=49152,timeout=5400,
              volumes={'/mnt/m3diff':volume})
def pilot():
    import os,json,re,random,time,hashlib,subprocess,sys,gc,csv,zipfile,copy
    from pathlib import Path
    root=Path('/mnt/m3diff');out=root/'grounded_caption_pilot_v1'
    out.mkdir(exist_ok=True);(out/'code').mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    base=root/'baseline_reproduction_v1';repo=base/'repo';img_root=root/'baseline_cache/OmniDiff'
    model_path=root/'locateanything_cache/model'
    os.environ['HF_HOME']=str(root/'locateanything_cache/hf')
    os.environ['HF_HUB_DISABLE_XET']='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    def save(p,obj):
        tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2));tmp.replace(p)
    def run(args,log=None,env=None):
        print('RUN:', ' '.join(map(str,args)),flush=True)
        fp=open(log,'a') if log else None
        try:
            with subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,text=True,bufsize=1) as proc:
                for line in proc.stdout:
                    print(line,end='',flush=True)
                    if fp:fp.write(line);fp.flush()
                if proc.wait():raise RuntimeError(f'Failed subprocess. Log: {log}')
        finally:
            if fp:fp.close()
    def load_rows(path):
        return {r['id']:r for r in [json.loads(l) for l in path.read_text().splitlines() if l.strip()]}

    # Handwritten noun lexicon: strip appearance qualifiers to avoid treating a color change as disappearance.
    # This prototype verifies draft-mentioned objects only; it cannot recover every omitted object.
    lexicon=[('storage box',r'\b(?:storage|plastic|green) box(?:es)?\b'),
        ('toy car',r'\btoy cars?\b'),('toy seat',r'\btoy seats?\b'),
        ('stuffed toy',r'\b(?:plush|stuffed) (?:toys?|animals?)\b'),
        ('potted plant',r'\bpotted plants?\b'),('traffic light',r'\btraffic lights?\b'),
        ('pickup truck',r'\bpickup trucks?\b'),('cabinet',r'\b(?:cabinets?|cupboards?)\b'),
        ('chair',r'\b(?:chairs?|seats?|stools?)\b'),('table',r'\b(?:tables?|desks?)\b'),
        ('car',r'\b(?:cars?|vehicles?|suvs?|sedans?)\b'),('truck',r'\btrucks?\b'),
        ('person',r'\b(?:person|people|man|men|woman|women|boy|girl|child|children)\b'),
        ('bicycle',r'\b(?:bicycles?|bikes?)\b'),('motorcycle',r'\bmotorcycles?\b'),
        ('dog',r'\bdogs?\b'),('cat',r'\bcats?\b'),('tree',r'\btrees?\b'),
        ('plant',r'\bplants?\b'),('flower',r'\bflowers?\b'),('house',r'\b(?:houses?|buildings?)\b'),
        ('bottle',r'\bbottles?\b'),('cup',r'\b(?:cups?|mugs?)\b'),('bowl',r'\bbowls?\b'),
        ('vase',r'\bvases?\b'),('book',r'\bbooks?\b'),('clock',r'\bclocks?\b'),
        ('laptop',r'\blaptops?\b'),('television',r'\b(?:television|tv)\b'),
        ('umbrella',r'\bumbrellas?\b'),('bag',r'\b(?:bags?|backpacks?|handbags?)\b'),
        ('sofa',r'\b(?:sofas?|couches|couch)\b'),('bed',r'\bbeds?\b'),
        ('ball',r'\bballs?\b'),('toy',r'\btoys?\b'),('box',r'\b(?:boxes|box)\b')]
    def proposals(caption):
        found=[];remaining=caption.lower()
        for label,pat in lexicon:
            if re.search(pat,remaining):
                found.append(label);remaining=re.sub(pat,' ',remaining)
        # Prefer specific categories over a redundant generic category.
        for broad,specifics in [('car',['toy car']),('truck',['pickup truck']),('plant',['potted plant']),
                                ('box',['storage box']),('toy',['toy car','toy seat','stuffed toy'])]:
            if broad in found and any(x in found for x in specifics):found.remove(broad)
        return found[:2]
    selected=[]
    for split in ['Real','Render']:
        qs=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text())
        preds=load_rows(base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl')
        rng=random.Random(20261027);qs=sorted(qs,key=lambda q:q['id']);rng.shuffle(qs)
        used=set();items=[]
        for q in qs:
            key=tuple(sorted(q['image']))
            labels=proposals(preds[q['id']]['caption'])
            if key in used or not labels:continue
            used.add(key)
            items.append({'id':q['id'],'split':split,'image':q['image'],
                          'original_prompt':q['conversations'][0]['value'],
                          'draft':preds[q['id']]['caption'],'queries':labels})
            if len(items)==12:break
        assert len(items)==12
        selected.extend(items)
    save(out/'selection.json',selected)
    config={'n_pairs':24,'pairs_per_split':12,'seed':20261027,'query_seed':42,
            'max_queries_per_pair':2,'selection':'Seeded shuffle; unique image pairs; baseline caption must match noun lexicon; no reference or score used for selection.',
            'base_config':json.loads((base/'run_config.json').read_text()),
            'locator_config':json.loads((root/'locateanything_demo_v1/run_config.json').read_text()),
            'limits':'Exploratory object-focused subset; draft-only noun proposals; locator misses and identity ambiguity; no training; references only for evaluation; no full-benchmark performance claim.'}
    save(out/'run_config.json',config);volume.commit()
    print('SELECTED',[(s['id'],s['queries']) for s in selected],flush=True)

    import torch
    from PIL import Image,ImageDraw,ImageOps
    from transformers import AutoTokenizer,AutoProcessor,AutoModel
    cache_path=out/'grounding_cache.json'
    cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
    tokenizer=AutoTokenizer.from_pretrained(model_path,trust_remote_code=True)
    processor=AutoProcessor.from_pretrained(model_path,trust_remote_code=True)
    locator=AutoModel.from_pretrained(model_path,torch_dtype=torch.bfloat16,
                 attn_implementation='sdpa',trust_remote_code=True).cuda().eval()
    try:
        total=sum(2*len(s['queries']) for s in selected);step=0
        for item in selected:
            evidence=[]
            for label in item['queries']:
                obs=[]
                for rel in item['image']:
                    key=hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
                    step+=1
                    if key not in cache:
                        pil=Image.open(img_root/rel).convert('RGB');pil.thumbnail((768,768))
                        prompt=f'Locate all the instances that match the following description: {label}.'
                        msgs=[{'role':'user','content':[{'type':'image','image':pil},{'type':'text','text':prompt}]}]
                        text=processor.py_apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
                        ims,vid=processor.process_vision_info(msgs)
                        inp=processor(text=[text],images=ims,videos=vid,return_tensors='pt').to('cuda')
                        torch.manual_seed(42)
                        with torch.inference_mode():
                            response=locator.generate(pixel_values=inp['pixel_values'].to(torch.bfloat16),
                              input_ids=inp['input_ids'],attention_mask=inp['attention_mask'],
                              image_grid_hws=inp.get('image_grid_hws'),tokenizer=tokenizer,
                              max_new_tokens=8192,use_cache=True,generation_mode='hybrid',
                              temperature=.7,do_sample=True,top_p=.9,repetition_penalty=1.1,verbose=False)
                        answer=response[0] if isinstance(response,tuple) else response
                        boxes=[list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',answer)]
                        valid=[b for b in boxes if all(0<=v<=1000 for v in b) and b[2]>b[0] and b[3]>b[1]]
                        none=bool(re.search(r'<box>\s*None\s*</box>',answer,re.I))
                        cache[key]={'image':rel,'label':label,'boxes':valid,'explicit_none':none,
                                    'format_ok':len(boxes)==len(valid) and bool(valid or none),'raw':answer}
                        save(cache_path,cache)
                    obs.append(cache[key]);print(f'GROUND {step}/{total}: {rel} {label} boxes={len(cache[key]["boxes"])}',flush=True)
                evidence.append({'category':label,'A':obs[0],'B':obs[1]})
            item['evidence']=evidence
            save(out/'grounded_selection.json',selected)
            volume.commit()
    finally:
        del locator,processor,tokenizer
        if 'inp' in locals():del inp
        gc.collect();torch.cuda.empty_cache()
        volume.commit()

    # Separate environment: M3Diff requires transformers 4.40 while LocateAnything uses 4.57.
    uv='/usr/local/bin/uv';venv=Path('/root/m3diff-pilot-venv');py=str(venv/'bin/python')
    if not Path(py).exists():run([uv,'venv',venv,'--python','3.10'])
    run([uv,'pip','install','--python',py,'-e',str(repo)+'[eval]','numpy<2',
         'accelerate==0.29.1','bitsandbytes==0.43.3'],out/'logs/setup.log')
    questions=[]
    instructions=('Review the two images and the draft below. The draft may be wrong. '
       'Write only the final difference caption, describing changes visibly supported by the images. '
       'Consider camera viewpoint and visibility. Do not invent object changes. ')
    for item in selected:
        draft='\nPrevious draft (unverified): '+item['draft']
        compact=[]
        for e in item['evidence']:
            row={'category':e['category']}
            for side in ['A','B']:
                obs=e[side]
                row[side]={'boxes_0_to_1000':obs['boxes'],'explicit_no_detection':obs['explicit_none'],
                           'valid_format':obs['format_ok']}
            compact.append(row)
        evidence=('\nIndependent, fallible object-locator observations: '+json.dumps(compact)+
           '\nThese observations are not ground truth. No detection does not prove absence. '
           'Same-category boxes do not prove object identity. Do not infer object movement or resizing from '
           'box coordinates alone, because camera movement and cropping also change them.')
        for arm,extra in [('control',''),('grounded',evidence)]:
            prompt=item['original_prompt']+'\n'+instructions+draft+extra+'\nFinal difference caption:'
            assert prompt.count('<image>')==2
            questions.append({'id':arm+'__'+item['id'],'image':item['image'],
                              'conversations':[{'from':'human','value':prompt}]})
    qpath=out/'rewrite_questions.json';save(qpath,questions)
    ans=out/'rewrites.jsonl'
    env=dict(os.environ,M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',
             PYTHONPATH=str(repo)+os.pathsep+os.environ.get('PYTHONPATH',''))
    run([py,base/'code/baseline_eval.py','--model-path',root/'baseline_cache/M3Diff',
         '--question-file',qpath,'--answers-file',ans,'--image-folder',img_root,
         '--num-chunks','1','--chunk-idx','0','--temperature','0','--num_beams','1',
         '--max-new-tokens','1024','--conv-mode','qwen_2','--torch-dtype','bfloat16',
         '--no-flash-attention'],out/'logs/rewrite.log',env)
    rewrites=load_rows(ans);assert len(rewrites)==48
    print('REWRITES COMPLETE',flush=True);volume.commit()

    # Read references only here, after every caption is generated.
    metrics={};manual=[]
    for split in ['Real','Render']:
        items=[s for s in selected if s['split']==split];ids={s['id'] for s in items}
        reference=json.loads((repo/f'data/evaluation/reference/OmniDiff_{split}.json').read_text())
        sub=copy.deepcopy(reference)
        sub['images']=[r for r in reference['images'] if r['id'] in ids]
        sub['annotations']=[r for r in reference['annotations'] if r['image_id'] in ids]
        assert {r['id'] for r in sub['images']}==ids
        refpath=out/f'{split}_reference_subset.json';save(refpath,sub)
        metrics[split]={}
        for arm in ['baseline','control','grounded']:
            pred=[]
            for item in items:
                cap=item['draft'] if arm=='baseline' else rewrites[arm+'__'+item['id']]['caption']
                pred.append({'id':item['id'],'image_id':item['id'],'caption':cap})
            predpath=out/f'{split}_{arm}.jsonl'
            predpath.write_text(''.join(json.dumps(r)+'\n' for r in pred))
            scorepath=out/f'{split}_{arm}_scores.json'
            run([py,base/'code/score_baseline.py','--reference',refpath,
                 '--prediction',predpath,'--output',scorepath],out/'logs/metrics.log',env)
            metrics[split][arm]=json.loads(scorepath.read_text())
        for item in items:
            manual.append({'id':item['id'],'split':split,'images':item['image'],
                'baseline':item['draft'],'control':rewrites['control__'+item['id']]['caption'],
                'grounded':rewrites['grounded__'+item['id']]['caption'],
                'references':[a['caption'] for a in sub['annotations'] if a['image_id']==item['id']],
                'evidence':item['evidence']})
    save(out/'metrics.json',metrics);save(out/'comparison.json',manual)
    with open(out/'manual_review.csv','w',newline='') as f:
        keys=['id','split','baseline','control','grounded','references',
              'grounded_fixes_error','grounded_introduces_error','review_notes']
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for r in manual:
            writer.writerow({k: (' | '.join(r[k]) if k=='references' else r[k]) for k in keys if k in r})
    # Contact sheets include originals, all three captions, and references for honest review.
    import textwrap
    for page in range(6):
        subset=manual[page*4:(page+1)*4]
        sheet=Image.new('RGB',(1400,1600),'white');draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(subset):
            y=j*400;draw.text((5,y+3),r['id'],fill='black')
            for k,rel in enumerate(r['images']):
                im=ImageOps.contain(Image.open(img_root/rel).convert('RGB'),(330,330))
                sheet.paste(im,(k*340,y+30))
            ty=y+25
            for key in ['baseline','control','grounded']:
                txt=key.upper()+': '+r[key]
                lines=textwrap.wrap(txt,width=93)
                # Truncation is display-only; full captions remain in JSON/CSV.
                if len(lines)>7:lines=lines[:7]+['[full text in comparison.json]']
                draw.multiline_text((690,ty),'\n'.join(lines),fill='black',spacing=2)
                ty+=len(lines)*13+10
            refs=textwrap.wrap('REF: '+' | '.join(r['references']),width=93)[:5]
            draw.multiline_text((690,min(ty,y+320)),'\n'.join(refs),fill='#444444',spacing=2)
        sheet.save(out/f'review_{page+1}.jpg',quality=92)
    report=['# Grounded-caption pilot: M3Diff + LocateAnything','',
       '24 object-focused pairs, 12 Real + 12 Render. No training. Fixed selection before grounding or scoring.',
       'Baseline vs draft-only rewrite (control) vs draft + locator observations (grounded).',
       'References never used in inference. Scores are for these subsets only; CIDEr is recomputed on each subset.',
       'This is an exploratory pilot, not the full benchmark and not evidence of improvement by itself.','',
       '|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|',
       '|---|---|---:|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm,s in arms.items():
            report.append(f"|{split}|{arm}|{s['Bleu_4']*100:.2f}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    report+=['','Inspect comparison.json and review_*.jpg. Fill manual_review.csv to distinguish corrected errors from new errors.',
       'Locator output is fallible; same-class detections do not establish identity; misses do not establish absence.',
       'Draft-only proposals cannot verify objects omitted from the initial draft. Both rewrite arms change the prompt distribution.']
    (out/'REPORT.md').write_text('\n'.join(report))
    save(out/'SUCCESS.json',{'n_pairs':24,'n_rewrites':48,'metrics':metrics})
    with zipfile.ZipFile(out/'grounded_caption_pilot.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob('*'):
            if p.is_file() and p.suffix!='.zip':z.write(p,p.relative_to(out))
    volume.commit();print('METRICS',json.dumps(metrics),flush=True);print('DONE',out,flush=True)


@app.local_entrypoint()
def main():
    pilot.remote()
