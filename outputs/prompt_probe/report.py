from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).parent
def load(n):return json.loads((ROOT/n).read_text(encoding='utf-8-sig'))
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
preds=load('results/masked_predictions.json');work=load('masked_assessments.json');assert len(preds)==len(work['cases'])==40
for p,r in zip(preds,work['cases']):
 assert p['id']==r['id']
 for c in [1,2,3]:assert r[f'candidate_{c}'] and r[f'candidate_{c}']['caption']==p[f'candidate_{c}']
key=load('results/mask_key.json');rows=[]
for p,r in zip(preds,work['cases']):
 for c in [1,2,3]:rows.append({**{k:p[k] for k in ['id','source_case_id','scene','condition','split','prompt_index','prompt']},'arm':key[p['id']][f'candidate_{c}'],**r[f'candidate_{c}']})
save('decoded_assessments.json',{'masked_score_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows})
arms=['baseline','old_mixed','balanced'];stats={}
groups={'all':lambda r:True,'fixed_question':lambda r:r['prompt'].startswith("What's the difference between 2 images?"),'other_questions':lambda r:not r['prompt'].startswith("What's the difference between 2 images?")}
for source in sorted({r['source_case_id'] for r in rows}):groups[source]=lambda r,s=source:r['source_case_id']==s
for name,keep in groups.items():
 out={}
 for arm in arms:
  rs=[r for r in rows if r['arm']==arm and keep(r)];vague=lambda r:r['caption'].strip()=='The scene has become more visible.' and r['condition']!='identity'
  out[arm]={'n':len(rs),'physical_fp_pairs':sum(r['fp'] for r in rs),'illumination_or_visibility_inferences':sum(r['illum'] for r in rs),'identity_difference_pairs':sum(r['identity_diff'] for r in rs),'broad_object_or_lighting_visibility_error':sum(bool(r['fp'] or r['illum'] or r['wrong_geometry']) for r in rs),'ambiguous_more_visible_only':sum(vague(r) and not r['fp'] for r in rs),'strict_error_excluding_vague_visibility':sum(bool(r['fp'] or (r['illum'] and not vague(r)) or r['wrong_geometry']) for r in rs)}
 stats[name]=out
save('metrics.json',stats)
save('decision.json',{'full_candidate_remains':'old_mixed','reason':'Balanced failed factual72 gate before probe decoded; geometry probe cannot rescue it.','shortcut_interpretation':'Fixed-template training imbalance is real. This four-source-case probe does not demonstrate that gains are restricted to that question, and balancing does not establish improved caption factuality.','ambiguity':'More visible can describe wider framing, so broad visibility tag is not by itself proved false illumination; show strict sensitivity alongside original broad count. Do not change saved ratings or claim correct camera reasoning.','sample_units':'40questions are10styles crossed with4sourcecases, not40 independent scenes.'})
lines=['# Probe10 cách hỏi ×4 cặp ảnh cố định','', 'Baseline, mixed cũ và balanced chạy cùng A10, tổng120 caption. Khóa tên model chỉ mở sau khi lưu toàn bộ nhãn. Đây là4 source case phát triển lặp10 cách hỏi; không phải40 scene độc lập.','', '| Chỉ số /40 câu | Baseline | Mixed cũ | Balanced |','|---|---:|---:|---:|']
for field,label in [('physical_fp_pairs','Bịa thay vật'),('broad_object_or_lighting_visibility_error','Vật/ánh sáng/độ rõ, nhãn rộng'),('strict_error_excluding_vague_visibility','Loại câu độ rõ mơ hồ khỏi lỗi chắc'),('ambiguous_more_visible_only','Chỉ nói more visible, chưa rõ cơ chế')]:lines.append('| '+label+' | '+' | '.join(str(stats['all'][a][field]) for a in arms)+' |')
lines+=['','Cụm “more visible” có thể nói về khung hình rộng hơn, không chắc là bịa ánh sáng. Giữ nguyên nhãn visibility từ rubric trước và báo thêm phân tích độ nhạy, không đổi nhãn sau giải khóa. Không coi câu mơ hồ này là đã hiểu đúng camera.','', 'Nguy cơ shortcut câu hỏi có trong phân phối train, nhưng probe nhỏ này chưa chứng minh model chỉ cải thiện ở câu đã dùng cho negative. Bản balanced không được chọn vì đã giảm fact cũ Real; không dùng probe để đảo điều kiện bảo toàn fact.','', 'Từng source/cách hỏi và caption nằm trong metrics.json/decoded_assessments.json. Trợ lý chấm, chưa được người chấm độc lập xác nhận.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_prompt_probe.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.log','.md','.txt']:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps(stats['all'],ensure_ascii=False,indent=2))
