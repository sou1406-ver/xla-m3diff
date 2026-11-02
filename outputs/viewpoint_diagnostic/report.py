"""Decode saved masked scoring only after review; never generates new labels."""
from pathlib import Path
import collections,hashlib,json,random,zipfile
ROOT=Path(__file__).resolve().parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
preds=load('results/masked_predictions.json');reviews=load('masked_assessments.json');key=load('results/mask_key.json');rubric=load('scoring_rubric.json')
assert len(preds)==len(reviews['cases'])==60
assert {r['id'] for r in preds}=={r['id'] for r in reviews['cases']}
lookup={r['id']:r for r in preds};decoded=[]
for r in reviews['cases']:
    p=lookup[r['id']]
    for c in [1,2]:
        q=r[f'candidate_{c}'];arm=key[r['id']][f'candidate_{c}']
        assert q['fp'] in [0,1] and q['ack'] in [0,1]
        facts=q.get('facts',[])
        assert len(facts)==len(set(facts))
        assert all(1<=i<=len(rubric['natural_pairs']['facts'][p['scene']]) for i in facts)
        if p['condition']!='natural':assert not facts
        decoded.append({k:p[k] for k in ['id','scene','partition','split','condition']}|{'arm':arm,**q})
save('decoded_assessments.json',{'reviewer':reviews['reviewer'],'masked_scores_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':decoded})
tables={}
for partition in ['dev','validation','all']:
    for split in ['Real','Render','all']:
        for group in ['identity','transformed','geometry','natural']:
            group_rows=[r for r in decoded if (partition=='all' or r['partition']==partition) and (split=='all' or r['split']==split) and
                        (r['condition']=='identity' if group=='identity' else r['condition'] not in ['identity','natural'] if group=='transformed' else r['condition']!='natural' if group=='geometry' else r['condition']=='natural')]
            stats={}
            for arm in ['baseline','camera_aware']:
                rows=[r for r in group_rows if r['arm']==arm]
                if not rows:continue
                stats[arm]={'n':len(rows),'false_positive_pairs':sum(r['fp'] for r in rows),'false_positive_rate':sum(r['fp'] for r in rows)/len(rows),
                            'geometry_acknowledged':sum(r['ack'] for r in rows),'supported_fact_hits':sum(len(r.get('facts',[])) for r in rows),
                            'unsupported_claim_count':sum(len(r.get('unsupported',[])) for r in rows),
                            'illumination_claim_pairs':sum(r['illumination_fp'] for r in rows),
                            'other_apparent_geometry_errors':sum(r['other_error'] for r in rows),
                            'identity_difference_pairs':sum(r['identity_difference'] for r in rows)}
                if group=='natural':stats[arm]['possible_facts']=sum(len(rubric['natural_pairs']['facts'][r['scene']]) for r in rows)
            tables[f'{partition}/{split}/{group}']=stats
save('metrics.json',tables)
intervals={};rng=random.Random(2026102720)
for partition in ['dev','validation','all']:
    rows=[r for r in decoded if (partition=='all' or r['partition']==partition) and r['condition'] not in ['identity','natural']]
    scenes=sorted({r['scene'] for r in rows});deltas=[]
    for scene in scenes:
        b=[r['fp'] for r in rows if r['scene']==scene and r['arm']=='baseline'];a=[r['fp'] for r in rows if r['scene']==scene and r['arm']=='camera_aware']
        deltas.append(100*(sum(a)/len(a)-sum(b)/len(b)))
    draws=sorted(sum(rng.choices(deltas,k=len(deltas)))/len(deltas) for _ in range(10000))
    intervals[partition]={'n_scenes':len(scenes),'delta_false_positive_percentage_points_camera_minus_baseline':sum(deltas)/len(deltas),'scene_bootstrap_CI95':[draws[249],draws[9749]],'interpretation':'Small descriptive diagnostic, not external validation or a multiple-seed confidence interval.'}
save('uncertainty.json',intervals)
g=tables['validation/all/geometry'];n=tables['validation/all/natural']
checks={'validation_geometry_false_positives_decrease':g['camera_aware']['false_positive_pairs']<g['baseline']['false_positive_pairs'],
        'validation_natural_fact_hits_do_not_drop':n['camera_aware']['supported_fact_hits']>=n['baseline']['supported_fact_hits']}
decision={'checks':checks,'promising_on_this_diagnostic_only':all(checks.values()),'not_a_rotation_or_3D_viewpoint_benchmark_claim':True,'next_action':'Do not launch further training or prompt search in this run; release GPU and preserve all predictions.'}
save('decision.json',decision)
lines=['# Kiểm tra góc xoay/zoom M3Diff','',
'So sánh checkpoint gốc với hai prompt cố định, **không train thêm**: prompt gốc và prompt nhắc phân biệt camera/crop với thay đổi vật.','',
'12 scene, mỗi scene có 4 đối chứng cùng ảnh (giống hệt, zoom 1,10×, xoay 8° có crop an toàn, xoay −8° + zoom) và 1 cặp tự nhiên có thay đổi. Tổng 60 cặp × 2 prompt = 120 caption. Nguồn là ảnh đã xem trong các thử nghiệm trước; tách 6 scene dev/6 scene validation chỉ áp dụng trong lượt diagnostic này.','',
'Caption được cùng lọc câu lặp, xáo tên prompt theo từng cặp. Trợ lý chấm và lưu trước khi giải khóa; không phải chấm mù độc lập bởi con người. Quy tắc và danh sách fact đã ghi trước khi đọc output mới.','',
'## Báo sai thay đổi vật','',
'Số cặp có ít nhất một khẳng định thay vật/màu/tư thế/số lượng/vị trí vật không được ảnh hỗ trợ. Camera/crop làm vật lệch hoặc khuất mép không tính là thay đổi vật thật. Khẳng định ánh sáng đổi được ghi riêng; trường hợp chỉ nói vị trí/kích thước trong khung nhưng không rõ đang nói vật dịch chuyển thật được chấm bảo thủ, có ghi chú.','',
'| Nhóm | Số cặp | Prompt gốc | Prompt xét camera |','|---|---:|---:|---:|']
for partition in ['dev','validation','all']:
    for group,label in [('identity','ảnh giống hệt'),('transformed','chỉ xoay/zoom')]:
        s=tables[f'{partition}/all/{group}'];b=s['baseline'];a=s['camera_aware']
        lines.append(f"| {partition}: {label} | {b['n']} | {b['false_positive_pairs']} | {a['false_positive_pairs']} |")
lines+=['','### Kiểm tra tránh chuyển loại lỗi','',
'| Validation | Prompt gốc | Prompt xét camera |','|---|---:|---:|']
for group,metric,label in [('identity','identity_difference_pairs','Ảnh giống hệt nhưng nói có khác biệt /6'),('transformed','illumination_claim_pairs','Chỉ xoay/zoom nhưng khẳng định ánh sáng đổi /18'),('transformed','other_apparent_geometry_errors','Mô tả sai vị trí/kích thước trong ảnh /18'),('transformed','geometry_acknowledged','Nêu rõ camera/framing đổi /18')]:
    s=tables[f'validation/all/{group}'];lines.append(f"| {label} | {s['baseline'][metric]} | {s['camera_aware'][metric]} |")
lines+=['','Khẳng định ánh sáng đổi không gộp vào lỗi thay vật. Crop có thể đổi phân bố sáng toàn ảnh, nên phát biểu “ảnh sáng hơn” không tự chứng minh có đổi nguồn sáng. Cần đọc caption và ghi chú, không coi việc bớt nói vật đổi nhưng chuyển sang suy ánh sáng là đã hiểu hình học.']
lines+=['','## Có bỏ sót thay đổi thật không?','',
'Mỗi fact là một thay đổi cụ thể đã khóa trước, xem `scoring_rubric.json`. Classroom chỉ thay sáng và được ghi là illumination-only trong manifest.','',
'| Nhóm | Tổng fact | Fact đúng: gốc | Fact đúng: xét camera | Cặp có khẳng định sai: gốc → mới |','|---|---:|---:|---:|---:|']
for partition in ['dev','validation','all']:
    s=tables[f'{partition}/all/natural'];b=s['baseline'];a=s['camera_aware']
    lines.append(f"| {partition} | {b['possible_facts']} | {b['supported_fact_hits']} | {a['supported_fact_hits']} | {b['false_positive_pairs']} → {a['false_positive_pairs']} |")
lines+=['','## Kết luận','',
('Prompt xét camera đạt điều kiện gợi ý trên diagnostic nhỏ này: giảm báo sai ở validation mà không giảm tổng fact đúng trên các cặp tự nhiên validation. Chưa đủ để thay cấu hình chính hoặc tuyên bố tăng năng lực hiểu ảnh.' if all(checks.values()) else 'Prompt xét camera không đạt đủ điều kiện đã định: cần vừa giảm báo sai trên validation vừa không giảm tổng fact đúng trên cặp tự nhiên validation. Không chọn thay prompt gốc.'),'',
'Đây là phép biến đổi 2D, không mô phỏng camera đổi góc nhìn 3D. Xoay có kèm mức phóng tối thiểu để không sinh viền đen/ảnh giả; ma trận và scale thật lưu ở manifest. Mỗi miền chỉ 6 scene, tập validation chỉ 6 scene tổng cộng; các điều kiện trong cùng scene tương quan. Bootstrap theo scene mô tả bất định, không dùng để tuyên bố cải thiện tổng quát.','',
'Mọi caption, điểm chấm, trường hợp sai và protocol có trong gói kết quả. Script Modal có timeout và tự trả GPU khi xong, không tạo endpoint thường trực.']
(ROOT/'PROMPT_KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_viewpoint_diagnostic.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix in ['.py','.json','.jsonl','.md','.log','.ipynb','.csv'] and 'dataset' not in p.relative_to(ROOT).parts:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'validation_geometry':g,'validation_natural':n,'decision':decision,'uncertainty':intervals['validation']},ensure_ascii=False,indent=2))
