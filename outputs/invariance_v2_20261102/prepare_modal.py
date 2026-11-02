from pathlib import Path
import modal

HERE = Path(__file__).parent
app = modal.App('m3diff-invariance-v2-prepare-20261102')
volume = modal.Volume.from_name('m3diff')
image = modal.Image.debian_slim(python_version='3.10').pip_install('Pillow==11.1.0').add_local_file(
    str(HERE/'PLAN.md'), '/root/PLAN.md', copy=True)

@app.function(image=image, cpu=4, memory=8192, timeout=900, volumes={'/mnt/m3diff':volume}, scaledown_window=2, retries=0)
def prepare():
    import copy, hashlib, json, math, random, zipfile
    from PIL import Image, ImageDraw, ImageEnhance
    root=Path('/mnt/m3diff'); out=root/'invariance_v2_20261102'; out.mkdir(exist_ok=True)
    def save(name, value):
        (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2))
    if (out/'PREPARED.json').exists():
        print((out/'PREPARED.json').read_text()); return
    (out/'PLAN.md').write_bytes(Path('/root/PLAN.md').read_bytes())
    old=json.loads((root/'invariance_ablation_v1/train.json').read_text())
    positive=[r for r in old if not r['is_invariance_negative']]; negative=[r for r in old if r['is_invariance_negative']]
    assert len(positive)==192 and len(negative)==64
    generated=out/'images'; generated.mkdir(exist_ok=True)
    boards=out/'boards'; boards.mkdir(exist_ok=True)
    def dh(path):
        with Image.open(path) as x:
            im=x.convert('RGB'); h=hashlib.sha256(); h.update(str(im.size).encode()); h.update(im.tobytes()); return h.hexdigest()
    def contained(im, angle, scale):
        w,h=im.size; rotated=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=(127,127,127))
        factor=min(w/rotated.width,h/rotated.height)*scale
        resized=rotated.resize((max(1,round(rotated.width*factor)),max(1,round(rotated.height*factor))),Image.Resampling.BICUBIC)
        canvas=Image.new('RGB',(w,h),(127,127,127)); canvas.paste(resized,((w-resized.width)//2,(h-resized.height)//2)); return canvas
    def output_image(im,name):
        p=generated/(name+'.png'); im.save(p); return p.relative_to(root).as_posix()
    def board(name, paths, caption=''):
        canvas=Image.new('RGB',(1400,570),'white'); draw=ImageDraw.Draw(canvas)
        for i,p in enumerate(paths):
            with Image.open(root/p) as original:
                im=original.convert('RGB'); im.thumbnail((680,470)); canvas.paste(im,(i*700+(680-im.width)//2,35+(470-im.height)//2))
            draw.text((i*700+10,8), name+(' BEFORE' if i==0 else ' AFTER'),fill='black')
        import textwrap
        draw.multiline_text((10,510),'\n'.join(textwrap.wrap(caption,185)[:4]),fill='black')
        canvas.save(boards/(name+'.jpg'),quality=92)
    control=[]
    for block in [positive,negative]:
        for repeat in range(2):
            for row in block:
                r=copy.deepcopy(row); r['id']=f'control_{repeat}_'+str(row['id']); control.append(r)
    revised=[copy.deepcopy(r) for r in positive]
    for i,row in enumerate(positive):
        r=copy.deepcopy(row); r['id']='positive_aug_'+str(i)
        angle=(-6,6,0)[i%3]; scale=.90 if i%3==2 else 1.
        r['image']=[output_image(contained(Image.open(root/p).convert('RGB'),angle,scale),f'positive_{i:03d}_{j}') for j,p in enumerate(row['image'])]
        r['conversations'][-1]['value']=row['conversations'][-1]['value'].rstrip()
        revised.append(r)
        if i<12: board(f'train_positive_{i:02d}',r['image'],r['conversations'][-1]['value'])
    label={
        'identity':'The two images are identical. No object, lighting, or viewpoint changes are visible.',
        'zoom_in_1p10':'The second image is a closer crop of the same scene. Objects in the shared area are unchanged; the image is not rotated and there is no lighting change.',
        'zoom_out_reverse_1p10':'The second image shows a wider framing of the same scene. Objects in the shared area are unchanged; the image is not rotated and there is no lighting change.',
        'roll_8_safe':'The second image is rotated with slightly different framing. Objects in the shared area are unchanged, and there is no lighting change.'}
    for row in negative:
        r=copy.deepcopy(row); condition=next(k for k in label if str(row['id']).endswith(k))
        r['conversations'][-1]['value']=label[condition]; revised.append(r)
    for i,row in enumerate(negative[:32]):
        r=copy.deepcopy(revised[384+i]); r['id']='negative_repeat_'+str(i); revised.append(r)
    sources=[]
    for row in negative:
        if str(row['id']).endswith('_identity'): sources.append(row['image'][0])
    assert len(sources)==16
    prompt="What's the difference between 2 images?  <image><image>Difference:"
    for i,src in enumerate(sources):
        for direction,factor in [('brighter',1.12),('darker',.88)]:
            path=output_image(ImageEnhance.Brightness(Image.open(root/src).convert('RGB')).enhance(factor),f'brightness_{i:02d}_{direction}')
            revised.append({'id':f'negative_brightness_{i}_{direction}','image':[src,path], 'is_invariance_negative':True,
                'conversations':[{'from':'human','value':prompt},{'from':'gpt','value':f'The second image is {direction}. The objects and image framing are unchanged.'}]})
            if i<2: board(f'train_brightness_{i}_{direction}',[src,path])
    assert len(control)==len(revised)==512
    assert sum(r['is_invariance_negative'] for r in revised)==128
    rng=random.Random(2026110201); order=list(range(512)); rng.shuffle(order)
    control=[control[i] for i in order]; revised=[revised[i] for i in order]
    save('train_control.json',control); save('train_revised.json',revised)
    # Exclude all previously used diagnostic / training images by decoded RGB.
    prior=[]
    for folder in ['invariance_sft_v1','invariance_confirmation_v1','invariance_ablation_v1']:
        for name in ['train.json','eval_questions.json']:
            p=root/folder/name
            if p.exists(): prior+=json.loads(p.read_text())
    excluded_paths={p for r in prior for p in r['image']} | {p for r in revised for p in r['image']}
    excluded=set()
    for i,p in enumerate(sorted(excluded_paths)):
        excluded.add(dh(root/p))
        if i%128==127: print('HASHED',i+1,flush=True)
    poolroot=root/'baseline_cache/OmniDiff'; repo=root/'baseline_reproduction_v1/repo'
    selected=[]; used=set(); rng=random.Random(2026110202)
    for domain in ['Real','Render']:
        pool=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{domain}_test.json').read_text()); rng.shuffle(pool); n=0
        for row in pool:
            hashes=[dh(poolroot/p) for p in row['image']]
            if len(set(hashes))!=2 or any(h in excluded or h in used for h in hashes): continue
            selected.append({'scene':f'v2_{domain}_{n:02d}','domain':domain,'original_id':row['id'],
                             'image':['baseline_cache/OmniDiff/'+p for p in row['image']], 'hashes':hashes})
            used.update(hashes); n+=1
            if n==8: break
        assert n==8, (domain,n)
    save('selection_locked.json',{'seed':2026110202,'selected':selected,'excluded_hashes':len(excluded),
                                'limits':'RGB-disjoint from prior inputs, not necessarily different background scenes.'})
    def cropped(im,angle=0,zoom=1.):
        w,h=im.size; t=math.radians(angle); c,s=math.cos(t),math.sin(t)
        scale=max(abs(c)+h/w*abs(s),abs(c)+w/h*abs(s))*(1.002 if angle else 1)*zoom
        a,b,d,e=c/scale,-s/scale,s/scale,c/scale
        return im.transform(im.size,Image.Transform.AFFINE,(a,b,w/2-a*w/2-b*h/2,d,e,h/2-d*w/2-e*h/2),resample=Image.Resampling.BICUBIC)
    questions=[]; meta=[]
    for row in selected:
        a,b=row['image']; src=Image.open(root/a).convert('RGB'); scene=row['scene']
        zoom=output_image(cropped(src,zoom=1.1),scene+'_zoom'); roll=output_image(cropped(src,angle=-8),scene+'_roll')
        bright=output_image(ImageEnhance.Brightness(src).enhance(1.12),scene+'_brightness')
        pairs=[('identity',[a,a]),('zoom_in',[a,zoom]),('zoom_out',[zoom,a]),('roll',[a,roll]),('brightness',[a,bright]),('natural',[a,b])]
        for condition,ims in pairs:
            rid=scene+'__'+condition; questions.append({'id':rid,'image':ims,'conversations':[{'from':'human','value':prompt}]})
            meta.append({'id':rid,'scene':scene,'domain':row['domain'],'condition':condition,'image':ims})
        board(scene,row['image'])
    save('eval_questions.json',questions); save('eval_manifest.json',meta)
    save('data_audit.json',{'train_records_each':512,'positive_each':384,'negative_each':128,'evaluation_pairs':len(questions),
        'evaluation_sources':16,'RGB_overlap_with_excluded':len(used & excluded),'model_captions_used':False,
        'train_hashes':{a:hashlib.sha256((out/f'train_{a}.json').read_bytes()).hexdigest() for a in ['control','revised']}})
    save('PREPARED.json',{'train_each':512,'eval_pairs':len(questions),'review_before_gpu':True})
    with zipfile.ZipFile(out/'preparation.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p.is_file() and p.suffix in ['.json','.md']: z.write(p,p.name)
        for p in boards.glob('*.jpg'): z.write(p,'boards/'+p.name)
    volume.commit(); print('PREPARATION COMPLETE; CPU released',flush=True)

@app.local_entrypoint()
def main(): prepare.remote()
