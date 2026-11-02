"""CPU-only deterministic data construction and leakage/provenance audit."""
from pathlib import Path
import json,hashlib,collections,sys,random,math,types
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import urlopen
from urllib.parse import quote
import time
import cv2,numpy as np,pandas as pd
from PIL import Image
ROOT=Path('/mnt/m3diff');OUT=ROOT/'r64_v2_final_round';DATA=OUT/'data';DATA.mkdir(parents=True,exist_ok=True);(DATA/'images').mkdir(exist_ok=True)
sys.path.insert(0,'/root')
import make_ft_data as g
recipe=json.loads(Path('/root/DATA_RECIPE.json').read_text());policy=json.loads(Path('/root/CAPTION_POLICY.json').read_text())
seed=recipe['seed'];rng=np.random.default_rng(seed)
annotation=[json.loads(l) for l in Path('/root/annotation.jsonl').read_text().splitlines() if l.strip()]
valimages=json.loads(Path('/root/IMAGE_MANIFEST.json').read_text());valhash={r['rgb_sha256'] for r in valimages};valpaths={r['path'] for r in valimages}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dh(im):
    rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB);h=hashlib.sha256();h.update(str((rgb.shape[1],rgb.shape[0])).encode());h.update(rgb.tobytes());return h.hexdigest()
train=[r for r in annotation if r['split']=='train'];paths=sorted({p for r in train for p in r['image']});hashcache=OUT/'TRAIN_SOURCE_RGB_HASHES.json';hashes=json.loads(hashcache.read_text()) if hashcache.exists() else {}
def ensure_image(name):
    path=ROOT/'baseline_cache/OmniDiff'/name
    if path.is_file():return
    path.parent.mkdir(parents=True,exist_ok=True)
    url='https://huggingface.co/datasets/IVC-liuyuan/OmniDiff/resolve/ed4a84cc51912c73e3d54c8643256d9469657552/'+quote(name,safe='/')
    for attempt in range(4):
        try:
            b=urlopen(url,timeout=45).read();tmp=path.with_suffix('.download');tmp.write_bytes(b)
            with Image.open(tmp) as im:im.verify()
            tmp.replace(path);return
        except Exception:
            if attempt==3:raise
            time.sleep(2*(attempt+1))
with ThreadPoolExecutor(max_workers=8) as ex:
    futures=[ex.submit(ensure_image,p) for p in paths]
    for i,f in enumerate(as_completed(futures),1):
        f.result()
        if i%200==0:print('TRAIN_CACHE',i,len(paths),flush=True)
if 'commit' in globals():commit()
for i,p in enumerate(paths):
    if p not in hashes:
        with Image.open(ROOT/'baseline_cache/OmniDiff'/p) as pil:
            pil=pil.convert('RGB');h=hashlib.sha256();h.update(str(pil.size).encode());h.update(pil.tobytes());hashes[p]=h.hexdigest()
    if (i+1)%250==0:
        hashcache.write_text(json.dumps(hashes));print('HASHED',i+1,len(paths),flush=True)
        if 'commit' in globals():commit()
hashcache.write_text(json.dumps(hashes))
eligible=[r for r in train if not any(p in valpaths or hashes[p] in valhash for p in r['image'])]
old=json.loads((ROOT/'ft/train_mix.json').read_text());oldpairs={tuple(p.replace('OmniDiff/','',1) for p in r['image']) for r in old if all(p.startswith('OmniDiff/') for p in r['image'])}
rr=random.Random(seed);replay=[]
for dom,n in [('real',3039),('render',2361)]:
    unique={tuple(r['image']):r for r in eligible if r['subset']==dom}
    replay += rr.sample(sorted(unique.values(),key=lambda r:r['id']),n)
assert len({r['id'] for r in replay})==len({tuple(r['image']) for r in replay})==5400
baseq=json.loads((ROOT/'baseline_reproduction_v1/repo/data/evaluation/prompt/OmniDiff_Real_test.json').read_text());prompts=sorted({q['conversations'][0]['value'] for q in baseq});assert len(prompts)==10
bgs=[]
for dom in ['Real','Render']:
    pool=[p for p in paths if p.startswith(dom+'/') and hashes[p] not in valhash]
    chosen=rr.sample(pool,min(300,len(pool)))
    for p in chosen:bgs.append((p,g.resize_to_long(cv2.imread(str(ROOT/'baseline_cache/OmniDiff'/p)),g.SRC_LONG)))
objs,color=g.load_objects(types.SimpleNamespace(objects_dir=str(ROOT/'ft/objects_all'),objects_csv='objects_train.csv'))
unique_bgs=list({hashes[name]:(name,src) for name,src in bgs}.values());assert len(unique_bgs)>=300
control_bgs={k:rr.sample(unique_bgs,300) for k in ['light','same','jpeg']}
test_ids=set(pd.read_csv(ROOT/'synth/objects/objects.csv')['obj_id']);assert not set(objs['obj_id'])&test_ids
def camera_cap(rng,kind,val,extra):
    key=('zoom_'+extra) if kind=='zoom' else kind
    return policy['camera_prefixes'][key][0]
g.cap_camera=camera_cap
def obj(pool,bg,center,used):
    H,W=bg.shape[:2]
    for _ in range(100):
        o=pool.iloc[int(rng.integers(len(pool)))];cat=o['category']
        if cat in used:continue
        rgb,a=g.prepare_object(o['_rgba'],float(rng.uniform(.012,.025))*W*H)
        if rgb.shape[1]>.20*W or rgb.shape[0]>.28*H:continue
        im,_=g.paste(bg,rgb,a,*center)
        if im is not None:return o,rgb,a
    raise RuntimeError('Could not place bounded distinct object')
def multi(index):
    name,src=bgs[int(rng.integers(len(bgs)))];bg=g.fit_out(src);H,W=bg.shape[:2]
    c1=(.23*W,.42*H);o1,rgb1,a1=obj(color,bg,c1,set());cn1=g.color_name(rgb1,a1)
    for _ in range(100):
        deg=float(rng.uniform(60,160))*(1 if rng.integers(2) else -1);rgb2=g.hue_shift(rgb1,deg);cn2=g.color_name(rgb2,a1)
        if cn1 and cn2 and cn1!=cn2:break
    else:return None
    A,_=g.paste(bg,rgb1,a1,*c1);B,_=g.paste(bg,rgb2,a1,*c1)
    caps=[g.cap_color(rng,cn1,cn2,o1['category'],g.loc_phrase(*c1,W,H))]
    op=['add','remove','move','size'][index%4];c2=(.70*W,.42*H);o2,r2,a2=obj(objs,bg,c2,{o1['category']});cn=g.color_name(r2,a2);loc=g.loc_phrase(*c2,W,H)
    if op=='add':B,_=g.paste(B,r2,a2,*c2);caps.append(g.cap_add(rng,cn,o2['category'],loc))
    if op=='remove':A,_=g.paste(A,r2,a2,*c2);caps.append(g.cap_remove(rng,cn,o2['category'],loc))
    if op=='move':
        A,_=g.paste(A,r2,a2,*c2);B,_=g.paste(B,r2,a2,c2[0]+.12*W,c2[1]);caps.append(g.cap_move(rng,cn,o2['category'],loc,'right'))
    if op=='size':
        A,_=g.paste(A,r2,a2,*c2);r3=cv2.resize(r2,None,fx=1.5,fy=1.5);a3=cv2.resize(a2,None,fx=1.5,fy=1.5);B,_=g.paste(B,r3,a3,*c2);caps.append(g.cap_size(rng,cn,o2['category'],loc,True))
    ids=[int(o1['obj_id']),int(o2['obj_id'])];categories=[o1['category'],o2['category']]
    if index%2==0:
        c3=(.46*W,.80*H);o3,r3,a3=obj(objs,bg,c3,set(categories));B,_=g.paste(B,r3,a3,*c3);caps.append(g.cap_add(rng,g.color_name(r3,a3),o3['category'],g.loc_phrase(*c3,W,H)));ids.append(int(o3['obj_id']));categories.append(o3['category'])
    assert A is not None and B is not None
    return A,B,' '.join(caps),{'cond':'multi_object','bg_source':name,'operations':['color',op]+(['add'] if index%2==0 else []),'obj_ids':ids,'categories':categories,'color_from':cn1,'color_to':cn2}
plan=[]
for kind,n in recipe['synthetic_plan'].items():plan += [(kind,i) for i in range(n)]
records=[];manifest=[]
for idx,(kind,i) in enumerate(plan):
    if kind in ['light','same','jpeg']:
        name,src=control_bgs[kind][i];A=g.fit_out(src);B=A.copy();meta={'cond':kind,'bg_source':name}
        if kind=='light':
            power=float(rng.uniform(1.2,2.4));up=bool(rng.integers(2));power=1/power if up else power;B=g.gamma(A,power);cap=g.cap_light(rng,up);meta['gamma']=power
        elif kind=='jpeg':
            quality=int(rng.integers(45,85));ok,enc=cv2.imencode('.jpg',A,[cv2.IMWRITE_JPEG_QUALITY,quality]);assert ok;B=cv2.imdecode(enc,cv2.IMREAD_COLOR);cap='There is no difference between the two images.';meta['jpeg_quality']=quality
        else:cap='There is no difference between the two images.'
    elif kind=='multi_object':
        for _ in range(100):
            result=multi(i)
            if result is not None:break
        else:raise RuntimeError('Could not generate a valid multi-object pair')
        A,B,cap,meta=result
    else:
        if kind=='camera_only':
            cond=(['zoom_in']*60+['zoom_out']*60+['rotate']*40+['pan']*40)[i]
            level=float(rng.uniform(1.1,1.5)) if cond.startswith('zoom') else (float(rng.uniform(3,15)) if cond=='rotate' else float(rng.uniform(.05,.18)))
        elif kind=='camera_object':cond='cam_add' if i<50 else 'cam_remove';level=None
        else:cond='color';level=None
        for _ in range(100):
            res=g.make_one(cond,rng,bgs,objs,color,level=level)
            if res is None:continue
            A,B,cap,meta=res
            if cond=='color' and ('different shade' in cap or np.array_equal(A,B)):continue
            break
        else:raise RuntimeError('Generation failed')
        if kind.startswith('camera'):
            meta['camera_prefix']=camera_cap(rng,meta['camera'],meta['camera_value'],meta['camera_dir']);assert cap.startswith(meta['camera_prefix'])
    assert A.shape==B.shape and A.dtype==B.dtype==np.uint8
    if kind=='same':assert np.array_equal(A,B)
    else:assert not np.array_equal(A,B),(kind,i)
    pid=f'v2_{kind}_{i:04d}';pa=f'r64_v2_final_round/data/images/{pid}_A.png';pb=f'r64_v2_final_round/data/images/{pid}_B.png'
    assert cv2.imwrite(str(ROOT/pa),A) and cv2.imwrite(str(ROOT/pb),B)
    prompt=prompts[idx%10]
    records.append({'id':pid,'image':[pa,pb],'conversations':[{'from':'human','value':prompt},{'from':'gpt','value':cap}]})
    manifest.append({'id':pid,'image':[pa,pb],'caption':cap,'word_count':len(cap.split()),'kind':kind,'source_image_rgb_sha256':hashes[meta['bg_source']],'rgb_sha256':[dh(A),dh(B)],'metadata':meta})
    if (idx+1)%100==0:print('GENERATED',idx+1,1800,flush=True)
for i,r in enumerate(replay):
    records.append({'id':'v2_replay_'+r['id'],'image':['baseline_cache/OmniDiff/'+p for p in r['image']],'conversations':[{'from':'human','value':prompts[i%10]},{'from':'gpt','value':r['caption']}]})
rr.shuffle(records);assert len(records)==7200
(DATA/'train.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
(DATA/'synthetic_manifest.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in manifest)+'\n',encoding='utf-8')
(DATA/'replay_manifest.json').write_text(json.dumps(replay,ensure_ascii=False,indent=2),encoding='utf-8')
assert len({tuple(r['rgb_sha256']) for r in manifest})==1800,'Synthetic duplicates must be fixed before training'
audit={'records':7200,'synthetic_records':1800,'replay_records':5400,'replay_domains':dict(collections.Counter(r['subset'] for r in replay)),'unique_replay_ids':len({r['id'] for r in replay}),'unique_replay_ordered_pairs':len({tuple(r['image']) for r in replay}),'overlap_r64_replay':sum(tuple(r['image']) in oldpairs for r in replay),'selected_val_path_matches':0,'selected_val_rgb_matches':0,'train_source_images_hashed':len(hashes),'train_images_rejected_rgb_val_overlap':sum(h in valhash for h in hashes.values()),'synthetic_plan':dict(collections.Counter(r['kind'] for r in manifest)),'multi_operations':dict(collections.Counter(op for r in manifest if r['kind']=='multi_object' for op in r['metadata']['operations'])),'multi_unique_records':len({tuple(r['rgb_sha256']) for r in manifest if r['kind']=='multi_object'}),'unique_synthetic_rgb_pairs':len({tuple(r['rgb_sha256']) for r in manifest}),'source_backgrounds':len({r['metadata']['bg_source'] for r in manifest}),'objects_test_overlap':0,'train_json_sha256':sha(DATA/'train.json'),'recipe_sha256':sha('/root/DATA_RECIPE.json'),'caption_policy_sha256':sha('/root/CAPTION_POLICY.json'),'replay_camera_wording_audit':'Original official replay labels retained. Camera-like text not standardized; report detector counts separately.'}
from camera_detector import camera_motion_claim
audit['replay_camera_detector_count']=sum(camera_motion_claim(r['caption']) for r in replay)
(OUT/'DATA_AUDIT.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
# Fixed review allocation covers new controls, color, every multi-operation and camera mode.
selected=[]
for k in recipe['synthetic_plan']:
    group=[r for r in manifest if r['kind']==k]
    if k=='multi_object':
        for op in ['add','remove','move','size']:selected+=rr.sample([r for r in group if r['metadata']['operations'][1]==op],2)
    elif k=='camera_only':
        for cond in ['zoom_in','zoom_out','rotate','pan']:selected+=rr.sample([r for r in group if r['metadata']['cond']==cond],1)
    elif k=='camera_object':
        for op in ['add','remove']:selected+=rr.sample([r for r in group if r['metadata']['obj_change']==op],2)
    elif k=='light':
        selected+=rr.sample([r for r in group if r['metadata']['gamma']<1],2)+rr.sample([r for r in group if r['metadata']['gamma']>1],2)
    else:selected+=rr.sample(group,4)
(OUT/'DATA_REVIEW_SELECTION.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
from PIL import Image,ImageDraw,ImageFont
try:font=ImageFont.truetype('DejaVuSans.ttf',18)
except OSError:font=ImageFont.load_default()
import textwrap
for i in range(0,len(selected),4):
    canvas=Image.new('RGB',(1600,2400),'white');d=ImageDraw.Draw(canvas)
    for j,r in enumerate(selected[i:i+4]):
        y=j*600;d.text((10,y+5),r['id'],fill='black',font=font)
        for side,imgpath in enumerate(r['image']):
            im=Image.open(ROOT/imgpath).convert('RGB');im.thumbnail((780,420));canvas.paste(im,(side*800+10,y+35))
        for k,l in enumerate(textwrap.wrap(r['caption'],width=145)):d.text((10,y+470+k*23),l,fill='black',font=font)
    canvas.save(OUT/f'data_review_{i//4:02d}.jpg',quality=90)
print('PREPARATION_COMPLETE',flush=True)
