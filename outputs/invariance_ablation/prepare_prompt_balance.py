"""Balance question templates without changing images, targets or record order."""
from pathlib import Path
import json,copy,collections,random,hashlib,shutil
HERE=Path(__file__).parent;OUT=HERE.parent/'prompt_balanced_sft';OUT.mkdir(exist_ok=True)
old=json.loads((HERE/'train.json').read_text());new=copy.deepcopy(old)
positive=collections.Counter(r['conversations'][0]['value'] for r in old if not r['is_invariance_negative']);assert len(positive)==10 and sum(positive.values())==192
templates=sorted(positive);target={p:positive[p]//3 for p in templates};remaining=64-sum(target.values())
for p in sorted(templates,key=lambda p:(-(positive[p]%3),positive[p]//3,p))[:remaining]:target[p]+=1
assert sum(target.values())==64 and all(4<=n<=8 for n in target.values())
conditions=['identity','zoom_in_1p10','roll_8_safe','zoom_out_reverse_1p10'];rng=random.Random(2026102804)
rosters={c:list(templates) for c in conditions};capacity={c:6 for c in conditions}
for p in sorted(templates,key=lambda p:(-(target[p]-4),p)):
 choices=conditions[:];rng.shuffle(choices);choices.sort(key=lambda c:-capacity[c]);chosen=choices[:target[p]-4]
 assert all(capacity[c]>0 for c in chosen)
 for c in chosen:rosters[c].append(p);capacity[c]-=1
assert all(n==0 for n in capacity.values())
for c in conditions:
 rows=[r for r in new if r['is_invariance_negative'] and r['id'].endswith('_'+c)];assert len(rows)==len(rosters[c])==16
 rng.shuffle(rosters[c])
 for r,p in zip(rows,rosters[c]):r['conversations'][0]['value']=p
for a,b in zip(old,new):
 assert a['id']==b['id'] and a['image']==b['image'] and a['conversations'][1:]==b['conversations'][1:]
 if not a['is_invariance_negative']:assert a==b
negative=collections.Counter(r['conversations'][0]['value'] for r in new if r['is_invariance_negative']);assert negative==target
audit={'only_negative_human_prompt_changes':True,'record_order_identical':True,'images_and_assistant_targets_identical':True,'n_positive':192,'n_negative':64,'positive_prompt_counts':dict(positive),'old_negative_prompt_counts':dict(collections.Counter(r['conversations'][0]['value'] for r in old if r['is_invariance_negative'])),'new_negative_prompt_counts':dict(negative),'each_condition_contains_every_prompt':True,'assignment_seed':2026102804,'limits':'Question length changes training dropout RNG consumption; matching initialization/order does not prove identical dropout masks. One seed; shortcut is possible from distribution, not proved as learned mechanism.'}
(OUT/'train.json').write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf8');audit['train_sha256']=hashlib.sha256((OUT/'train.json').read_bytes()).hexdigest()
(OUT/'data_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
for n in ['eval_questions.json','eval_manifest.json','train_weighted.py']:shutil.copy2(HERE/n,OUT/n)
print(json.dumps(audit,ensure_ascii=False,indent=2))
