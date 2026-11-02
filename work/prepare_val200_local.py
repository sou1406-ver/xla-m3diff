from pathlib import Path
import json,random,hashlib,collections
root=Path(__file__).resolve().parents[1];out=root/'outputs/r64_val_precheck_20261102'
rows=[json.loads(l) for l in (out/'SOURCE_annotation.jsonl').read_text().splitlines() if l.strip()]
rng=random.Random(20261103);chosen=[];groupinfo={}
for domain in ['real','render']:
    pool=[r for r in rows if r['split']=='val' and r['subset']==domain]
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    for r in pool:
        a,b=map(find,r['image']);parent[max(a,b)]=min(a,b)
    groups=collections.defaultdict(list)
    for r in pool:groups[find(r['image'][0])].append(r)
    pools=[sorted(g,key=lambda r:r['id']) for k,g in sorted(groups.items())]
    for g in pools:rng.shuffle(g)
    rng.shuffle(pools);selected=[];i=0
    while len(selected)<100:
        for g in pools:
            if i<len(g):selected.append(g[i])
            if len(selected)==100:break
        i+=1
    for r in selected:r['image_component']=find(r['image'][0])
    chosen+=selected
    groupinfo[domain]={'available_pairs':len(pool),'available_image_components':len(groups),'selected_pairs':100,'selected_image_components':len({r['image_component'] for r in selected})}
testq=json.loads((root/'outputs/baseline_source_audit_20261102/baseline_reproduction_v1/repo/data/evaluation/prompt/OmniDiff_Real_test.json').read_text())
prompt=testq[0]['text'] if 'text' in testq[0] else testq[0].get('conversations',[{}])[0].get('value')
assert prompt
questions=[{'id':r['id'],'image':r['image'],'conversations':[{'from':'human','value':prompt}]} for r in chosen]
# All source paths, not only selected pairs: pathname overlap audit against train/test.
selectedpaths={p for r in chosen for p in r['image']}
overlaps={split:len(selectedpaths&{p for r in rows if r['split']==split for p in r['image']}) for split in ['train','test']}
assert not any(overlaps.values())
for name,data in [('selected_rows.json',chosen),('questions.json',questions)]:
    (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for domain in ['real','render']:
    rs=[r for r in chosen if r['subset']==domain]
    ref={'images':[{'id':r['id']} for r in rs],'annotations':[{'id':r['id'],'image_id':r['id'],'caption':r['caption']} for r in rs]}
    (out/f'{domain}_reference.json').write_text(json.dumps(ref,ensure_ascii=False,indent=2),encoding='utf-8')
lock={'selection_locked_before_inference':True,'seed':20261103,'dataset_revision':'ed4a84cc51912c73e3d54c8643256d9469657552','sampling':'round robin shuffled connected image components per domain','groups':groupinfo,'path_overlap':overlaps,'unique_image_files':len(selectedpaths),'prompt':prompt,'exposure':'No val IDs found in locally searched prior artifacts before selection; not a guarantee of no prior exposure elsewhere. Full test already exposed. RGB overlap pending image download; do not call independent unseen-scene validation.','hashes':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['SOURCE_annotation.jsonl','selected_rows.json','questions.json','real_reference.json','render_reference.json']}}
(out/'SELECTION_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(lock,ensure_ascii=False,indent=2))
