"""Report the frozen-v1 extension; no threshold search or model scoring."""
from pathlib import Path
import collections,csv,hashlib,json,zipfile
from safe_pipeline import route_features
ROOT=Path(__file__).resolve().parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
lock=load('selection_locked.json');audit=load('results/audit.json');composed=load('composed_results/composed_audit.json');review=load('natural_review.json')
assert len(audit)==104 and len(composed)==24
assert hashlib.sha256((ROOT/'registration_gate_frozen.py').read_bytes()).hexdigest()==lock['frozen_registration_source_sha256']
rows=audit+composed;assert len({r['id'] for r in rows})==128
assert load('safe_check/SUCCESS.json')['all_nonidentity_captions_unchanged']
for r in rows:r['safe_policy']=route_features(r['features'],lock['frozen_thresholds'])
assert all(not r['safe_policy']['replace_caption'] for r in rows if not r['features']['exact_identity'])
stats={}
for r in rows:
    key=r['kind']+'/'+r['condition'];entry=stats.setdefault(key,{'n':0,'v1_accepts_no_change':0,'safe_policy_replacements':0,'safe_advisory_flags':0})
    entry['n']+=1;entry['v1_accepts_no_change']+=int(r['decision']['accept_no_scene_change']);entry['safe_policy_replacements']+=int(r['safe_policy']['replace_caption']);entry['safe_advisory_flags']+=int(r['safe_policy']['needs_review'])
confirmed={r['scene'] for r in review['pairs'] if r['status']=='confirmed_change'}
natural=[r for r in audit if r['condition']=='natural' and r['scene'] in confirmed]
primary=[r for r in rows if r['kind'] in ['primary_stress','composed_primary_stress']]
failures=[r['id'] for r in primary if r['decision']['accept_no_scene_change']]
decision={'frozen_v1_primary_stress_false_suppressions':len(failures),'primary_stress_n':len(primary),
 'confirmed_natural_false_suppressions':sum(r['decision']['accept_no_scene_change'] for r in natural),'confirmed_natural_n':len(natural),
 'uncertain_natural_n':1,'v1_automatic_approximate_caption_replacement_allowed':not bool(failures),
 'current_policy':'Only exact decoded-pixel identity may replace caption. Approximate alignment is advisory and preserves M3Diff caption.',
 'safe_policy_changed_case_replacements':sum(r['safe_policy']['replace_caption'] for r in rows if r['kind']!='nochange'),
 'not_a_new_M3Diff_caption_metric':'No model inference performed in this extension. Synthetic appearance edits are not natural semantic object changes.',
 'known_failed_ids':failures}
assert failures and decision['safe_policy_changed_case_replacements']==0
save('summary.json',stats);save('decision.json',decision);save('safe_policy_audit.json',rows)
with (ROOT/'case_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['id','split','kind','condition','v1_nochange','safe_replaces_caption','safe_review_flag','changed_native_pixels','overlap','mean_rgb_error','p99_error'])
    for r in rows:w.writerow([r['id'],r['split'],r['kind'],r['condition'],r['decision']['accept_no_scene_change'],r['safe_policy']['replace_caption'],r['safe_policy']['needs_review'],r.get('changed_native_pixels'),r['features'].get('overlap'),r['features'].get('mean_absolute_rgb_error'),r['features'].get('p99_max_channel_error')])
lines=['# Kiểm tra tiếp: zoom-out và thay đổi nhỏ','',
'**Kết luận: không dùng bộ căn chỉnh v1 để tự thay caption bằng “không đổi”. Có phản ví dụ rõ về ảnh đã bị sửa nhưng bộ chặn vẫn cho qua. Căn chỉnh gần đúng chuyển thành gợi ý; chỉ ảnh giống hệt sau giải mã mới được trả tự động “không khác biệt”.**','',
'Đã giữ nguyên code/hash/ngưỡng v1 và kiểm tra 8 scene khác bộ diagnostic trước: 4 Real, 4 Render. Ảnh thuộc OmniDiff test đã được checkpoint gốc chạy trong toàn bộ benchmark trước đây; đây không phải dữ liệu ngoài hoàn toàn mới. Không gọi GPU hay sinh caption mới trong phép CPU này.','',
'## Độ bao phủ trên 40 cặp không thay đổi vật','',
'| Điều kiện | V1 chấp nhận không đổi / 8 |','|---|---:|']
for c in lock['nochange_conditions']:lines.append(f"| {c} | {stats['nochange/'+c]['v1_accepts_no_change']} |")
lines+=['','Zoom-out ở đây là đảo chiều cặp ảnh crop/zoom-in, không dựng thêm phần cảnh giả. V1 đòi ít nhất 95% ảnh đích nằm trong phần đối chiếu, nên zoom-out có vùng mới lộ ra bị fallback. Đó là giới hạn bao phủ, không phải bằng chứng model đã hiểu zoom-out sai.','',
'## Thay đổi tổng hợp có bị bỏ qua?','',
'Mỗi trường hợp có chỉnh sửa pixel biết chắc đã xảy ra. Đây là stress appearance tổng hợp, không được trình bày như tỷ lệ bỏ sót vật thể thật ngoài đời.','',
'| Stress chính | V1 trả nhầm “không đổi” / 8 |','|---|---:|']
for c in lock['primary_stress']:lines.append(f"| {c} | {stats['primary_stress/'+c]['v1_accepts_no_change']} |")
lines+=['','| Vừa đổi hình học vừa sửa mảng màu 32×32 | V1 trả nhầm “không đổi” / 8 |','|---|---:|']
for c in ['zoom_in_1p10','roll_8_safe','zoom_out_1p10']:lines.append(f"| {c} | {stats['composed_primary_stress/'+c]['v1_accepts_no_change']} |")
lines+=['',f"Tổng stress chính bị chặn nhầm: **{len(failures)}/{len(primary)}**. Không nới hay dò lại ngưỡng trên các kết quả này.",'',
'Các stress nhạy hơn (mảng nhỏ +4 RGB, tăng sáng toàn ảnh +1, đổi một pixel) lưu riêng trong CSV. Chúng thăm giới hạn độ phân giải/dung sai; không dùng để khẳng định một khác biệt nhỏ đến vậy phải được mô tả trong caption ngữ nghĩa.','',
'## Cặp tự nhiên','',
f"Đã xem ảnh trước khi đọc kết quả bộ chặn: 7 cặp có thay đổi rõ, 1 cặp quần áo có lẫn khung hình/che khuất chưa gán nhãn chắc. V1 không chặn nhầm cặp nào trong **{len(natural)} cặp thay đổi rõ**. Điều này không xóa các phản ví dụ appearance tổng hợp, cũng không phải phép đo recall caption mới.",'',
'## Đã sửa pipeline','',
'`safe_pipeline.py` giữ nguyên caption M3Diff cho mọi cặp không giống hệt pixel. Cờ `--registration-advice` chỉ ghi thông tin căn chỉnh, phần ảnh chung và gợi ý kiểm tra; không ghi đè caption. Không có cờ bật lại việc thay caption gần đúng trong bản này.','',
'```powershell',
'python safe_pipeline.py --manifest pairs.json --image-root images --input captions.jsonl --output captions_safe.jsonl --audit review_flags.json',
'```','',
'Để có gợi ý căn chỉnh, thêm `--registration-advice` và cài OpenCV theo README. Input/output/manifest/audit phải là tệp khác nhau. ID, thứ tự và metadata được giữ.','',
'Đã chạy CLI đầu-cuối bằng CPU trên 5 trường hợp: giống hệt, zoom-out, thay mảng màu nhỏ, vừa zoom vừa sửa mảng, và cặp tự nhiên thêm người. Chỉ ảnh giống hệt bị thay caption; phản ví dụ mà v1 cho qua đã giữ nguyên caption gốc. `safe_check/SUCCESS.json` ghi bằng chứng. Chính sách cũng được áp dụng lên 128 feature đã lưu: không thay caption ở bất kỳ trường hợp không giống hệt nào.','',
'## Ý nghĩa cho hướng cải thiện','',
'Kết quả tích cực 14/18 → 5/18 trước đây vẫn là số đo đúng trên diagnostic cũ, nhưng không đủ để bật bộ chặn gần đúng tự động. Vấn đề còn lại là model phải học phân biệt thay đổi vật với thay đổi khung hình; một bộ so pixel có dung sai không thể chứng minh không có thay đổi ngữ nghĩa. Một pilot fine-tune bất biến góc/zoom được tách riêng ở `../invariance_sft/`, dùng ảnh train và không thay các kết quả CPU này.','',
'Ảnh minh chứng có BEFORE / AFTER / chênh lệch pixel ×12. Ảnh chỉ minh họa phản ví dụ, không phải annotation vật thể. Toàn bộ thử nghiệm extension dùng CPU, các function đều có timeout và không triển khai endpoint thường trực.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_viewpoint_extension.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if p.is_file() and '__pycache__' not in rel.parts and p.suffix in ['.py','.json','.jsonl','.md','.csv','.jpg']:z.write(p,str(rel))
print(json.dumps({k:v for k,v in decision.items() if k!='known_failed_ids'},ensure_ascii=False,indent=2))
