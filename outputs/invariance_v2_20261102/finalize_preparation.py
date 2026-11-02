"""Review-bound artifact finalization, before any new inference or training."""
import copy,hashlib,json,random,zipfile
from pathlib import Path
HERE=Path(__file__).parent
with zipfile.ZipFile(HERE/'preparation.zip') as z:
    for name in z.namelist():
        if name=='PLAN.md': continue
        target=(HERE/name).resolve()
        assert target.is_relative_to(HERE.resolve()),name
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(name))
old=json.loads((HERE.parent/'invariance_ablation/train.json').read_text())
pos=[r for r in old if not r['is_invariance_negative']]; neg=[r for r in old if r['is_invariance_negative']]
assert len(pos)==192 and len(neg)==64
control=[]
for block in [pos,neg]:
    for repeat in range(2):
        for row in block:
            r=copy.deepcopy(row);r['id']=f'control_{repeat}_'+str(row['id']);control.append(r)
order=list(range(512));random.Random(2026110201).shuffle(order);control=[control[i] for i in order]
revised=json.loads((HERE/'train_revised.json').read_text())
assert len(control)==len(revised)==512
assert all(a['is_invariance_negative']==b['is_invariance_negative'] for a,b in zip(control,revised))
# Half of augmented positives perturb AFTER only: true differences remain visible,
# while the caption must also account for a known display rotation/scale change.
relative=0
for row in revised:
    if str(row['id']).startswith('positive_aug_'):
        i=int(row['id'].removeprefix('positive_aug_'))
        if i%2:
            row['image'][0]=pos[i]['image'][0]
            row['conversations'][-1]['value'] += (' The second image is also displayed at a smaller scale.' if i%3==2
                else ' The second image is also displayed with an additional rotation.')
            relative+=1
assert relative==96
(HERE/'train_control.json').write_text(json.dumps(control,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/'train_revised.json').write_text(json.dumps(revised,ensure_ascii=False,indent=2),encoding='utf8')
audit=json.loads((HERE/'data_audit.json').read_text())
audit['train_hashes']['control']=hashlib.sha256((HERE/'train_control.json').read_bytes()).hexdigest()
audit['train_hashes']['revised']=hashlib.sha256((HERE/'train_revised.json').read_bytes()).hexdigest()
audit['matched_positive_negative_flags_per_index']=True
audit['positive_augmentation']={'common_both_images':96,'after_only_with_explicit_caption':96}
audit['finalization_note']='Control arranged positive384/negative128 before same shuffle, matching revised category indices. No captions observed.'
(HERE/'data_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
print(json.dumps(audit,indent=2))
