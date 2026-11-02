"""M3Diff caption stays primary. LocateAnything + geometric/visual checks filter only contradicted clauses."""
from pathlib import Path
import modal

app=modal.App('m3diff-minimal-caption-verifier-v2')
volume=modal.Volume.from_name('m3diff',create_if_missing=False)
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
       .pip_install('torch==2.6.0','torchvision==0.21.0','transformers==4.57.1','tokenizers==0.22.0',
                    'numpy==1.25.0','Pillow==11.1.0','peft==0.12.0','accelerate==1.5.2',
                    'opencv-python-headless==4.11.0.86','decord==0.6.0','lmdb==1.7.5',
                    'timm>=1.0.11','einops','sentencepiece','uv')
       .pip_install('pycocoevalcap==1.2','pycocotools')
       .add_local_file(str(Path(__file__).with_name('caption_verifier.py')),'/root/caption_verifier.py',copy=True))


@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=2400,
              volumes={'/mnt/m3diff':volume})
def verify():
    import os,sys,json,re,hashlib,csv,zipfile,subprocess,gc,textwrap
    sys.path.insert(0,'/root')
    from caption_verifier import extract_claims,align_pair,stable_region,minimally_filter
    root=Path('/mnt/m3diff');old=root/'grounded_caption_pilot_v1';out=root/'caption_verifier_v2'
    out.mkdir(exist_ok=True);imgroot=root/'baseline_cache/OmniDiff'
    items=json.loads((old/'comparison.json').read_text())
    cache=json.loads((old/'grounding_cache.json').read_text())
    if (out/'grounding_cache.json').exists():cache.update(json.loads((out/'grounding_cache.json').read_text()))
    def save(p,data):
        temp=Path(str(p)+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.replace(p)
    plan=[];needed={}
    def key(rel,label):return hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
    for item in items:
        sentences,claims=extract_claims(item['baseline'])
        plan.append({**item,'sentences':sentences,'claims':claims})
        for c in claims:
            for rel in item['images']:
                k=key(rel,c['label'])
                if k not in cache:needed[k]=(rel,c['label'])
    save(out/'claim_plan.json',plan)
    config={'method':'Rule-based minimal deletion with abstention; baseline otherwise unchanged; no rewriting LLM.',
       'n_pairs':len(items),'n_claims':sum(len(p['claims']) for p in plan),'new_grounding_queries':len(needed),
       'thresholds':{'sift_ratio':.70,'min_inliers':25,'min_inlier_ratio':.45,'min_coverage':.10,
                     'min_aligned_box_iou':.60,'min_match_margin':.20,'min_ssim':.80,'min_edge_corr':.85,
                     'max_instances_for_edit':1,'min_valid_overlap':.98},
       'evaluation':'Same 24-pair development pilot as V1; not held-out validation. No references used in editing.',
       'limits':'Only selected added/removed clauses are checked. Correct identity is not guaranteed by geometry/similarity. Color/pose/OCR claims not repaired. If every sentence would be removed, keep original.'}
    save(out/'run_config.json',config);volume.commit()
    print('PLAN',json.dumps(config),flush=True)
    os.environ['HF_HOME']=str(root/'locateanything_cache/hf')
    os.environ['HF_HUB_DISABLE_XET']='1'
    import numpy as np,cv2
    from PIL import Image,ImageDraw,ImageOps
    # Meaningful safeguards: same textured ROI passes; altered ROI and ambiguous instances abstain.
    sample=np.array(Image.open(root/'locateanything_demo_v1/real_before_box_input.png').convert('RGB'))
    testbox=[[712,0,998,169]]
    assert stable_region(sample,sample,np.eye(3),testbox,testbox)['stable']
    changed=sample.copy();changed[:130,540:]=0
    assert not stable_region(sample,changed,np.eye(3),testbox,testbox)['stable']
    assert not stable_region(sample,sample,np.eye(3),testbox*2,testbox*2)['stable']
    assert not stable_region(sample,sample,np.eye(3),testbox,[])['stable']
    print('PASS visual-consistency and abstention safeguards',flush=True)
    if needed:
        import torch
        from transformers import AutoModel,AutoTokenizer,AutoProcessor
        mp=root/'locateanything_cache/model'
        tokenizer=AutoTokenizer.from_pretrained(mp,trust_remote_code=True)
        processor=AutoProcessor.from_pretrained(mp,trust_remote_code=True)
        model=AutoModel.from_pretrained(mp,torch_dtype=torch.bfloat16,attn_implementation='sdpa',trust_remote_code=True).cuda().eval()
        try:
            for j,(k,(rel,label)) in enumerate(needed.items()):
                pil=Image.open(imgroot/rel).convert('RGB');pil.thumbnail((768,768))
                msgs=[{'role':'user','content':[{'type':'image','image':pil},
                    {'type':'text','text':f'Locate all the instances that match the following description: {label}.'}]}]
                text=processor.py_apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
                ims,vid=processor.process_vision_info(msgs)
                inp=processor(text=[text],images=ims,videos=vid,return_tensors='pt').to('cuda')
                torch.manual_seed(42)
                with torch.inference_mode():
                    response=model.generate(pixel_values=inp['pixel_values'].to(torch.bfloat16),input_ids=inp['input_ids'],
                        attention_mask=inp['attention_mask'],image_grid_hws=inp.get('image_grid_hws'),tokenizer=tokenizer,
                        max_new_tokens=8192,use_cache=True,generation_mode='hybrid',temperature=.7,
                        do_sample=True,top_p=.9,repetition_penalty=1.1,verbose=False)
                answer=response[0] if isinstance(response,tuple) else response
                boxes=[list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',answer)]
                valid=[b for b in boxes if all(0<=v<=1000 for v in b) and b[2]>b[0] and b[3]>b[1]]
                none=bool(re.search(r'<box>\s*None\s*</box>',answer,re.I))
                cache[k]={'image':rel,'label':label,'boxes':valid,'explicit_none':none,
                          'format_ok':len(valid)==len(boxes) and bool(valid or none),'raw':answer}
                save(out/'grounding_cache.json',cache)
                print(f'LOCATE {j+1}/{len(needed)} {label}: {len(valid)} boxes',flush=True)
                if (j+1)%8==0:volume.commit()
        finally:
            del model,processor,tokenizer
            if 'inp' in locals():del inp
            gc.collect();torch.cuda.empty_cache();volume.commit()
    results=[]
    for item in plan:
        pil_a=Image.open(imgroot/item['images'][0]).convert('RGB');pil_a.thumbnail((768,768))
        pil_b=Image.open(imgroot/item['images'][1]).convert('RGB');pil_b.thumbnail((768,768))
        a,b=np.array(pil_a),np.array(pil_b)
        alignment,h=align_pair(a,b) if item['claims'] else ({'ok':False,'reason':'no eligible event claims'},None)
        decisions=[]
        for claim in item['claims']:
            oa=cache[key(item['images'][0],claim['label'])];ob=cache[key(item['images'][1],claim['label'])]
            d={'claim':claim,'action':'keep','reason':'abstain','A':oa,'B':ob}
            if not oa['format_ok'] or not ob['format_ok']:d['reason']='invalid grounding format'
            elif not alignment['ok']:d['reason']='alignment not reliable: '+alignment['reason']
            elif not oa['boxes'] or not ob['boxes']:d['reason']='missing detections are not proof; keep original'
            else:
                evidence=stable_region(a,b,h,oa['boxes'],ob['boxes']);d['visual_evidence']=evidence
                if evidence['stable']:
                    d.update(action='drop',reason='same unique category region strongly agrees across images; event claim contradicted by conservative visual heuristic')
                else:d['reason']=evidence['reason']
            decisions.append(d)
        caption=minimally_filter(item['sentences'],decisions)
        result={k:item[k] for k in ['id','split','images','baseline','control','grounded','references']}
        result.update(v2=caption,changed=caption!=item['baseline'],alignment=alignment,decisions=decisions)
        results.append(result)
        print('VERIFY',item['id'],'edit=',result['changed'],[(d['claim']['label'],d['action'],d['reason']) for d in decisions],flush=True)
    save(out/'comparison.json',results);volume.commit()
    # Scoring only now reads reference subsets from V1. They were not used by the editor.
    metrics=json.loads((old/'metrics.json').read_text())
    score_script=root/'baseline_reproduction_v1/code/score_baseline.py'
    for split in ['Real','Render']:
        rows=[{'id':r['id'],'image_id':r['id'],'caption':r['v2']} for r in results if r['split']==split]
        pred=out/f'{split}_v2.jsonl';pred.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        scores=out/f'{split}_v2_scores.json'
        subprocess.run([sys.executable,str(score_script),'--reference',str(old/f'{split}_reference_subset.json'),
                        '--prediction',str(pred),'--output',str(scores)],check=True)
        metrics[split]['v2']=json.loads(scores.read_text())
    save(out/'metrics.json',metrics)
    with open(out/'claims.csv','w',newline='') as f:
        fields=['id','split','event','label','sentence','action','reason','aligned_box_iou','ssim','edge_correlation']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in results:
            for d in r['decisions']:
                writer.writerow({'id':r['id'],'split':r['split'],**d['claim'],
                    'action':d['action'],'reason':d['reason'],
                    **{k:d.get('visual_evidence',{}).get(k,'') for k in fields[-3:]}} if False else
                    {'id':r['id'],'split':r['split'],'event':d['claim']['event'],'label':d['claim']['label'],
                     'sentence':d['claim']['sentence'],'action':d['action'],'reason':d['reason'],
                     **{k:d.get('visual_evidence',{}).get(k,'') for k in fields[-3:]}})
    edits=[r for r in results if r['changed']]
    with open(out/'manual_review.csv','w',newline='') as f:
        fields=['id','split','baseline','v2','deleted_sentences','human_edit_correct','human_notes']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in edits:
            writer.writerow({'id':r['id'],'split':r['split'],'baseline':r['baseline'],'v2':r['v2'],
               'deleted_sentences':' | '.join(d['claim']['sentence'] for d in r['decisions'] if d['action']=='drop')})
    for i,r in enumerate(edits):
        sheet=Image.new('RGB',(1200,1100),'white');draw=ImageDraw.Draw(sheet)
        for side,rel in enumerate(r['images']):
            pil=Image.open(imgroot/rel).convert('RGB');pil.thumbnail((580,580));sheet.paste(pil,(side*600,30))
        y=620
        for label,cap in [('BASELINE',r['baseline']),('V2',r['v2']),('REF',' | '.join(r['references']))]:
            lines=textwrap.wrap(label+': '+cap,width=160)
            draw.multiline_text((8,y),'\n'.join(lines),fill='black',spacing=3);y+=len(lines)*14+16
        sheet.save(out/f'edit_{i+1}_{r["id"]}.jpg',quality=95)
    report=['# M3Diff + LocateAnything — Minimal caption verifier V2','',
      f'24 development pairs; {sum(len(r["decisions"]) for r in results)} eligible event clauses; {len(edits)} captions changed.',
      'No full-caption rewrite. A/B detections + reliable SIFT alignment + unique corresponding box + SSIM/edge checks required for deletion.',
      'All other sentences retained. No detection is treated as uncertainty, not absence. If every sentence would be removed, abstain.',
      'This rule is still a heuristic; human review of every edit is required. Same development subset as V1; not held-out improvement evidence.','',
      '|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|','|---|---|---:|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm,s in arms.items():report.append(f"|{split}|{arm}|{s['Bleu_4']*100:.2f}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    report+=['','Scores computed on the same 12-pair subsets as V1; CIDEr document frequency is subset-specific.',
       'No attributes/pose/OCR repair and no replacement phrase generation. Low coverage is expected from conservative abstention.',
       'Only checking object categories mentioned in supported event sentences cannot recover all omitted changes.']
    (out/'REPORT.md').write_text('\n'.join(report))
    save(out/'SUCCESS.json',{'n_pairs':24,'n_edits':len(edits),'metrics':metrics})
    with zipfile.ZipFile(out/'caption_verifier_v2.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    volume.commit();print('METRICS',json.dumps(metrics),flush=True);print('DONE edits=',len(edits),flush=True)


@app.local_entrypoint()
def main(mode: str='check'):
    if mode=='attributes':attribute_check.remote()
    elif mode=='check':verify.remote()
    else:raise ValueError('mode must be check or attributes')


@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=1800,
              volumes={'/mnt/m3diff':volume})
def attribute_check():
    import sys,os,json,re,hashlib,subprocess,zipfile,textwrap,gc
    import numpy as np
    from PIL import Image,ImageDraw,ImageOps
    sys.path.insert(0,'/root')
    from caption_verifier import align_pair,stable_region
    root=Path('/mnt/m3diff');prior=root/'caption_verifier_v2';v1=root/'grounded_caption_pilot_v1'
    out=root/'caption_verifier_attributes_v3';out.mkdir(exist_ok=True)
    plans=json.loads((prior/'claim_plan.json').read_text())
    cache=json.loads((v1/'grounding_cache.json').read_text());cache.update(json.loads((prior/'grounding_cache.json').read_text()))
    colors=['black','white','gray','red','orange','yellow','green','blue','purple','brown','pink']
    def save(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    def key(rel,label):return hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
    results=[];candidates=[]
    for item in plans:
        entry={k:item[k] for k in ['id','split','images','baseline','grounded']}
        entry.update(v3=item['baseline'],changed=False,checks=[]);results.append(entry)
        pil=[]
        for rel in item['images']:
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((768,768));pil.append(p)
        arrays=[np.array(p) for p in pil]
        alignment,h=align_pair(*arrays) if item['claims'] else ({'ok':False},None)
        if not alignment['ok']:continue
        for claim in item['claims']:
            obs=[cache[key(rel,claim['label'])] for rel in item['images']]
            if any(not o['format_ok'] or len(o['boxes'])!=1 for o in obs):continue
            info=stable_region(*arrays,h,obs[0]['boxes'],obs[1]['boxes'])
            if info.get('aligned_box_iou',0)<.80:continue
            # A colored subject, not a color in a location phrase or another object's description.
            head=re.split(r'\b(?:on|in|at|near|beside|above|below|behind|with|wearing|that|which|to|of)\b',claim['sentence'],1,flags=re.I)[0]
            mentioned=set(re.findall(r'\b(?:'+'|'.join(colors)+r')\b',head,re.I))
            if len(mentioned)!=1:continue
            crops=[]
            for p,o,side in zip(pil,obs,['A','B']):
                x1,y1,x2,y2=o['boxes'][0];x1,x2=x1*p.width/1000,x2*p.width/1000;y1,y2=y1*p.height/1000,y2*p.height/1000
                dx,dy=(x2-x1)*.10,(y2-y1)*.10
                crop=p.crop((max(0,int(x1-dx)),max(0,int(y1-dy)),min(p.width,int(x2+dx)),min(p.height,int(y2+dy))))
                scale=448/max(crop.size)
                crop=crop.resize((max(56,round(crop.width*scale)),max(56,round(crop.height*scale))))
                crop.save(out/f"{item['id']}_{claim['label'].replace(' ','_')}_{side}_crop.png")
                crops.append(crop)
            candidates.append((item,entry,claim,info,crops,next(iter(mentioned)).lower()))
    save('candidate_plan.json',[{'id':i['id'],'claim':c,'geometry':g,'draft_subject_color':col} for i,e,c,g,cr,col in candidates])
    save('run_config.json',{'method':'Minimal clause replacement only after all-instance color-conditioned grounding of matched object crops in both images.',
       'colors':colors,'candidate_rule':'Unique valid generic detections in both images; reliable global alignment; aligned IoU>=.80; exactly one color in draft subject.',
       'acceptance':'Exactly one positive color in each crop; colors differ; draft color matches the time-side of the event.',
       'limits':'Same development cases as V1/V2; includes known ladder failure. Not held-out evidence. Geometry does not establish physical identity perfectly; this prototype can confuse replacement with recoloring.',
       'n_candidates':len(candidates),'n_pairs':24})
    volume.commit();print('COLOR CANDIDATES',len(candidates),flush=True)
    if candidates:
        os.environ['HF_HOME']=str(root/'locateanything_cache/hf');os.environ['HF_HUB_DISABLE_XET']='1'
        import torch
        from transformers import AutoTokenizer,AutoProcessor,AutoModel
        mp=root/'locateanything_cache/model'
        tokenizer=AutoTokenizer.from_pretrained(mp,trust_remote_code=True)
        processor=AutoProcessor.from_pretrained(mp,trust_remote_code=True)
        model=AutoModel.from_pretrained(mp,torch_dtype=torch.bfloat16,attn_implementation='sdpa',trust_remote_code=True).cuda().eval()
        try:
            for item,entry,claim,geo,crops,draft_color in candidates:
                observations=[]
                for crop,side in zip(crops,['A','B']):
                    prompt='Locate all the instances that matches the following description: '+ '</c>'.join(c+' '+claim['label'] for c in colors)+'.'
                    msgs=[{'role':'user','content':[{'type':'image','image':crop},{'type':'text','text':prompt}]}]
                    text=processor.py_apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
                    ims,vid=processor.process_vision_info(msgs);inp=processor(text=[text],images=ims,videos=vid,return_tensors='pt').to('cuda')
                    torch.manual_seed(42)
                    with torch.inference_mode():
                        response=model.generate(pixel_values=inp['pixel_values'].to(torch.bfloat16),input_ids=inp['input_ids'],
                            attention_mask=inp['attention_mask'],image_grid_hws=inp.get('image_grid_hws'),tokenizer=tokenizer,
                            max_new_tokens=8192,use_cache=True,generation_mode='hybrid',temperature=.7,do_sample=True,
                            top_p=.9,repetition_penalty=1.1,verbose=False)
                    answer=response[0] if isinstance(response,tuple) else response
                    positives=[]
                    for ref,body in re.findall(r'<ref>(.*?)</ref>(.*?)(?=<ref>|$)',answer,re.S):
                        boxes=[list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',body)]
                        color=next((c for c in colors if ref.strip().lower()==c+' '+claim['label']),None)
                        if color and any(all(0<=v<=1000 for v in b) and b[2]>b[0] and b[3]>b[1] for b in boxes):
                            positives.append(color)
                    obs={'side':side,'positive_colors':sorted(set(positives)),'raw':answer,'prompt':prompt}
                    observations.append(obs);print('COLOR',item['id'],side,obs,flush=True)
                check={'claim':claim,'geometry':geo,'color_observations':observations,'action':'keep'}
                a,b=[o['positive_colors'] for o in observations]
                if len(a)==len(b)==1 and a[0]!=b[0] and draft_color==(a[0] if claim['event']=='removed' else b[0]):
                    replacement=f"The {claim['label']} has changed from {a[0]} to {b[0]}."
                    sentences=list(item['sentences']);sentences[claim['sentence_index']]=replacement
                    entry.update(v3=' '.join(sentences),changed=True)
                    check.update(action='replace',replacement=replacement)
                entry['checks'].append(check)
                save('comparison.json',results);volume.commit()
        finally:
            del model,tokenizer,processor;gc.collect();torch.cuda.empty_cache()
    save('comparison.json',results)
    metrics=json.loads((prior/'metrics.json').read_text())
    for split in ['Real','Render']:
        pred=out/f'{split}_v3.jsonl';pred.write_text(''.join(json.dumps({'id':r['id'],'image_id':r['id'],'caption':r['v3']})+'\n' for r in results if r['split']==split))
        score=out/f'{split}_v3_scores.json'
        subprocess.run([sys.executable,str(root/'baseline_reproduction_v1/code/score_baseline.py'),
             '--reference',str(v1/f'{split}_reference_subset.json'),'--prediction',str(pred),'--output',str(score)],check=True)
        metrics[split]['v3']=json.loads(score.read_text())
    save('metrics.json',metrics)
    edits=[r for r in results if r['changed']]
    refs={r['id']:r['references'] for r in json.loads((v1/'comparison.json').read_text())}
    for i,r in enumerate(edits):
        sheet=Image.new('RGB',(1200,1100),'white');draw=ImageDraw.Draw(sheet)
        for side,rel in enumerate(r['images']):
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((580,580));sheet.paste(p,(side*600,30))
        y=620
        for label,cap in [('BASE',r['baseline']),('V3',r['v3']),('REF',' | '.join(refs[r['id']]))]:
            lines=textwrap.wrap(label+': '+cap,width=150);draw.multiline_text((8,y),'\n'.join(lines),fill='black',spacing=3);y+=len(lines)*14+16
        sheet.save(out/f'edit_{i+1}_{r["id"]}.jpg',quality=95)
    report=['# Minimal attribute verification V3 — development pilot','',f'24 pairs; {len(candidates)} candidates; {len(edits)} captions edited.',
      'M3Diff caption remains unchanged except a supported color-transition clause. No full rewrite.',
      'LocateAnything color-conditioned all-instance queries on matched crops are used to support the edit.',
      'This is still a heuristic. Developed on these same cases; do not call this held-out improvement.','',
      '|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|','|---|---|---:|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm in ['baseline','grounded','v2','v3']:
            s=arms[arm];report.append(f"|{split}|{arm}|{s['Bleu_4']*100:.2f}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    (out/'REPORT.md').write_text('\n'.join(report));save('SUCCESS.json',{'n_pairs':24,'n_edits':len(edits),'metrics':metrics})
    with zipfile.ZipFile(out/'caption_verifier_attributes_v3.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    volume.commit();print('DONE edits',len(edits),'METRICS',json.dumps(metrics),flush=True)
