"""Summarize original keyword scorer; leave semantic gates to human review."""
from pathlib import Path
import json,csv,collections,hashlib
HERE=Path(__file__).parent
read=lambda n:[json.loads(l) for l in (HERE/n).read_text(encoding='utf-8').splitlines() if l.strip()]
man=read('manifest.jsonl');base={r['id']:r['caption'] for r in read('camtest_base.jsonl')};ft={r['id']:r['caption'] for r in read('camtest_ft.jsonl')}
assert len(man)==len(base)==len(ft)==240
assert set(base)==set(ft)=={r['pair_id'] for r in man}
scores=list(csv.DictReader((HERE/'camtest_compare.csv').open(encoding='utf-8')))
assert len(scores)==480
lookup={(r['pair_id'],r['model']):r for r in scores}
truth=lambda v:v.lower()=='true'
summary={}
for group in ['camera_only','camera_object']:
    chosen=[r for r in man if (r['cond'] in ['cam_add','cam_remove'])==(group=='camera_object')]
    entry={'n':len(chosen)}
    for model in ['base','ft']:
        selected=[lookup[r['pair_id'],model] for r in chosen]
        entry[model]={'mentions_camera':sum(truth(r['cam_ok']) for r in selected),'direction_keyword_correct':sum(truth(r['dir_ok']) for r in selected)}
        if group=='camera_only':entry[model]['object_change_keyword_flag']=sum(truth(r['false_obj']) for r in selected)
        else:entry[model].update({'object_type_keyword':sum(truth(r['obj_type_ok']) for r in selected),'object_name_keyword':sum(truth(r['obj_name_ok']) for r in selected),'object_type_and_name_keywords':sum(truth(r['obj_name_ok']) and truth(r['obj_type_ok']) for r in selected)})
    summary[group]=entry
rows=[]
for m in man:
    row={k:m.get(k,'') for k in ['pair_id','cond','level','category','caption','camera_dir','bg_source','image_A','image_B']}
    row['base_caption']=base[m['pair_id']];row['r64_caption']=ft[m['pair_id']]
    for model in ['base','ft']:
        for k in ['false_obj','obj_type_ok','obj_name_ok','cam_ok','dir_ok']:row[model+'_keyword_'+k]=lookup[m['pair_id'],model].get(k,'')
    for k in ['human_base_hallucination','human_r64_hallucination','human_base_correct_object_change','human_r64_correct_object_change','human_notes']:row[k]=''
    rows.append(row)
with (HERE/'REVIEW_240.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(HERE/'keyword_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
timings=json.loads((HERE/'timings.json').read_text());print('TIMINGS',timings)
text=['# Camera240: caption gốc và r64 để chấm gate','', 'Điểm từ khóa chỉ là hỗ trợ; cột human trong REVIEW_240.csv để trống. Chưa quyết định qua gate.','']
for row in rows:
    text.extend([f"## {row['pair_id']} — {row['cond']} / {row['category']}",'',f"Kỳ vọng: {row['caption']}",'',f"Gốc: {row['base_caption']}",'',f"r64: {row['r64_caption']}",''])
(HERE/'CAPTIONS_240.md').write_text('\n'.join(text),encoding='utf-8')
