"""Decode only after all masked annotations have been recorded."""
import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
scores=load(ROOT/'masked_assessments.json');preds=load(ROOT/'results/masked_predictions.json')
assert len(scores['cases'])==len(preds)==72
for r,p in zip(scores['cases'],preds):
 assert r['id']==p['id']
 for c in [1,2,3]:assert r[f'candidate_{c}'] and r[f'candidate_{c}']['caption']==p[f'candidate_{c}']
key=load(ROOT/'results/mask_key.json');rubric=load(ROOT.parent/'invariance_sft/eval_rubric.json');rows=[]
for r,p in zip(scores['cases'],preds):
 for c in [1,2,3]:rows.append({**{k:p[k] for k in ['id','cohort','scene','split','condition']},'arm':key[p['id']][f'candidate_{c}'],**r[f'candidate_{c}']})
save('decoded_assessments.json',{'masked_score_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows})
arms=['baseline','positive_control','mixed_objective'];stats={}
for cohort in ['old','new','all']:
 for domain in ['Real','Render','all']:
  for group in ['identity','transformed','natural']:
   selected=[r for r in rows if (cohort=='all' or r['cohort']==cohort) and (domain=='all' or r['split']==domain) and ((group=='identity' and r['condition']=='identity') or (group=='transformed' and r['condition'] not in ['identity','natural']) or (group=='natural' and r['condition']=='natural' and r['scene'] not in rubric['excluded_natural'].get(r['cohort'],[])))]
   result={}
   for a in arms:
    rs=[r for r in selected if r['arm']==a]
    result[a]={'n':len(rs),'physical_fp_pairs':sum(r['fp'] for r in rs),'illumination_inferences':sum(r['illum'] for r in rs),'camera_acknowledged':sum(r['ack'] for r in rs),'identity_difference_pairs':sum(r['identity_diff'] for r in rs),'fact_hits':sum(len(r['facts']) for r in rs),'unsupported_pairs':sum(bool(r['unsupported']) for r in rs),'suppressed_natural_pairs':sum(r['suppression'] for r in rs)}
    result[a]['physical_or_illumination_errors']=sum(bool(r['fp'] or r['illum']) for r in rs)
    result[a]['wrong_global_explanations']=sum('WRONG:' in r.get('note','') for r in rs)
    result[a]['any_recorded_geometry_error']=sum(bool(r['fp'] or r['illum'] or 'WRONG:' in r.get('note','')) for r in rs)
    if group=='natural':result[a]['possible_facts']=sum(len(rubric['facts'][r['cohort']][r['scene']]) for r in rs)
   stats[f'{cohort}/{domain}/{group}']=result
save('metrics.json',stats);checks={}
for a in arms[1:]:
 ch={'new_physical_fp_decreases':stats['new/all/transformed'][a]['physical_fp_pairs']<stats['new/all/transformed']['baseline']['physical_fp_pairs']}
 for cohort in ['old','new']:
  for domain in ['Real','Render']:ch[f'{cohort}_{domain}_facts_preserved']=stats[f'{cohort}/{domain}/natural'][a]['fact_hits']>=stats[f'{cohort}/{domain}/natural']['baseline']['fact_hits']
 ch['new_unsupported_not_increased']=stats['new/all/natural'][a]['unsupported_pairs']<=stats['new/all/natural']['baseline']['unsupported_pairs']
 checks[a]={'checks':ch,'passes':all(ch.values())}
eligible=[a for a in arms[1:] if checks[a]['passes']]
eligible.sort(key=lambda a:(stats['new/all/transformed'][a]['physical_fp_pairs'],-stats['all/all/natural'][a]['fact_hits']))
save('decision.json',{'arms':checks,'selected_for_broader_evaluation':eligible[0] if eligible else None,'limits':'Adaptive development scenes, one seed, synthetic2D, assistant labels. Not final benchmark proof.'})
lines=['# Đối chứng loss không đổi: hai nhánh LoRA','', 'Cùng256 record, khởi tạo và hai thứ tự epoch đã đối chiếu. Mỗi nhánh64 update, LR2e-5; chỉ khác loss của64 mẫu không đổi là0 hay1. Base, vision, projector và MDP đóng băng. Hai adapter được nạp FP32 riêng; baseline gốc được chạy lại cùng GPU.','', '| Nhóm | Baseline | Chỉ loss positive | Thêm loss không đổi |','|---|---:|---:|---:|']
for key_,label,field in [('new/all/transformed','Bịa thay vật,32 cặp xoay/zoom','physical_fp_pairs'),('new/all/transformed','Đoán ánh sáng thay đổi,32 cặp','illumination_inferences'),('new/all/transformed','Có lỗi vật/ánh sáng/giải thích camera sai,32 cặp','any_recorded_geometry_error'),('all/all/identity','Bịa khác biệt,20 cặp ảnh giống nhau','identity_difference_pairs'),('new/all/natural','Fact đúng,12 fact mới','fact_hits'),('old/all/natural','Fact đúng,22 fact cũ','fact_hits'),('new/all/natural','Cặp tự nhiên có chi tiết sai,7 cặp','unsupported_pairs')]:lines.append('| '+label+' | '+' | '.join(str(stats[key_][a][field]) for a in arms)+' |')
lines+=['','Từng miền Real/Render và từng nhãn nằm trong metrics.json / decoded_assessments.json. Chỉ chọn thử rộng hơn nếu giảm bịa vật và không giảm fact ở bất kỳ miền/nhóm cũ-mới nào; không tăng số cặp tự nhiên có chi tiết sai.', '', 'Quyết định: '+(eligible[0]+' đủ điều kiện pilot để kiểm tra rộng hơn.' if eligible else 'Cả hai nhánh chưa qua điều kiện pilot; giữ checkpoint gốc.'),'', 'Điều kiện pilot đạt không đồng nghĩa caption sạch: mixed vẫn có lỗi vật/ánh sáng/giải thích hình học ở29/32 cặp, so với32/32 baseline. Số đoán ánh sáng tăng7→15; một câu nói xoay90độ trong cặp chỉ zoom-out là sai. Câu sai này đã ghi rõ trước giải khóa, không được coi là hiểu camera đúng.','', f"Đã tái dùng {scores['reused_candidate_annotations']}/216 nhãn khi ID, toàn bộ câu hỏi và caption trùng chính xác. Các câu mới được trợ lý chấm trước khi mở khóa; không phải người chấm độc lập. Ảnh đã được dùng trong quá trình phát triển, augmentation2D không chứng minh góc nhìn3D."]
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_invariance_ablation.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.md','.log','.txt']:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'checks':checks,'selected':eligible,'new_geometry':stats['new/all/transformed'],'natural':stats['all/all/natural']},ensure_ascii=False,indent=2))
