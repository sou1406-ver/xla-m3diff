"""Evaluate the previously locked CPU policy once on saved validation features."""
import hashlib,json,zipfile
from pathlib import Path
from registration_gate import decide
from deduplicate_caption import deduplicate_caption
ROOT=Path(__file__).resolve().parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
protocol=load('registration_protocol.json');thresholds=protocol['thresholds']
assert hashlib.sha256((ROOT/'registration_gate.py').read_bytes()).hexdigest()==protocol['registration_source_sha256']
features=load('registration_dev_features.json')+load('registration_validation_features.json')
assert len(features)==len({r['id'] for r in features})==60
manifest=load('manifest.json');assert {r['id'] for r in features}=={r['id'] for r in manifest}
raw=[json.loads(l) for l in (ROOT/'results/baseline.jsonl').read_text().splitlines() if l.strip()]
assert len(raw)==len({r['id'] for r in raw})==60
clean={r['id']:{**r,'caption':deduplicate_caption(r['caption'])[0]} for r in raw}
(ROOT/'baseline_clean.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in clean.values()),encoding='utf8')
old={r['id']:r for r in load('decoded_assessments.json')['rows'] if r['arm']=='baseline'}
decisions=[{**r,'decision':decide(r['features'],thresholds)} for r in features]
stress=[{**r,'decision':decide(r['features'],thresholds)} for r in load('registration_stress_features.json')]
assert len(stress)==18
save('registration_decisions.json',decisions);save('registration_stress_decisions.json',stress)
summary={}
for partition in ['dev','validation','all']:
    rows=[r for r in decisions if partition=='all' or r['partition']==partition]
    natural=[r for r in rows if r['condition']=='natural'];identity=[r for r in rows if r['condition']=='identity'];trans=[r for r in rows if r['condition'] not in ['identity','natural']]
    geo=identity+trans
    summary[partition]={'geometry_pairs':len(geo),'identity_pairs':len(identity),'transformed_pairs':len(trans),
      'identity_routed':sum(r['decision']['accept_no_scene_change'] for r in identity),
      'transformed_routed':sum(r['decision']['accept_no_scene_change'] for r in trans),
      'natural_pairs':len(natural),'natural_wrongly_routed':sum(r['decision']['accept_no_scene_change'] for r in natural),
      'physical_fp_before_geometry':sum(old[r['id']]['fp'] for r in geo),
      'physical_fp_after_geometry':sum(old[r['id']]['fp'] and not r['decision']['accept_no_scene_change'] for r in geo),
      'physical_fp_before_transformed':sum(old[r['id']]['fp'] for r in trans),
      'physical_fp_after_transformed':sum(old[r['id']]['fp'] and not r['decision']['accept_no_scene_change'] for r in trans),
      'natural_fact_hits_before':sum(len(old[r['id']]['facts']) for r in natural),
      'natural_fact_hits_after':sum(len(old[r['id']]['facts']) for r in natural if not r['decision']['accept_no_scene_change'])}
checks={'routes_nonidentity_validation':summary['validation']['transformed_routed']>0,
        'no_natural_validation_suppressed':summary['validation']['natural_wrongly_routed']==0,
        'rejects_all_stress_changes':not any(r['decision']['accept_no_scene_change'] for r in stress)}
result={'counts':summary,'stress_changes':len(stress),'stress_wrongly_routed':sum(r['decision']['accept_no_scene_change'] for r in stress),'fixed_gate_checks':checks,
        'promising_on_diagnostic_only':all(checks.values()),'default_cli_mode':'identity-only','approximate_registration':'explicit opt-in; heuristic, not proof of scene identity'}
result['transformed_coverage_by_domain']={s:{'n':sum(r['split']==s and r['condition'] not in ['identity','natural'] for r in decisions),'routed':sum(r['split']==s and r['condition'] not in ['identity','natural'] and r['decision']['accept_no_scene_change'] for r in decisions)} for s in ['Real','Render']}
save('registration_results.json',result)
out=[]
for r in decisions:
    row=clean[r['id']];d=r['decision'];out.append({**row,'caption':d['caption'] if d['accept_no_scene_change'] else row['caption']})
(ROOT/'registration_guarded.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out),encoding='utf8')
for r in decisions:
    if not r['decision']['accept_no_scene_change']:assert next(o for o in out if o['id']==r['id'])==clean[r['id']]
if summary['all']['natural_wrongly_routed']==0:
    for r in decisions:
        if r['condition']=='natural':assert next(o for o in out if o['id']==r['id'])==clean[r['id']]
lines=['# Kết quả tiếp theo: kiểm tra camera trước M3Diff','',
'**Có tín hiệu tốt hơn ở bộ kiểm tra có kiểm soát: căn chỉnh ảnh + kiểm tra phần còn khác giúp tránh một số caption bịa khi chỉ xoay/zoom. Chưa đủ bằng chứng cho đổi góc nhìn 3D hoặc dữ liệu mới ngoài bộ này.**','',
'## Cách đang kiểm tra','',
'Ảnh giống hệt từng pixel sau giải mã được trả “không có thay đổi”. Với ảnh khác, SIFT/RANSAC ước lượng xoay/phóng/tịnh tiến toàn ảnh; chỉ khi phần ảnh chung khớp rất sát và không còn vùng sai khác rõ thì trả mô tả đổi khung hình. Trường hợp không đủ chắc giữ nguyên caption checkpoint M3Diff gốc sau lọc câu lặp. Không cập nhật trọng số, không dùng LocateAnything, không thay bằng prompt mới.','',
'Ngưỡng chọn trên 6 scene dev rồi khóa trước khi tính 6 scene validation. Những cảnh furniture nhiều chi tiết bị bỏ qua thay vì nới ngưỡng cho qua. Kiểm tra thêm 18 ảnh có thay đổi tổng hợp: đảo màu mảng 8×8, nét 2×32 và tăng sáng RGB +8. Các stress này kiểm tra bộ chặn, không đại diện một benchmark thay đổi vật tự nhiên.','',
'## Kết quả bộ căn chỉnh','',
'| Nhóm | Chỉ xoay/zoom được nhận ra | Ảnh giống hệt nhận ra | Cặp thay đổi thật bị trả nhầm “không đổi” |','|---|---:|---:|---:|']
for p,label in [('dev','Dev'),('validation','Validation'),('all','Tổng')]:
    s=summary[p];lines.append(f"| {label} | {s['transformed_routed']}/{s['transformed_pairs']} | {s['identity_routed']}/{s['identity_pairs']} | {s['natural_wrongly_routed']}/{s['natural_pairs']} |")
lines+=['','| Lỗi bịa thay đổi vật | Trước | Sau bộ căn chỉnh |','|---|---:|---:|']
for p,label in [('validation','Validation'),('all','Tổng')]:
    s=summary[p]
    lines.append(f"| {label}: chỉ xoay/zoom | {s['physical_fp_before_transformed']}/{s['transformed_pairs']} | {s['physical_fp_after_transformed']}/{s['transformed_pairs']} |")
    lines.append(f"| {label}: gồm cả ảnh giống hệt | {s['physical_fp_before_geometry']}/{s['geometry_pairs']} | {s['physical_fp_after_geometry']}/{s['geometry_pairs']} |")
lines+=['',f"Stress có thay đổi tổng hợp bị chặn nhầm: **{result['stress_wrongly_routed']}/18**.",'',
f"Mức bao phủ các cặp xoay/zoom-in khác nhau theo miền: Real **{result['transformed_coverage_by_domain']['Real']['routed']}/18**, Render **{result['transformed_coverage_by_domain']['Render']['routed']}/18**. Các trường hợp còn lại giữ caption M3Diff, không tự ép thành không đổi.",'',
('Bộ căn chỉnh đạt điều kiện cố định trong diagnostic này. Cả 12 caption trên cặp tự nhiên được giữ nguyên từng ký tự sau lọc lặp; vì vậy nó không làm mất thêm thay đổi thật trong mẫu đã thử, nhưng cũng chưa sửa các lỗi sẵn có của M3Diff trên các cặp đó.' if all(checks.values()) and summary['all']['natural_wrongly_routed']==0 else 'Bộ căn chỉnh chưa đạt đủ điều kiện kiểm tra. Không bật phần căn chỉnh gần đúng mặc định; chỉ dùng nhánh ảnh giống hệt.'),'',
'Đây là giảm báo sai nhờ pipeline nhận biết một số cặp không đổi, không phải model đã học hiểu góc nhìn tốt hơn. Các câu do bộ chặn thay được đánh giá theo nguồn ảnh/phép biến đổi đã biết, không cần nhờ model tự chấm nó. Các caption fallback giữ điểm chấm trực quan đã lưu trước đó.','',
'## Lượt thử prompt','',
'Đã chạy 120 caption trên 60 cặp (hai prompt). Ở validation, lỗi nói vật thay đổi giảm 19/24 → 13/24, nhưng khẳng định ánh sáng đổi tăng và không caption nào nêu camera/framing. Tổng fact đúng trên 12 cặp tự nhiên giảm 9/22 → 6/22. Vì vậy chưa dùng prompt xét camera làm mặc định. `PROMPT_KET_QUA.md` có bảng đầy đủ.','',
'## Dùng mã','',
'Mặc định an toàn về nội dung ảnh: chỉ bắt ảnh giống hệt, không dùng SIFT.','',
'```powershell',
'python apply_registration_gate.py --manifest manifest.json --image-root dataset --input baseline_clean.jsonl --output identity_guarded.jsonl --audit identity_audit.json',
'```','',
'Thử căn chỉnh gần đúng bằng cờ `--mode registration --protocol registration_protocol.json`, cần OpenCV. Có thể gọi `try_no_change(before, after, mode, thresholds)` trước bước sinh caption; nếu trả fallback thì chạy M3Diff như cũ. Bản đánh giá hiện tại tái sử dụng caption đã sinh, không chạy lại GPU để tiết kiệm credit.','',
'## Giới hạn cần ghi trong báo cáo','',
'- Chỉ 12 scene, ảnh đã được xem trong các thử nghiệm trước; validation chỉ tách scene trong diagnostic này, không phải test mới độc lập. Người chấm là trợ lý Codex, chưa có người gán nhãn độc lập.',
'- Xoay 2D có kèm crop an toàn, zoom-in nhỏ 1,10×; chưa kiểm tra zoom-out, 3D viewpoint/parallax hoặc zoom lớn. Ảnh nhiều chi tiết và trường hợp không đủ khớp sẽ fallback.',
'- Kiểm tra ở tối đa 1.024 pixel cạnh dài và có dung sai màu: vẫn có thể bỏ qua thay đổi rất nhỏ/ít tương phản hoặc nằm ngoài vùng chung. 18 stress chưa bao phủ mọi kiểu thay đổi; không gọi đây là chứng minh “không có thay đổi”.',
'- Ngưỡng cần kiểm tra lại trên tập scene mới, đặc biệt vật nhỏ và đổi sáng nhẹ, trước khi bật căn chỉnh gần đúng cho toàn bộ hệ thống. CLI mặc định chỉ bật so ảnh giống hệt.',
'','Tất cả job GPU và CPU của lượt thử đã kết thúc. Không có endpoint hay lịch chạy thường trực.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_viewpoint_diagnostic.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if p.is_file() and not any(k in rel.parts for k in ['dataset','.deps','__pycache__']) and p.suffix in ['.py','.json','.jsonl','.md','.csv','.log','.txt']:z.write(p,str(rel))
with zipfile.ZipFile(ROOT.parent/'m3diff_viewpoint_previews.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in (ROOT/'boards').glob('*.jpg'):z.write(p,'boards/'+p.name)
    for n in ['manifest.json','review.csv','README.md']:z.write(ROOT/n,n)
print(json.dumps(result,ensure_ascii=False,indent=2))
