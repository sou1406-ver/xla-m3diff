"""Build user report from completed artifacts; never invent missing full scores."""
from pathlib import Path
import json
ROOT=Path(__file__).parent;OUT=ROOT.parent;res=ROOT/'results'
audit=json.loads((res/'completion_audit.json').read_text(encoding='utf8'))
scores=json.loads((res/'summary_x100.json').read_text(encoding='utf8'))
budget=json.loads((OUT/'modal_budget/latest_budget.json').read_text(encoding='utf8'))
def value(split,arm,processing):return next(r for r in scores if r['split']==split and r['arm']==arm and r['processing']==processing)
lines=['# Kết quả M3Diff mới nhất','',
'Đã tái lập inference/evaluation từ checkpoint công bố trên đủ **803 Real +767 Render**. Đây là tái lập kết quả từ checkpoint; phần cải thiện có training LoRA riêng. Không cần train lại khi chuyển máy: giữ base đúng revision, adapter và môi trường đi kèm.','',
'**Bản LoRA không đạt điều kiện thay model gốc.** Trên full test, CIDEr sau cùng bộ lọc giảm từ33,754 xuống32,138 ở Real và từ30,647 xuống19,963 ở Render; BLEU-4, METEOR và ROUGE-L cũng giảm ở cả hai tập. Nó giảm một loại lỗi bịa thay đổi vật trong bộ diagnostic, nhưng chưa cải thiện lỗi tổng thể khi tính cả ánh sáng/khả năng nhìn thấy. Giữ model gốc làm mặc định.','',
f'## Đánh giá caption chính thức — {audit["n_completed"]}/1570 mẫu','',
('Đã hoàn thành toàn bộ hai tập test.' if audit['full_test_complete'] else '**Chưa hoàn thành full test:** chỉ chấm các ID đã chạy xong; baseline được chấm lại trên đúng các ID đó. Không so CIDEr tập con với điểm full baseline.'),'',
'Điểm dưới đây nhân100. Hai bản dùng cùng câu hỏi gốc, cùng ID/reference, BF16, greedy, tối đa1024 token. LoRA giữ FP32 không merge; chọn adapter trước khi đọc điểm full. `dedup` là lọc câu lặp nguyên văn v1, áp dụng bằng nhau cho hai bản.','',
'| Tập | Xử lý | n | BLEU-4 gốc → LoRA | METEOR gốc → LoRA | ROUGE-L gốc → LoRA | CIDEr gốc → LoRA |',
'|---|---|---:|---:|---:|---:|---:|']
for split in ['Real','Render']:
 for processing in ['raw','dedup','dedup_joined_v2']:
  a=value(split,'baseline',processing);b=value(split,'mixed_objective',processing)
  # Official scorer names are kept in source JSON; support its BLEU naming.
  def metric(row,name):
   for key in [name, name.replace('Bleu','BLEU')]:
    if key in row:return row[key]
   raise KeyError((name,list(row)))
  entries=[f'{metric(a,k):.3f} → {metric(b,k):.3f}' for k in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]
  lines.append(f'| {split} | {processing} | {a["n"]} | '+ ' | '.join(entries)+' |')
lines+=['','Không chọn lại model bằng điểm test. Điều kiện đưa vào dùng chính đã thất bại ở kiểm tra lỗi tổng hợp bên dưới, dù một chỉ số caption có thể tăng. Điểm caption không chứng minh hiểu góc nhìn3D.','',
'Baseline full chạy NVIDIA A10; candidate chạy4 chunk A10G và1 chunk A10, cùng họ GPU và cấu hình nhưng không phải phép thử ghép cặp trên cùng một GPU vật lý. Không khẳng định caption greedy khớp từng chữ khi đổi thiết bị. Đây là điểm đo thực tế để quyết định giữ baseline; muốn tách hoàn toàn tác động adapter cần chạy lại cả hai bản trên cùng môi trường/GPU.','',
'## Kiểm tra xoay/zoom và đối chứng','',
'| Phép thử | Model gốc | LoRA mixed | Diễn giải |',
'|---|---:|---:|---|',
'| Pilot: bịa thay đổi vật,32 ca hình học |31/32|21/32|Giảm loại lỗi hẹp|',
'| Xác nhận: bịa thay đổi vật,48 ca hình học |36/48|29/48|Có cải thiện hẹp|',
'| Xác nhận: bịa khác biệt khi hai ảnh giống hệt |16/16|6/16|LoRA giảm lỗi; guard RGB riêng xử lý chắc chắn ca trùng pixel|',
'| Xác nhận: lỗi vật/ánh sáng/visibility/giải thích hình học |44/48|44/48|Không cải thiện tổng thể|',
'| Xác nhận: fact thật nhận đúng |19/24|20/24|Không mất tổng fact trong bộ này|',
'| Xác nhận: cặp tự nhiên có claim bịa |9/16|9/16|Không giảm|','',
'Các nhãn do trợ lý chấm, lưu đánh giá che tên model trước khi mở khóa; chưa có người chấm độc lập. Bộ xác nhận có16 cặp nguồn nhưng11 cặp thuộc bối cảnh quen, chỉ5 bối cảnh Real ít quen và không có Render mới hoàn toàn. Biến đổi2D tổng hợp không đại diện đầy đủ cho đổi góc chụp3D.','',
'Đối chứng cùng ảnh/thứ tự/khởi tạo nhưng bỏ loss âm làm mất fact thật, nên không chọn. Bản chia đều10 kiểu câu hỏi cũng mất fact ở Real, nên không chọn. Probe4 ca ×10 câu hỏi không chứng minh hiệu quả chỉ đến từ một kiểu prompt. Câu “more visible” có thể ám chỉ khung hình rộng hơn; không tự coi mọi câu như vậy là sai ánh sáng.','',
'Căn chỉnh ảnh xấp xỉ không được dùng để tự kết luận không đổi: kiểm tra mở rộng đã chặn nhầm20/56 ca stress có sửa nội dung. Chỉ guard RGB trùng từng pixel được phép bỏ qua model. Lọc câu lặp là xử lý văn bản, không sửa claim bịa.','',
'## Mang sang máy khác','',
'Giải nén `m3diff_portable.zip`, đọc README, mở `m3diff-inference-portable.ipynb` trên Linux/WSL2/server GPU với Python3.10. Tải base đúng revision một lần, sửa đường dẫn hai ảnh rồi chạy. Chỉ tải/cài và inference, không train lại. Base khoảng14GB không nằm trong ZIP.','',
'Adapter SHA256: `6b8d81729b03f83e9c03de9a78fb1aa895a47088c32c4435115ac39b77a1fb5f`. Đã kiểm tra hash đủ4 file, CRC weights, nạp đúng392 tensor và portable runner khớp caption2/2 với runner đánh giá trên GPU. Notebook kiểm tra cú pháp; chưa RunAll trên một máy GPU mới độc lập.','',
'## Hồ sơ và credit','',
'- `mixed_full_benchmark/results/summary_x100.json`: mọi metric và xử lý của cả hai bản.',
'- `mixed_full_benchmark/results/completion_audit.json`: đủ/thiếu ID.',
'- `mixed_full_benchmark/results/caption_behavior_audit.json`: độ dài/tần suất caption, không phải nhãn đúng sai.',
'- `invariance_confirmation/KET_QUA.md`: tradeoff và giới hạn bộ xác nhận.',
'- `modal_budget/`: log ngân sách, reservation và báo cáo chi phí.',
f'- Chụp ngân sách lúc {budget["time_utc"]}: API consumption upper ${budget["api_consumption_upper_usd"]}; còn ${budget["remaining_guarded_usd"]} sau dự phòng của sổ theo dõi. Đây không phải số dư tiền mặt thời gian thực. Không mua thêm credit.',
'']
gpu_check=OUT/'modal_budget/FINAL_GPU_CHECK.json'
if gpu_check.exists():
 gpu=json.loads(gpu_check.read_text(encoding='utf8'))
 if gpu['all_own_recent_apps_stopped'] and not gpu['active_own_apps']:lines += [f'Đã kiểm tra lúc {gpu["time_utc"]}: không còn app của công việc này chạy, các app gần đây đều stopped và0 task. GPU đã được trả. Nguồn kiểm tra: `modal_budget/final_apps.json`.','']
cap_report=OUT/'caption_cap_probe/KET_QUA.md'
if cap_report.exists():lines += ['## Kiểm tra độ dài caption bổ sung','',cap_report.read_text(encoding='utf8').replace('# Thử giới hạn độ dài caption','').strip(),'']
text='\n'.join(lines)
(OUT/'M3DIFF_KET_QUA_MOI_NHAT.md').write_text(text,encoding='utf8')
(OUT/'m3diff_portable/EVALUATION.md').write_text(text,encoding='utf8')
print({'report_written':True,'full_test_complete':audit['full_test_complete'],'n':audit['n_completed']})
