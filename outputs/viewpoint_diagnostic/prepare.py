"""Deterministic geometry-only controls, paired with previously reviewed real changes."""
from pathlib import Path
import hashlib,json,math,random,shutil
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'curated_sft'
selection=json.loads((OLD/'blind_image_selection.json').read_text())
observations=json.loads((OLD/'image_only_observations.json').read_text())
# One source pair per visually distinct scene. Scene labels are manually assigned.
chosen=[(0,'furniture','dev'),(1,'exercise','dev'),(2,'yoga','validation'),(5,'mouse','dev'),(6,'kitchen','validation'),(7,'silhouette','validation'),
        (8,'hospital','dev'),(9,'street','dev'),(10,'picnic','validation'),(11,'office','validation'),(12,'greenhouse','dev'),(13,'classroom','validation')]
baseline="What's the difference between 2 images?  <image><image>Difference:"
aware=("What's the difference between 2 images? <image><image> "
       "Compare corresponding objects while accounting for camera rotation, zoom, perspective, lighting, and cropping. "
       "An object moving in the frame or becoming cropped is not by itself evidence that it was added, removed, or physically moved. "
       "Describe supported scene changes; do not invent changes to unchanged objects. "
       "If only the camera view or framing changes, say so. Difference:")
manifest=[];images=ROOT/'dataset/images';images.mkdir(parents=True,exist_ok=True)
def save(name,obj):(ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def transform(im,angle,zoom):
    w,h=im.size;t=math.radians(angle);c,s=math.cos(t),math.sin(t)
    # Inverse affine is guaranteed to sample only inside the source rectangle.
    safe=max(abs(c)+h/w*abs(s),abs(c)+w/h*abs(s))*(1.002 if angle else 1)
    scale=safe*zoom
    a,b,d,e=c/scale,-s/scale,s/scale,c/scale
    x0=w/2-a*w/2-b*h/2;y0=h/2-d*w/2-e*h/2
    for x,y in [(0,0),(w,0),(0,h),(w,h)]:
        assert -1e-7<=a*x+b*y+x0<=w+1e-7 and -1e-7<=d*x+e*y+y0<=h+1e-7
    out=im.transform(im.size,Image.Transform.AFFINE,(a,b,x0,d,e,y0),resample=Image.Resampling.BICUBIC)
    return out,{'angle_degrees':angle,'requested_zoom':zoom,'actual_scale':scale,'output_to_input_affine':[a,b,x0,d,e,y0],'border_fill_samples':0}
for ix,scene,partition in chosen:
    q=selection[ix];im=Image.open(OLD/'blind_images/originals'/q['images'][0]).convert('RGB')
    src=f'images/{scene}_source.png';im.save(ROOT/'dataset'/src)
    for condition,angle,zoom in [('identity',0,1),('zoom_1p10',0,1.10),('roll_8_safe',8,1),('roll_minus8_zoom',-8,1.10)]:
        dst=f'images/{scene}_{condition}.png';trans,params=transform(im,angle,zoom)
        if condition=='identity':assert trans.tobytes()==im.tobytes()
        trans.save(ROOT/'dataset'/dst)
        manifest.append({'id':f'{scene}__{condition}','split':q['split'],'scene':scene,'partition':partition,'condition':condition,
          'image':[src,dst],'source_dataset_images':[q['images'][0]],'expected':'No physical object/state change in shared visible content. Global geometry/framing change allowed; cropping can hide content without removal.',
          'transform':params})
    dst=f'images/{scene}_positive.png';Image.open(OLD/'blind_images/originals'/q['images'][1]).convert('RGB').save(ROOT/'dataset'/dst)
    manifest.append({'id':f'{scene}__natural','split':q['split'],'scene':scene,'partition':partition,'condition':'natural',
       'image':[src,dst],'source_dataset_images':q['images'],'source_pair_id':q['id'],'image_only_observations':observations['observations'][ix],
       'expected':'Describe the visually reviewed changes without inventing other changes. Classroom is illumination-only, scored separately from physical-object positives.'})
assert len(manifest)==60 and len({r['scene'] for r in manifest})==12
for arm,prompt in [('baseline',baseline),('camera_aware',aware)]:
    questions=[{'id':r['id'],'image':r['image'],'conversations':[{'from':'human','value':prompt}]} for r in manifest]
    random.Random(2026102718).shuffle(questions);save(f'dataset/{arm}_questions.json',questions)
save('manifest.json',manifest);shutil.copy2(ROOT/'manifest.json',ROOT/'dataset/manifest.json')
lock={'version':1,'seed':2026102718,'source_pairs':12,'geometry_controls':48,'natural_pairs':12,'arms':{'baseline':baseline,'camera_aware':aware},
 'generation':{'model':'published M3Diff','quantization':'none','dtype':'bfloat16','temperature':0,'num_beams':1,'max_new_tokens':1024,'gpu_request':'A100-40GB'},
 'plan':'One fixed prompt comparison; no fine-tuning or post-result prompt search. Assistant masked assessment: unsupported physical object/state claims on 48 known geometry-only controls; supported-fact coverage and hallucinations on 12 natural pairs. Report identity separately. Scene-clustered uncertainty. Primary held-aside validation has 6 scenes and 24 geometry controls, plus 6 natural pairs; dev likewise. No aggregate CIDEr on handcrafted no-change captions.',
 'selection':'Manually select one representative pair per distinct scene among earlier visually reviewed diagnostic pairs; fixed before new prompt outputs.',
 'success_gate':'Consider prompt promising only if false-positive count decreases on validation geometry controls and total supported-fact hits do not decrease on validation natural pairs. No claim of generalization from this small reused-image diagnostic.',
 'limitations':['Sources have already been viewed and evaluated in earlier work. Scene-held-aside here is only within this diagnostic; not a fresh external test.','2D affine roll/crop/zoom is not a true 3D camera viewpoint change.','Rotation controls include the minimal center zoom needed to avoid invented padding; record actual scale.','Cropping hides border content; physical deletion claims are wrong, explicit out-of-frame/visibility statements allowed.','One seed, 12 scenes, assistant review not independent human gold.','Prompt combines geometry caution and grounding; effects cannot be attributed separately.'],
 'file_sha256':{str(p.relative_to(ROOT/'dataset')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'dataset').rglob('*')) if p.is_file()}}
save('protocol_locked.json',lock)
# All previews generated before model outputs.
boards=ROOT/'boards';boards.mkdir(exist_ok=True)
for r in manifest:
    board=Image.new('RGB',(1500,800),'#eeeeee');draw=ImageDraw.Draw(board)
    for k,rel in enumerate(r['image']):
        pic=ImageOps.contain(Image.open(ROOT/'dataset'/rel),(740,750));board.paste(pic,(750*k+(740-pic.width)//2,40+(750-pic.height)//2))
        draw.text((750*k+8,10),r['id']+(' BEFORE' if k==0 else ' AFTER'),fill='black')
    board.save(boards/(r['id']+'.jpg'),quality=94)
print('Prepared 60 pairs, 12 scenes, 120 generations; protocol locked before output.')
