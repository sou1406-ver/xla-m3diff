"""Small NVIDIA LocateAnything-3B grounding demo on existing OmniDiff images."""
import modal

app = modal.App('locateanything-smoke-demo')
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


@app.function(image=image, gpu='A10', cpu=4, memory=32768,
              timeout=3600, volumes={'/mnt/m3diff': vol})
def demo():
    import os, json, time, re, zipfile, textwrap
    from pathlib import Path
    os.environ['HF_HOME'] = '/mnt/m3diff/locateanything_cache/hf'
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    import torch
    from PIL import Image, ImageDraw
    from huggingface_hub import HfApi, snapshot_download
    from transformers import AutoTokenizer, AutoProcessor, AutoModel

    root = Path('/mnt/m3diff')
    out = root / 'locateanything_demo_v1'
    out.mkdir(exist_ok=True)
    model_path = root / 'locateanything_cache/model'
    model_id = 'nvidia/LocateAnything-3B'
    revision = HfApi().model_info(model_id).sha
    print('Downloading model revision', revision, flush=True)
    snapshot_download(model_id, revision=revision, local_dir=model_path, max_workers=4)
    vol.commit()
    print('Loading LocateAnything BF16 / SDPA on', torch.cuda.get_device_name(0), flush=True)
    torch.manual_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, torch_dtype=torch.bfloat16,
                                     attn_implementation='sdpa', trust_remote_code=True).cuda().eval()

    repo = root / 'baseline_reproduction_v1/repo'
    img_root = root / 'baseline_cache/OmniDiff'
    real = json.loads((repo / 'data/evaluation/prompt/OmniDiff_Real_test.json').read_text())[0]
    render = json.loads((repo / 'data/evaluation/prompt/OmniDiff_Render_test.json').read_text())[0]
    cases = [
        ('real_before_box', real['image'][0], 'Locate a single instance that matches the following description: the green storage box.'),
        ('real_after_box', real['image'][1], 'Locate a single instance that matches the following description: the green storage box.'),
        ('real_before_objects', real['image'][0], 'Locate all the instances that matches the following description: storage box</c>cabinet.'),
        ('render_people', render['image'][0], 'Locate all the instances that matches the following description: person.'),
    ]
    results = []
    try:
        for name, rel, prompt in cases:
            start = time.time()
            pil = Image.open(img_root / rel).convert('RGB')
            original_size = pil.size
            pil.thumbnail((768, 768))  # bound SDPA memory for this small smoke test
            pil.save(out / f'{name}_input.png')
            messages = [{'role': 'user', 'content': [
                {'type': 'image', 'image': pil}, {'type': 'text', 'text': prompt}]}]
            text = processor.py_apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            images, videos = processor.process_vision_info(messages)
            inputs = processor(text=[text], images=images, videos=videos, return_tensors='pt').to('cuda')
            torch.cuda.reset_peak_memory_stats()
            with torch.inference_mode():
                response = model.generate(
                    pixel_values=inputs['pixel_values'].to(torch.bfloat16),
                    input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'],
                    image_grid_hws=inputs.get('image_grid_hws'), tokenizer=tokenizer,
                    max_new_tokens=8192, use_cache=True, generation_mode='hybrid',
                    temperature=0.7, do_sample=True, top_p=0.9,
                    repetition_penalty=1.1, verbose=True)
            answer = response[0] if isinstance(response, tuple) else response
            if not isinstance(answer, str):
                raise TypeError(f'Unexpected response: {type(answer)}')
            boxes = []
            for match in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>', answer):
                coords = list(map(int, match.groups()))
                refs = re.findall(r'<ref>(.*?)</ref>', answer[:match.start()], flags=re.S)
                boxes.append({'label': refs[-1] if refs else 'object', 'normalized_1000': coords,
                              'pixels': [coords[0]*pil.width/1000, coords[1]*pil.height/1000,
                                         coords[2]*pil.width/1000, coords[3]*pil.height/1000]})
            record = {'name': name, 'source_image': rel, 'prompt': prompt,
                      'original_size': original_size, 'inference_size': pil.size,
                      'answer': answer, 'boxes': boxes, 'seconds': time.time()-start,
                      'peak_vram_gb': torch.cuda.max_memory_allocated()/2**30}
            results.append(record)
            canvas = pil.copy()
            draw = ImageDraw.Draw(canvas)
            palette = ['#ff3030', '#00a0ff', '#00cc60', '#e08000']
            for i, box in enumerate(boxes):
                xy = box['pixels']
                if xy[2] >= xy[0] and xy[3] >= xy[1]:
                    draw.rectangle(xy, outline=palette[i % len(palette)], width=3)
                    draw.text((max(0,xy[0]), max(0,xy[1]-14)), f"{i+1}: {box['label']}",
                              fill=palette[i % len(palette)])
            canvas.save(out / f'{name}_boxes.png')
            (out / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
            vol.commit()
            print(name, 'boxes=', len(boxes), 'answer=', answer, flush=True)
        manifest = {'model': model_id, 'revision': revision, 'torch': torch.__version__,
                    'gpu': torch.cuda.get_device_name(0), 'dtype': 'bfloat16',
                    'attention': 'sdpa', 'max_image_side': 768, 'seed': 42,
                    'generation_mode': 'hybrid', 'max_new_tokens': 8192,
                    'note': 'Small qualitative demo; no ground-truth localization metrics.'}
        (out / 'run_config.json').write_text(json.dumps(manifest, indent=2))
        report = ['# NVIDIA LocateAnything-3B: thử định vị trên OmniDiff', '',
                  'Thử định tính trên 4 truy vấn; chưa phải benchmark hoặc phép đo cải thiện M3Diff.', '']
        for r in results:
            report += [f"## {r['name']}", r['prompt'], '', f"Số box: {len(r['boxes'])}; thời gian: {r['seconds']:.2f}s.",
                       '', r['answer'], '', f"![Result]({r['name']}_boxes.png)", '']
        (out / 'REPORT.md').write_text('\n'.join(report))
        with zipfile.ZipFile(out / 'locateanything_demo.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for p in out.iterdir():
                if p.is_file() and p.suffix != '.zip':
                    z.write(p, p.name)
        print('DONE:', out, flush=True)
    finally:
        vol.commit()


@app.local_entrypoint()
def main(mode: str = 'demo'):
    if mode == 'robustness':
        robustness.remote()
    elif mode == 'demo':
        demo.remote()
    else:
        raise ValueError('mode must be demo or robustness')


@app.function(image=image, gpu='A10', cpu=4, memory=32768,
              timeout=1800, volumes={'/mnt/m3diff': vol})
def robustness():
    import os, json, time, re, zipfile, csv
    from pathlib import Path
    os.environ['HF_HOME'] = '/mnt/m3diff/locateanything_cache/hf'
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    import torch
    from PIL import Image, ImageDraw, ImageOps
    from transformers import AutoTokenizer, AutoProcessor, AutoModel
    root = Path('/mnt/m3diff')
    previous = root / 'locateanything_demo_v1'
    out = root / 'locateanything_robustness_v1'
    out.mkdir(exist_ok=True)
    model_path = root / 'locateanything_cache/model'
    before = Image.open(previous / 'real_before_box_input.png').convert('RGB')
    after = Image.open(previous / 'real_after_box_input.png').convert('RGB')
    render = Image.open(previous / 'render_people_input.png').convert('RGB')
    w, h = before.size
    zoom = before.crop((round(.5*w), 0, w, round(.5*h))).resize(before.size)
    scaled = Image.new('RGB', before.size, (128,128,128))
    tiny = before.resize((round(.6*w), round(.6*h)))
    scaled.paste(tiny, ((w-tiny.width)//2, (h-tiny.height)//2))
    floor = before.crop((0, round(.56*h), w, h))
    lower = before.crop((0, round(.24*h), w, h))
    cases = [
        ('original_single', before.copy(), True, 'Original image', 'single'),
        ('oblique_real', after, True, 'Actual second photograph; target partly near image edge', 'single'),
        ('rotate_cw15', before.rotate(-15, expand=True, fillcolor=(128,128,128)), True, 'Synthetic 2D rotation clockwise 15 deg', 'single'),
        ('rotate_ccw30', before.rotate(30, expand=True, fillcolor=(128,128,128)), True, 'Synthetic 2D rotation counterclockwise 30 deg', 'single'),
        ('zoom_on_target', zoom, True, 'Synthetic crop of upper-right quadrant, resized', 'single'),
        ('scale_down_60', scaled, True, 'Synthetic 60% rescale with gray padding; not a real camera zoom-out', 'single'),
        ('resolution_384', before.resize((384,384)), True, 'Reduced input resolution', 'single'),
        ('floor_single', floor.copy(), False, 'Floor-only crop; storage box excluded', 'single'),
        ('lower_scene_single', lower.copy(), False, 'Lower scene crop; storage box excluded', 'single'),
        ('street_negative', render, False, 'Street scene with no green storage box', 'single'),
        ('original_all', before.copy(), True, 'Original image; all-instance prompt', 'all'),
        ('floor_all', floor.copy(), False, 'Floor-only crop; all-instance prompt', 'all'),
        ('lower_scene_all', lower.copy(), False, 'Lower scene crop; all-instance prompt', 'all'),
    ]
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, torch_dtype=torch.bfloat16,
                                     attn_implementation='sdpa', trust_remote_code=True).cuda().eval()
    results = []
    try:
        for name, pil, present, note, style in cases:
            pil.thumbnail((768,768))
            prompt = ('Locate a single instance that matches the following description: the green storage box.'
                      if style == 'single' else
                      'Locate all the instances that match the following description: the green storage box.')
            torch.manual_seed(42)
            messages = [{'role':'user','content':[{'type':'image','image':pil},{'type':'text','text':prompt}]}]
            text = processor.py_apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            images, videos = processor.process_vision_info(messages)
            inputs = processor(text=[text], images=images, videos=videos, return_tensors='pt').to('cuda')
            start = time.time()
            with torch.inference_mode():
                response = model.generate(pixel_values=inputs['pixel_values'].to(torch.bfloat16),
                    input_ids=inputs['input_ids'], attention_mask=inputs['attention_mask'],
                    image_grid_hws=inputs.get('image_grid_hws'), tokenizer=tokenizer,
                    max_new_tokens=8192, use_cache=True, generation_mode='hybrid',
                    temperature=.7, do_sample=True, top_p=.9, repetition_penalty=1.1, verbose=True)
            answer = response[0] if isinstance(response, tuple) else response
            assert isinstance(answer,str), type(answer)
            boxes = [list(map(int,m.groups())) for m in re.finditer(r'<box><(\d+)><(\d+)><(\d+)><(\d+)></box>',answer)]
            pil.save(out / f'{name}_input.png')
            annotated = pil.copy()
            draw = ImageDraw.Draw(annotated)
            for i,b in enumerate(boxes):
                xy = [b[0]*pil.width/1000,b[1]*pil.height/1000,b[2]*pil.width/1000,b[3]*pil.height/1000]
                if xy[2]>=xy[0] and xy[3]>=xy[1]:
                    draw.rectangle(xy,outline='red',width=3)
                    draw.text((xy[0],max(0,xy[1]-12)),f'box {i+1}',fill='red')
            annotated.save(out / f'{name}_boxes.png')
            results.append({'name':name,'target_present':present,'note':note,'prompt_style':style,
                            'prompt':prompt,'size':pil.size,'boxes_1000':boxes,'answer':answer,
                            'seconds':time.time()-start,
                            'negative_false_positive': (bool(boxes) if not present else None)})
            (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
            vol.commit()
            print(name, 'present=',present,'boxes=',len(boxes),'answer=',answer,flush=True)
        fields=['name','target_present','prompt_style','n_boxes','seconds','negative_false_positive']
        with open(out/'summary.csv','w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
            for r in results:
                writer.writerow({**{k:r[k] for k in fields if k!='n_boxes'},'n_boxes':len(r['boxes_1000'])})
        # Render a contact sheet without inventing labels for localization correctness.
        tile_w,tile_h=390,450
        sheet=Image.new('RGB',(tile_w*3,tile_h*((len(results)+2)//3)),'white')
        d=ImageDraw.Draw(sheet)
        for i,r in enumerate(results):
            x,y=(i%3)*tile_w,(i//3)*tile_h
            tile=ImageOps.contain(Image.open(out/f"{r['name']}_boxes.png"),(380,380))
            sheet.paste(tile,(x+(tile_w-tile.width)//2,y+55))
            d.text((x+8,y+6),r['name'],fill='black')
            d.text((x+8,y+24),f"target present: {r['target_present']} | boxes: {len(r['boxes_1000'])}",fill='black')
        sheet.save(out/'gallery.jpg',quality=92)
        cfg=json.loads((previous/'run_config.json').read_text())
        cfg.update({'seed_per_case':42,'n_queries':len(results),
                    'note':'Controlled qualitative test, one source scene plus two actual photos. No box ground truth or localization accuracy. 2D rotations do not model 3D viewpoint changes.'})
        (out/'run_config.json').write_text(json.dumps(cfg,indent=2))
        with zipfile.ZipFile(out/'locateanything_robustness.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in out.iterdir():
                if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
        print('DONE',out,flush=True)
    finally:
        vol.commit()
