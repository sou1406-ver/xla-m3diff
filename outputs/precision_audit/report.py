"""Report same-checkpoint precision comparison after all scores are saved."""
import csv,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
preds=load('comparison_results/masked_predictions.json');key=load('comparison_results/mask_key.json');scores=load('masked_assessments.json');rubric=load('eval_rubric.json');rows=[]
assert len(scores['cases'])==len(preds)==108
for p,r in zip(preds,scores['cases']):
    assert p['id']==r['id']
    for c in [1,2]:
        s=r[f'candidate_{c}'];assert s is not None and s['caption']==p[f'candidate_{c}']
        rows.append({**{k:p[k] for k in ['id','cohort','scene','split','condition']},'mode':key[p['id']][f'candidate_{c}'],**s})
save('decoded_assessments.json',{'reviewer':scores['reviewer'],'masked_score_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows})
stats={};modes=['merged_bf16','unmerged_fp32']
for cohort in ['old','new','all']:
    for domain in ['Real','Render','all']:
        for group in ['identity','transformed','natural']:
            selected=[]
            for r in rows:
                if cohort!='all' and r['cohort']!=cohort:continue
                if domain!='all' and r['split']!=domain:continue
                if group=='identity' and r['condition']!='identity':continue
                if group=='transformed' and r['condition'] in ['identity','natural']:continue
                if group=='natural' and (r['condition']!='natural' or r['scene'] in rubric['excluded_natural'].get(r['cohort'],[])):continue
                selected.append(r)
            result={}
            for mode in modes:
                rs=[r for r in selected if r['mode']==mode]
                result[mode]={'n':len(rs),'physical_fp_pairs':sum(r['fp'] for r in rs),'illumination_inferences':sum(r['illum'] for r in rs),'camera_acknowledged':sum(r['ack'] for r in rs),'identity_difference_pairs':sum(r['identity_diff'] for r in rs),'fact_hits':sum(len(r['facts']) for r in rs),'unsupported_pairs':sum(bool(r['unsupported']) for r in rs)}
                if group=='natural':result[mode]['possible_facts']=sum(len(rubric['facts'][r['cohort']][r['scene']]) for r in rs)
            stats[f'{cohort}/{domain}/{group}']=result
save('metrics.json',stats)
checks={};s=stats['new/all/transformed'];checks['new_geometry_physical_fp_decreases']=s['unmerged_fp32']['physical_fp_pairs']<s['merged_bf16']['physical_fp_pairs']
for domain in ['Real','Render']:
    s=stats[f'new/{domain}/natural'];checks[f'new_{domain}_fact_hits_do_not_drop']=s['unmerged_fp32']['fact_hits']>=s['merged_bf16']['fact_hits']
s=stats['new/all/natural'];checks['new_unsupported_pairs_do_not_increase']=s['unmerged_fp32']['unsupported_pairs']<=s['merged_bf16']['unsupported_pairs']
decision={'fixed_new_scene_checks':checks,'caption_gain_gate_passes':all(checks.values()),
 'numeric_rounding_evidence':'Mean relative L2 update rounding error .951 on21 matrices; 5.539% of sampled base elements change after merge.',
 'interpretation':'Numerical discrepancy does not itself imply caption improvement. Keep adapter FP32/unmerged as an explicit experimental loading option, not an established quality gain.',
 'production_default':'Published checkpoint remains default until a candidate passes factual-preservation and broader checks.'}
save('decision.json',decision)
same=sum(p['candidate_1']==p['candidate_2'] for p in preds)
diag={'pairs_with_identical_displayed_captions':same,'n_pairs':108,'exact_prior_annotations_reused':scores['reused_candidate_annotations'],'new_candidate_annotations':216-scores['reused_candidate_annotations']}
for mode in modes:
    raw=[json.loads(l) for l in (ROOT/'comparison_results'/(mode+'.jsonl')).read_text().splitlines() if l.strip()]
    words=[len(r['caption'].split()) for r in raw];diag[mode]={'mean_words':sum(words)/len(words),'max_words':max(words),'captions_over_200_words':sum(n>200 for n in words)}
save('diagnostics.json',diag)
lines=['# LoRA FP32 riêng so với merge BF16','',
'Cùng checkpoint invariance_sft_v1, không train thêm: so sánh merge vào base BF16 với giữ LoRA riêng bằng FP32. Hai chế độ chạy cùng108 cặp, cùng prompt/greedy trong cùng GPU container. Đã xác nhận392 tensor adapter được nạp, tất cả LoRA-B khác0, và chế độ FP32 khôi phục đúng từng giá trị đã lưu.','',
'## Phép đo số học','',
'Lấy mẫu21 ma trận ở tầng0,14,27: chỉ5,539% phần tử trọng số nền thay đổi sau merge BF16; sai sốL2 trung bình của cập nhật so với phép cộngFP32 là0,951. Đây là bằng chứng làm tròn cập nhật nhỏ, không phải tỷ lệ mất accuracy hay tỷ lệ caption sai.','',
'## Caption thực tế','',
'| Nhóm | Số cặp | Merge BF16: bịa thay vật | Giữ FP32 riêng: bịa thay vật |','|---|---:|---:|---:|']
for cohort,label in [('new','8 scene mới, xoay/zoom'),('old','12 scene cũ, xoay/zoom')]:
    s=stats[f'{cohort}/all/transformed'];lines.append(f"| {label} | {s[modes[0]]['n']} | {s[modes[0]]['physical_fp_pairs']} | {s[modes[1]]['physical_fp_pairs']} |")
lines+=['','| Nhóm/miền | Tổng fact tự nhiên | Merge BF16 | Giữ FP32 riêng |','|---|---:|---:|---:|']
for cohort in ['new','old']:
    for domain in ['Real','Render']:
        s=stats[f'{cohort}/{domain}/natural'];lines.append(f"| {cohort}/{domain} | {s[modes[0]]['possible_facts']} | {s[modes[0]]['fact_hits']} | {s[modes[1]]['fact_hits']} |")
lines+=['',f"Có {same}/108 cặp có caption hiển thị giống hệt giữa hai chế độ. {scores['reused_candidate_annotations']}/216 nhãn được tái dùng vì ID/câu hỏi và toàn bộ caption trùng khớp; {216-scores['reused_candidate_annotations']} câu mới đã được trợ lý chấm trước khi giải khóa tên chế độ. Đây là procedural masking, không phải người chấm mù độc lập.",'',
('Chế độ không merge đạt điều kiện mới-scene đã định, nhưng còn cần kiểm tra recall cũ, tốc độ, nhiều seed và toàn bộ benchmark.' if all(checks.values()) else 'Chế độ không merge chưa đạt điều kiện tăng chất lượng caption đã định. Mất mát số học là có thật nhưng không đủ giải thích/sửa điểm yếu model trong pilot nhỏ này.'),'',
'Các ảnh này đã được dùng trong quá trình phát triển; chỉ một checkpoint, một họ augmentation2D, ít scene và đánh giá trợ lý. Không suy ra độ bền góc nhìn3D. Điều kiện, từng nhãn, raw caption và dtype audit đều được lưu. Không thay ngưỡng/nhãn sau khi mở khóa.','',
'`load_wrapper.py` giữ phương thức generate của multimodal LM và các LoRA Linear đang hoạt động; không sửa mã repo và không gộp trọng số. Có thể dùng để kiểm tra các lượt train tiếp theo mà không làm tròn delta vào trọng số nền trước inference.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_precision_audit.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.md','.txt','.log']:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'decision':decision,'new_geometry':stats['new/all/transformed'],'new_natural':stats['new/all/natural'],'old_natural':stats['old/all/natural'],'diagnostics':diag},ensure_ascii=False,indent=2))
