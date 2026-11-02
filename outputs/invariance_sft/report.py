"""Decode completed masked scores and apply the one-candidate protocol."""
import collections,csv,hashlib,json,random,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
preds=load('results/masked_predictions.json');key=load('results/mask_key.json');scores=load('masked_assessments.json');rubric=load('eval_rubric.json')
assert len(preds)==len(scores['cases'])==108
lookup={r['id']:r for r in preds};assert set(lookup)=={r['id'] for r in scores['cases']}
rows=[]
for r in scores['cases']:
    p=lookup[r['id']]
    for c in [1,2]:
        s=r[f'candidate_{c}'];arm=key[r['id']][f'candidate_{c}']
        for f in ['fp','ack','illum','identity_diff','suppression']:assert s[f] in [0,1]
        facts=s['facts'];assert len(set(facts))==len(facts)
        if p['condition']=='natural' and p['scene'] not in rubric['excluded_natural'].get(p['cohort'],[]):
            assert all(1<=i<=len(rubric['facts'][p['cohort']][p['scene']]) for i in facts)
        else:assert not facts
        if s['suppression']:assert s['unsupported']
        rows.append({**{k:p[k] for k in ['id','cohort','scene','split','condition']},'arm':arm,**s})
save('decoded_assessments.json',{'reviewer':scores['reviewer'],'masked_source_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows})
stats={}
for cohort in ['old','new','all']:
    for domain in ['Real','Render','all']:
        for group in ['identity','transformed','geometry','natural','uncertain_natural']:
            filtered=[]
            for r in rows:
                if cohort!='all' and r['cohort']!=cohort:continue
                if domain!='all' and r['split']!=domain:continue
                excluded=r['scene'] in rubric['excluded_natural'].get(r['cohort'],[])
                keep=(r['condition']=='identity' if group=='identity' else r['condition'] not in ['identity','natural'] if group=='transformed' else r['condition']!='natural' if group=='geometry' else r['condition']=='natural' and not excluded if group=='natural' else r['condition']=='natural' and excluded)
                if keep:filtered.append(r)
            arms={}
            for arm in ['baseline','invariance']:
                a=[r for r in filtered if r['arm']==arm]
                arms[arm]={'n':len(a),'physical_fp_pairs':sum(r['fp'] for r in a),'camera_acknowledged':sum(r['ack'] for r in a),
                    'illumination_inference_pairs':sum(r['illum'] for r in a),'identity_difference_pairs':sum(r['identity_diff'] for r in a),
                    'supported_fact_hits':sum(len(r['facts']) for r in a),'unsupported_claim_pairs':sum(bool(r['unsupported']) for r in a),'explicit_suppression_pairs':sum(r['suppression'] for r in a)}
                if group=='natural':arms[arm]['possible_facts']=sum(len(rubric['facts'][r['cohort']][r['scene']]) for r in a)
            stats[f'{cohort}/{domain}/{group}']=arms
save('metrics.json',stats)
checks={}
s=stats['new/all/transformed'];checks['new_scene_geometry_physical_fp_decreases']=s['invariance']['physical_fp_pairs']<s['baseline']['physical_fp_pairs']
for cohort in ['old','new']:
    for domain in ['Real','Render']:
        s=stats[f'{cohort}/{domain}/natural'];checks[f'{cohort}_{domain}_natural_fact_hits_do_not_drop']=s['invariance']['supported_fact_hits']>=s['baseline']['supported_fact_hits']
s=stats['new/all/natural'];checks['new_natural_unsupported_pairs_do_not_increase']=s['invariance']['unsupported_claim_pairs']<=s['baseline']['unsupported_claim_pairs']
decision={'checks':checks,'promising_on_this_development_diagnostic':all(checks.values()),'one_configuration_only':True,
 'interpretation':'Small single-seed adaptive development pilot, not external validation or proof of 3D robustness. No claim based solely on no-change accuracy.',
 'selected_for_further_research':all(checks.values()),'production_default':'Published checkpoint + exact-sentence dedup + exact-pixel identity only; approximate registration remains advisory.'}
save('decision.json',decision)
# Fixed scene-level paired resampling: four nonidentity conditions per new scene.
rng=random.Random(2026102725);deltas=[]
for scene in sorted({r['scene'] for r in rows if r['cohort']=='new'}):
    a=[r for r in rows if r['cohort']=='new' and r['scene']==scene and r['condition'] not in ['identity','natural']]
    b=[r['fp'] for r in a if r['arm']=='baseline'];c=[r['fp'] for r in a if r['arm']=='invariance']
    assert len(b)==len(c)==4;deltas.append(100*(sum(c)/4-sum(b)/4))
draws=sorted(sum(rng.choices(deltas,k=len(deltas)))/len(deltas) for _ in range(10000))
save('uncertainty.json',{'new_scene_n':8,'delta_physical_fp_percentage_points_candidate_minus_baseline':sum(deltas)/len(deltas),'scene_bootstrap_CI95':[draws[249],draws[9749]],'limits':'Within-sample scene resampling only, not uncertainty over training seeds or a fresh test distribution.'})
with (ROOT/'case_scores.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['id','cohort','scene','split','condition','arm','physical_fp','illum','camera_ack','identity_difference','fact_hits','suppression','unsupported','uncertain'])
    for r in rows:w.writerow([r['id'],r['cohort'],r['scene'],r['split'],r['condition'],r['arm'],r['fp'],r['illum'],r['ack'],r['identity_diff'],str(r['facts']),r['suppression'],'; '.join(r['unsupported']),'; '.join(r['uncertain'])])
lines=['# Pilot học đối chứng không-thay-đổi','',
('**Có tín hiệu đạt điều kiện đã định trong diagnostic này; giữ checkpoint candidate để nghiên cứu tiếp. Chưa chọn thay model gốc cho toàn bộ hệ thống.**' if all(checks.values()) else '**Candidate chưa đạt đủ điều kiện đã định; giữ checkpoint gốc làm bản chính. Không dò thêm cấu hình sau kết quả này.**'),'','## Đã chạy','',
'Một LoRA r16, LR 5e-6, 32 update; vision/projector/MDP đóng băng. Batch train gồm 64 mẫu không-thay-đổi từ 16 ảnh train và 192 mẫu có thay đổi. Đã kiểm tra 360 ảnh train gốc với 40 ảnh test gốc: không trùng hash RGB sau giải mã. Đây là loại trùng chính xác, không bảo đảm scene độc lập.','',
'Checkpoint gốc và candidate chạy 108 cặp cùng prompt gốc/BF16/greedy trong cùng GPU container, không dùng bộ chặn căn chỉnh hoặc prompt camera-aware. Cả hai caption cùng lọc lặp trước khi xáo tên nhánh. Trợ lý ghi nhận xét rồi mới mở khóa tên; không phải chấm mù độc lập bởi con người.','',
'## Bịa thay đổi vật trên cặp chỉ đổi hình học','',
'| Nhóm | Cặp | Baseline | Candidate |','|---|---:|---:|---:|']
for cohort,label in [('new','8 scene mới'),('old','12 scene diagnostic cũ')]:
    for group,glabel in [('transformed','chỉ xoay/zoom'),('identity','ảnh giống hệt')]:
        s=stats[f'{cohort}/all/{group}'];lines.append(f"| {label}: {glabel} | {s['baseline']['n']} | {s['baseline']['physical_fp_pairs']} | {s['invariance']['physical_fp_pairs']} |")
lines+=['','Khẳng định ánh sáng thay đổi và sai khác giả trên ảnh giống hệt được ghi riêng; ít bịa thay vật không tự chứng minh đã hiểu camera. CSV có chi tiết và phần chưa chắc.','',
'## Khả năng giữ thay đổi thật','',
'| Nhóm | Miền | Tổng fact | Baseline nhận đúng | Candidate nhận đúng | Cặp có phát biểu không được hỗ trợ: gốc → mới |','|---|---|---:|---:|---:|---:|']
for cohort,label in [('new','Scene mới'),('old','Diagnostic cũ')]:
    for domain in ['Real','Render']:
        s=stats[f'{cohort}/{domain}/natural'];b=s['baseline'];a=s['invariance'];lines.append(f"| {label} | {domain} | {b['possible_facts']} | {b['supported_fact_hits']} | {a['supported_fact_hits']} | {b['unsupported_claim_pairs']} → {a['unsupported_claim_pairs']} |")
lines+=['','Một cặp quần áo mới có lẫn thay khung hình/che khuất chưa được gán nhãn chắc nên không vào số fact chính. Đủ nhãn và ghi chú ở eval_rubric và masked_assessments; không dựa vào caption model tự chấm.','',
'## Điều kiện đã kiểm tra','']
for name,passed in checks.items():lines.append(f"- {name}: {'đạt' if passed else 'không đạt'}")
lines+=['','Chỉ một seed/cấu hình. Những ảnh đánh giá đã được xem trong các lượt phát triển trước; cùng họ phép biến đổi với augmentation train, nên resampling shortcut là khả năng cần kiểm tra trên dữ liệu ngoài. Tập nhỏ nhiều cặp chung scene; chưa có bằng chứng cho góc nhìn 3D/parallax. Chưa chạy full-test benchmark cho candidate này, không suy CIDEr/BLEU toàn bộ từ diagnostic.','',
'Trọng số ở Volume `m3diff/invariance_sft_v1/m3diff-invariance-lora`. Code, train recipe, hash dữ liệu, log, caption raw, chấm từng cặp và khóa giải đều được lưu. Các job phải được kiểm tra dừng ở modal_final_status trước khi giao kết quả.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_invariance_sft.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if p.is_file() and '__pycache__' not in rel.parts and p.suffix in ['.py','.json','.jsonl','.txt','.log','.md','.csv'] and p.stat().st_size<20_000_000:z.write(p,str(rel))
print(json.dumps({'decision':decision,'primary_geometry':stats['new/all/transformed'],'new_natural':stats['new/all/natural'],'old_natural':stats['old/all/natural']},ensure_ascii=False,indent=2))
