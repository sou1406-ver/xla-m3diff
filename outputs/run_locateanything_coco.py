"""Small paired single/all prompt diagnostic, using cached COCO val2017 labels."""
import modal
vol = modal.Volume.from_name('m3diff', create_if_missing=False)
image = (
    modal.Image.debian_slim(python_version='3.10')
    .pip_install('torch==2.6.0', 'torchvision==0.21.0',
                 'transformers==4.57.1', 'tokenizers==0.22.0',
                 'numpy==1.25.0', 'Pillow==11.1.0', 'peft==0.12.0',
                 'accelerate==1.5.2', 'opencv-python-headless==4.11.0.86',
                 'decord==0.6.0', 'lmdb==1.7.5', 'timm>=1.0.11',
                 'einops', 'sentencepiece')
)

app = modal.App('locateanything-coco-diagnostic')


@app.function(image=image, gpu='A10', cpu=4, memory=32768,
              timeout=1800, volumes={'/mnt/m3diff':vol})
def evaluate():
    import os, json, csv, re, time, zipfile, hashlib
    from collections import defaultdict
    from pathlib import Path
    os.environ['HF_HOME']='/mnt/m3diff/locateanything_cache/hf'
    os.environ['HF_HUB_DISABLE_XET']='1'
    import torch
    from PIL import Image, ImageDraw, ImageOps
    from transformers import AutoModel, AutoTokenizer, AutoProcessor

    root=Path('/mnt/m3diff')
    out=root/'locateanything_coco_v1'
    out.mkdir(exist_ok=True)
    ann_path=root/'synth/coco_cache/instances_val2017.json'
    img_root=root/'synth/coco_cache/val2017'
    if not ann_path.exists():
        raise FileNotFoundError(f'Expected existing annotations: {ann_path}')
    data=json.loads(ann_path.read_text())
    cats={c['name']:c['id'] for c in data['categories']}
    infos={i['id']:i for i in data['images']}
    anns=defaultdict(list)
    for a in data['annotations']:anns[a['image_id']].append(a)
    classes=['car','chair','dog','cat','bottle','cup']
    chosen=[]; used=set()
    for label in classes:
        candidates=[]
        for iid in sorted(anns):
            info=infos[iid]
            if iid in used or not (img_root/info['file_name']).exists():continue
            good=[a for a in anns[iid] if a['category_id']==cats[label] and not a['iscrowd']
                  and a['bbox'][2]>=60 and a['bbox'][3]>=60
                  and a['area']>=.01*info['width']*info['height']]
            if not good:continue
            # Crowded classes complicate an all-instance recall diagnostic: exclude this class/image.
            if any(a['category_id']==cats[label] and a['iscrowd'] for a in anns[iid]):continue
            present={a['category_id'] for a in anns[iid]}
            missing=[c for c in classes if cats[c] not in present]
            if not missing:continue
            candidates.append((iid,missing))
        for j,(iid,missing) in enumerate(candidates[:2]):
            chosen.append({'image_id':iid,'positive':label,'negative':missing[j%len(missing)]})
            used.add(iid)
    if len(chosen)!=12:
        raise RuntimeError(f'Need 2 cached images per class; found only {len(chosen)}. No GPU inference performed.')
    manifest=[]
    for item in chosen:
        iid=item['image_id']; info=infos[iid]
        for is_positive,label in [(True,item['positive']),(False,item['negative'])]:
            gt=[]
            for a in anns[iid]:
                if a['category_id']==cats[label] and not a['iscrowd']:
                    x,y,w,h=a['bbox'];gt.append([x,y,x+w,y+h])
            assert bool(gt)==is_positive
            for style in ['single','all']:
                manifest.append({'case_id':f'{iid}_{label}_{style}', 'image_id':iid,
                    'file_name':info['file_name'],'query':label,'positive':is_positive,
                    'style':style,'gt_boxes_original':gt,'original_size':[info['width'],info['height']]})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Protocol: 12 cached COCO images, 6 positive categories, 48 paired queries.',flush=True)
    vol.commit()
    model_path=root/'locateanything_cache/model'
    tokenizer=AutoTokenizer.from_pretrained(model_path,trust_remote_code=True)
    processor=AutoProcessor.from_pretrained(model_path,trust_remote_code=True)
    model=AutoModel.from_pretrained(model_path,torch_dtype=torch.bfloat16,
        attn_implementation='sdpa',trust_remote_code=True).cuda().eval()

    def iou(a,b):
        area=lambda z:max(0,z[2]-z[0])*max(0,z[3]-z[1])
        inter=area([max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])])
        return inter/max(1e-9,area(a)+area(b)-inter)

    rows=[]
    try:
        for ci,case in enumerate(manifest):
            pil=Image.open(img_root/case['file_name']).convert('RGB')
            pil.thumbnail((768,768))
            sx,sy=pil.width/case['original_size'][0],pil.height/case['original_size'][1]
            gt=[[b[0]*sx,b[1]*sy,b[2]*sx,b[3]*sy] for b in case['gt_boxes_original']]
            prompt=(f"Locate a single instance that matches the following description: {case['query']}."
                    if case['style']=='single' else
                    f"Locate all the instances that match the following description: {case['query']}.")
            torch.manual_seed(42)
            messages=[{'role':'user','content':[{'type':'image','image':pil},{'type':'text','text':prompt}]}]
            text=processor.py_apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            images,videos=processor.process_vision_info(messages)
            inputs=processor(text=[text],images=images,videos=videos,return_tensors='pt').to('cuda')
            start=time.time()
            with torch.inference_mode():
                resp=model.generate(pixel_values=inputs['pixel_values'].to(torch.bfloat16),
                    input_ids=inputs['input_ids'],attention_mask=inputs['attention_mask'],
                    image_grid_hws=inputs.get('image_grid_hws'),tokenizer=tokenizer,
                    max_new_tokens=8192,use_cache=True,generation_mode='hybrid',
                    temperature=.7,do_sample=True,top_p=.9,repetition_penalty=1.1,verbose=False)
            answer=resp[0] if isinstance(resp,tuple) else resp
            assert isinstance(answer,str)
            raw=[list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',answer)]
            valid=[b for b in raw if all(0<=v<=1000 for v in b) and b[2]>b[0] and b[3]>b[1]]
            pred=[[b[0]*pil.width/1000,b[1]*pil.height/1000,b[2]*pil.width/1000,b[3]*pil.height/1000] for b in valid]
            explicit_none=bool(re.search(r'<box>\s*None\s*</box>',answer,re.I))
            format_ok=(len(raw)==len(valid)) and bool(pred or explicit_none)
            best=max((iou(p,g) for p in pred for g in gt),default=0.)
            # Greedy one-to-one matching at IoU .5; useful coverage for all-instance output.
            pairs=sorted([(iou(p,g),pi,gi) for pi,p in enumerate(pred) for gi,g in enumerate(gt)],reverse=True)
            seen_p=set();seen_g=set()
            for ov,pi,gi in pairs:
                if ov>=.5 and pi not in seen_p and gi not in seen_g:
                    seen_p.add(pi);seen_g.add(gi)
            row={**case,'prompt':prompt,'inference_size':pil.size,'answer':answer,
                 'pred_boxes':pred,'gt_boxes':gt,'n_pred':len(pred),'n_gt':len(gt),
                 'format_ok':format_ok,'explicit_none':explicit_none,'best_iou':best,
                 'positive_hit_iou50':bool(best>=.5) if case['positive'] else None,
                 'negative_false_positive':bool(raw) if not case['positive'] else None,
                 'negative_correct_rejection':bool(format_ok and explicit_none and not pred) if not case['positive'] else None,
                 'matched_gt':len(seen_g),'seconds':time.time()-start}
            rows.append(row)
            canvas=pil.copy();draw=ImageDraw.Draw(canvas)
            for b in gt:draw.rectangle(b,outline='#00b040',width=3)
            for b in pred:draw.rectangle(b,outline='#ff2020',width=3)
            canvas.save(out/f"{case['case_id']}.jpg",quality=92)
            (out/'results.json').write_text(json.dumps(rows,indent=2))
            print(f"{ci+1}/48 {case['case_id']}: positive={case['positive']} pred={len(pred)} bestIoU={best:.3f} None={explicit_none}",flush=True)
            if (ci+1)%8==0:vol.commit()
        summary={}
        for style in ['single','all']:
            pos=[r for r in rows if r['style']==style and r['positive']]
            neg=[r for r in rows if r['style']==style and not r['positive']]
            summary[style]={'n_positive':len(pos),'positive_hits_iou50':sum(r['positive_hit_iou50'] for r in pos),
                'n_negative':len(neg),'negative_false_positives':sum(r['negative_false_positive'] for r in neg),
                'negative_correct_rejections':sum(r['negative_correct_rejection'] for r in neg),
                'format_errors':sum(not r['format_ok'] for r in pos+neg),
                'positive_best_iou_mean':sum(r['best_iou'] for r in pos)/len(pos)}
            if style=='all':
                summary[style]['gt_boxes']=sum(r['n_gt'] for r in pos)
                summary[style]['matched_gt_iou50']=sum(r['matched_gt'] for r in pos)
        (out/'summary.json').write_text(json.dumps(summary,indent=2))
        keys=['case_id','query','positive','style','n_pred','n_gt','best_iou',
              'positive_hit_iou50','negative_false_positive','negative_correct_rejection','format_ok','seconds']
        with open(out/'per_query.csv','w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
            writer.writerows({k:r[k] for k in keys} for r in rows)
        for page in range(4):
            subset=rows[page*12:(page+1)*12]
            sheet=Image.new('RGB',(1200,1200),'white');draw=ImageDraw.Draw(sheet)
            for j,r in enumerate(subset):
                x,y=(j%3)*400,(j//3)*300
                draw.text((x+5,y+4),f"{r['image_id']} {r['query']} / {r['style']}",fill='black')
                draw.text((x+5,y+20),f"GT={r['n_gt']} pred={r['n_pred']} bestIoU={r['best_iou']:.2f}",fill='black')
                tile=ImageOps.contain(Image.open(out/f"{r['case_id']}.jpg"),(390,250))
                sheet.paste(tile,(x+(400-tile.width)//2,y+45))
            sheet.save(out/f'gallery_{page+1}.jpg',quality=92)
        config=json.loads((root/'locateanything_demo_v1/run_config.json').read_text())
        config.update({'protocol':'First two eligible cached COCO val2017 images per selected class, sorted image_id, unique images, 12 positive and 12 negative image-query pairs, both single/all prompts.',
                       'annotation_sha256':hashlib.sha256(ann_path.read_bytes()).hexdigest(),
                       'classes':classes,'seed_per_query':42,
                       'limits':'Small diagnostic on convenience sample of cached images; COCO annotation absence is a proxy for true absence. Training overlap unknown. Not official benchmark reproduction or proof of M3Diff improvement.'})
        (out/'run_config.json').write_text(json.dumps(config,indent=2))
        with zipfile.ZipFile(out/'locateanything_coco.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in out.iterdir():
                if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
        print('SUMMARY',json.dumps(summary),flush=True)
        print('DONE',out,flush=True)
    finally:
        vol.commit()


@app.local_entrypoint()
def main():
    evaluate.remote()
