"""CPU-only structural checker refinement; reuses all stored LocateAnything predictions."""
from pathlib import Path
import modal
app=modal.App('m3diff-caption-verifier-v21-cpu')
vol=modal.Volume.from_name('m3diff',create_if_missing=False)
image=(modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless')
       .pip_install('numpy==1.25.0','Pillow==11.1.0','opencv-python-headless==4.11.0.86',
                    'pycocoevalcap==1.2','pycocotools')
       .add_local_file(str(Path(__file__).with_name('caption_verifier.py')),'/root/caption_verifier.py',copy=True))

@app.function(image=image,cpu=4,memory=8192,timeout=900,volumes={'/mnt/m3diff':vol})
def check():
    import sys,json,hashlib,csv,subprocess,zipfile,textwrap
    import numpy as np
    from PIL import Image,ImageDraw
    sys.path.insert(0,'/root')
    from caption_verifier import align_pair,stable_region,minimally_filter
    root=Path('/mnt/m3diff');old=root/'caption_verifier_v2';v1=root/'grounded_caption_pilot_v1'
    out=root/'caption_verifier_v21';out.mkdir(exist_ok=True)
    plan=json.loads((old/'claim_plan.json').read_text())
    cache=json.loads((v1/'grounding_cache.json').read_text())
    cache.update(json.loads((old/'grounding_cache.json').read_text()))
    def key(rel,label):return hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
    def save(name,data):(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    # Independent stress controls for the color-tolerant rule, before reading references.
    sample=np.array(Image.open(root/'locateanything_demo_v1/real_before_box_input.png').convert('RGB'))
    box=[[712,0,998,169]]
    color=sample.copy();roi=color[:130,540:].astype(np.float32);color[:130,540:]=np.clip(roi*.7+20,0,255).astype(np.uint8)
    assert stable_region(sample,sample,np.eye(3),box,box,True)['stable']
    assert stable_region(sample,color,np.eye(3),box,box,True)['stable']
    removed=sample.copy();removed[:130,540:]=120
    assert not stable_region(sample,removed,np.eye(3),box,box,True)['stable']
    assert not stable_region(sample,sample,np.eye(3),box*2,box*2,True)['stable']
    print('PASS same/photometric-change/removed-region/multiple-instance controls',flush=True)
    results=[]
    for item in plan:
        ims=[]
        for rel in item['images']:
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((768,768));ims.append(np.array(p))
        alignment,h=align_pair(*ims) if item['claims'] else ({'ok':False,'reason':'no eligible claims'},None)
        decisions=[]
        for claim in item['claims']:
            oa,ob=[cache[key(rel,claim['label'])] for rel in item['images']]
            d={'claim':claim,'action':'keep','reason':'abstain'}
            if not alignment['ok']:d['reason']='unreliable alignment'
            elif not oa['format_ok'] or not ob['format_ok']:d['reason']='invalid grounding output'
            elif not oa['boxes'] or not ob['boxes']:d['reason']='missing detections are inconclusive'
            else:
                e=stable_region(*ims,h,oa['boxes'],ob['boxes'],True);d['visual_evidence']=e
                if e['stable']:d.update(action='drop',reason='unique region persists under reliable alignment and structural/visual checks')
                else:d['reason']=e['reason']
            decisions.append(d)
        cap=minimally_filter(item['sentences'],decisions)
        results.append({k:item[k] for k in ['id','split','images','baseline','control','grounded']})
        results[-1].update(v21=cap,changed=cap!=item['baseline'],decisions=decisions,alignment=alignment)
        print(item['id'],'EDIT',results[-1]['changed'],[(d['claim']['label'],d['action'],d.get('visual_evidence',{})) for d in decisions],flush=True)
    save('comparison.json',results)
    config=json.loads((old/'run_config.json').read_text())
    config.update(version='2.1',cpu_only=True,extra_grounding_queries=0,
                  structural_rule={'min_box_iou':.80,'min_ssim':.50,'min_edge_f1':.85,'min_bidirectional_edge_match':.80,'edge_tolerance_pixels':2.},
                  caveat='Refinement on development cases, including a known ladder color-change case. Not held-out evidence.')
    save('run_config.json',config);vol.commit()
    metrics=json.loads((old/'metrics.json').read_text())
    for split in ['Real','Render']:
        pred=out/f'{split}_v21.jsonl'
        pred.write_text(''.join(json.dumps({'id':r['id'],'image_id':r['id'],'caption':r['v21']})+'\n' for r in results if r['split']==split))
        score=out/f'{split}_v21_scores.json'
        subprocess.run([sys.executable,str(root/'baseline_reproduction_v1/code/score_baseline.py'),
                        '--reference',str(v1/f'{split}_reference_subset.json'),'--prediction',str(pred),'--output',str(score)],check=True)
        metrics[split]['v21']=json.loads(score.read_text())
    save('metrics.json',metrics)
    refs=json.loads((v1/'comparison.json').read_text());refs={r['id']:r['references'] for r in refs}
    edits=[r for r in results if r['changed']]
    for i,r in enumerate(edits):
        sheet=Image.new('RGB',(1200,1100),'white');draw=ImageDraw.Draw(sheet)
        for side,rel in enumerate(r['images']):
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((580,580));sheet.paste(p,(side*600,30))
        y=620
        for label,cap in [('BASE',r['baseline']),('V2.1',r['v21']),('REF',' | '.join(refs[r['id']]))]:
            lines=textwrap.wrap(label+': '+cap,width=150)
            draw.multiline_text((8,y),'\n'.join(lines),fill='black',spacing=3);y+=14*len(lines)+16
        sheet.save(out/f'edit_{i+1}_{r["id"]}.jpg',quality=95)
    report=['# Caption verifier V2.1 — development pilot','',f'24 pairs; {len(edits)} captions changed. Reused all detector outputs; CPU-only refinement.',
      'Baseline retained except eligible added/removed sentences contradicted by unique region persistence.',
      'Structural edge persistence handles some photometric/color changes that strict pixel checks rejected.',
      'Developed on these same cases, not held-out validation. Only manual inspection can assess whether edits are correct.','',
      '|Split|Arm|METEOR x100|ROUGE-L x100|CIDEr x100|','|---|---|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm in ['baseline','grounded','v2','v21']:
            s=arms[arm];report.append(f"|{split}|{arm}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    (out/'REPORT.md').write_text('\n'.join(report))
    save('SUCCESS.json',{'n_pairs':24,'n_edits':len(edits),'metrics':metrics})
    with zipfile.ZipFile(out/'caption_verifier_v21.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    vol.commit();print('DONE edits',len(edits),'METRICS',json.dumps(metrics),flush=True)

@app.local_entrypoint()
def main(mode: str='structure'):
    if mode=='color':color_pixels.remote()
    elif mode=='structure':check.remote()
    else:raise ValueError('mode must be structure or color')


@app.function(image=image,cpu=4,memory=8192,timeout=900,volumes={'/mnt/m3diff':vol})
def color_pixels():
    import sys,json,hashlib,re,subprocess,zipfile,textwrap
    import numpy as np
    from PIL import Image,ImageDraw
    sys.path.insert(0,'/root')
    from caption_verifier import align_pair,stable_region,verify_color_transition
    root=Path('/mnt/m3diff');v1=root/'grounded_caption_pilot_v1';v2=root/'caption_verifier_v2'
    out=root/'caption_verifier_color_v4';out.mkdir(exist_ok=True)
    plans=json.loads((v2/'claim_plan.json').read_text());cache=json.loads((v1/'grounding_cache.json').read_text())
    cache.update(json.loads((v2/'grounding_cache.json').read_text()))
    def key(rel,label):return hashlib.sha256((rel+'\n'+label).encode()).hexdigest()
    def save(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    results=[]
    for item in plans:
        ims=[]
        for rel in item['images']:
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((768,768));ims.append(np.array(p))
        alignment,h=align_pair(*ims) if item['claims'] else ({'ok':False},None)
        sentences=list(item['sentences']);checks=[]
        for claim in item['claims']:
            oa,ob=[cache[key(rel,claim['label'])] for rel in item['images']]
            d={'claim':claim,'action':'keep'};checks.append(d)
            if not alignment['ok'] or any(not o['format_ok'] or len(o['boxes'])!=1 for o in [oa,ob]):continue
            e=stable_region(*ims,h,oa['boxes'],ob['boxes']);d['geometry']=e
            if e.get('aligned_box_iou',0)<.80 or 'box_a' not in e:continue
            head=re.split(r'\b(?:on|in|at|near|beside|above|below|behind|with|wearing|that|which|to|of)\b',claim['sentence'],1,flags=re.I)[0]
            colors=set(re.findall(r'\b(?:red|orange|yellow|green|blue|purple|pink|brown)\b',head,re.I))
            if len(colors)!=1 or claim['event']!='removed':continue
            color=next(iter(colors)).lower()
            proof=verify_color_transition(*ims,h,e['box_a'],e['box_b_aligned'],color);d['color_check']=proof
            # Identical images must never yield a color-change edit.
            assert not verify_color_transition(ims[0],ims[0],np.eye(3),e['box_a'],e['box_a'],color)['supported']
            if proof['supported']:
                replacement=f"The {claim['label']} has changed from {proof['source_color']} to {proof['target_color']}."
                sentences[claim['sentence_index']]=replacement;d.update(action='replace',replacement=replacement)
            print('COLOR PIXELS',item['id'],d,flush=True)
        entry={k:item[k] for k in ['id','split','images','baseline','grounded']}
        caption=' '.join(sentences);entry.update(v4=caption,changed=caption!=item['baseline'],checks=checks)
        results.append(entry)
    save('comparison.json',results)
    save('run_config.json',{'method':'LocateAnything unique generic detections + reliable global geometry + matched-pixel color evidence; only removed->color-change clause replacement.',
      'rules':{'min_aligned_iou':.80,'min_source_interior_pixels':30,'min_target_color_fraction':.80,'source_mask_erosion':3},
      'limits':'24 development pairs reused, including known ladder failure. No independent generalization claim. Palette is coarse; illumination/occlusion can confound color. Same-class substitution not fully resolved.'})
    vol.commit()
    metrics=json.loads((v2/'metrics.json').read_text())
    for split in ['Real','Render']:
        pred=out/f'{split}_v4.jsonl';pred.write_text(''.join(json.dumps({'id':r['id'],'image_id':r['id'],'caption':r['v4']})+'\n' for r in results if r['split']==split))
        score=out/f'{split}_v4_scores.json'
        subprocess.run([sys.executable,str(root/'baseline_reproduction_v1/code/score_baseline.py'),
            '--reference',str(v1/f'{split}_reference_subset.json'),'--prediction',str(pred),'--output',str(score)],check=True)
        metrics[split]['v4']=json.loads(score.read_text())
    save('metrics.json',metrics)
    edits=[r for r in results if r['changed']]
    refs={r['id']:r['references'] for r in json.loads((v1/'comparison.json').read_text())}
    for i,r in enumerate(edits):
        sheet=Image.new('RGB',(1200,1100),'white');draw=ImageDraw.Draw(sheet)
        for side,rel in enumerate(r['images']):
            p=Image.open(root/'baseline_cache/OmniDiff'/rel).convert('RGB');p.thumbnail((580,580));sheet.paste(p,(side*600,30))
        y=620
        for label,cap in [('BASE',r['baseline']),('V4',r['v4']),('REF',' | '.join(refs[r['id']]))]:
            lines=textwrap.wrap(label+': '+cap,width=150);draw.multiline_text((8,y),'\n'.join(lines),fill='black',spacing=3);y+=len(lines)*14+16
        sheet.save(out/f'edit_{i+1}_{r["id"]}.jpg',quality=95)
    report=['# Minimal caption color verifier V4','',f'24 development pairs; {len(edits)} captions edited.',
       'Locator supplies object regions; corresponding color pixels verify the replacement clause. No full-caption rewrite.',
       'Same development sample as earlier iterations. This is proof-of-concept, not held-out improvement evidence.','',
       '|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|','|---|---|---:|---:|---:|---:|']
    for split,arms in metrics.items():
        for arm in ['baseline','grounded','v2','v4']:
            s=arms[arm];report.append(f"|{split}|{arm}|{s['Bleu_4']*100:.2f}|{s['METEOR']*100:.2f}|{s['ROUGE_L']*100:.2f}|{s['CIDEr']*100:.2f}|")
    (out/'REPORT.md').write_text('\n'.join(report));save('SUCCESS.json',{'n_pairs':24,'n_edits':len(edits),'metrics':metrics})
    with zipfile.ZipFile(out/'caption_verifier_color_v4.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    vol.commit();print('DONE edits',len(edits),'METRICS',json.dumps(metrics),flush=True)
