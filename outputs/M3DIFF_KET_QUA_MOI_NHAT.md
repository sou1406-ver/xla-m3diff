# Kết quả M3Diff mới nhất

Đã tái lập inference/evaluation từ checkpoint công bố trên đủ **803 Real +767 Render**. Đây là tái lập kết quả từ checkpoint; phần cải thiện có training LoRA riêng. Không cần train lại khi chuyển máy: giữ base đúng revision, adapter và môi trường đi kèm.

**Bản LoRA không đạt điều kiện thay model gốc.** Trên full test, CIDEr sau cùng bộ lọc giảm từ33,754 xuống32,138 ở Real và từ30,647 xuống19,963 ở Render; BLEU-4, METEOR và ROUGE-L cũng giảm ở cả hai tập. Nó giảm một loại lỗi bịa thay đổi vật trong bộ diagnostic, nhưng chưa cải thiện lỗi tổng thể khi tính cả ánh sáng/khả năng nhìn thấy. Giữ model gốc làm mặc định.

## Đánh giá caption chính thức — 1570/1570 mẫu

Đã hoàn thành toàn bộ hai tập test.

Điểm dưới đây nhân100. Hai bản dùng cùng câu hỏi gốc, cùng ID/reference, BF16, greedy, tối đa1024 token. LoRA giữ FP32 không merge; chọn adapter trước khi đọc điểm full. `dedup` là lọc câu lặp nguyên văn v1, áp dụng bằng nhau cho hai bản.

| Tập | Xử lý | n | BLEU-4 gốc → LoRA | METEOR gốc → LoRA | ROUGE-L gốc → LoRA | CIDEr gốc → LoRA |
|---|---|---:|---:|---:|---:|---:|
| Real | raw | 803 | 14.265 → 11.881 | 19.495 → 17.484 | 32.606 → 31.349 | 33.753 → 32.130 |
| Real | dedup | 803 | 14.861 → 11.873 | 19.593 → 17.486 | 32.653 → 31.354 | 33.754 → 32.138 |
| Real | dedup_joined_v2 | 803 | 14.861 → 11.873 | 19.593 → 17.486 | 32.653 → 31.354 | 33.754 → 32.138 |
| Render | raw | 767 | 16.917 → 13.713 | 20.141 → 16.280 | 35.751 → 31.471 | 30.493 → 19.998 |
| Render | dedup | 767 | 19.479 → 14.369 | 20.646 → 16.878 | 36.046 → 31.888 | 30.647 → 19.963 |
| Render | dedup_joined_v2 | 767 | 19.479 → 14.369 | 20.646 → 16.878 | 36.046 → 31.888 | 30.647 → 19.963 |

Không chọn lại model bằng điểm test. Điều kiện đưa vào dùng chính đã thất bại ở kiểm tra lỗi tổng hợp bên dưới, dù một chỉ số caption có thể tăng. Điểm caption không chứng minh hiểu góc nhìn3D.

Baseline full chạy NVIDIA A10; candidate chạy4 chunk A10G và1 chunk A10, cùng họ GPU và cấu hình nhưng không phải phép thử ghép cặp trên cùng một GPU vật lý. Không khẳng định caption greedy khớp từng chữ khi đổi thiết bị. Đây là điểm đo thực tế để quyết định giữ baseline; muốn tách hoàn toàn tác động adapter cần chạy lại cả hai bản trên cùng môi trường/GPU.

## Kiểm tra xoay/zoom và đối chứng

| Phép thử | Model gốc | LoRA mixed | Diễn giải |
|---|---:|---:|---|
| Pilot: bịa thay đổi vật,32 ca hình học |31/32|21/32|Giảm loại lỗi hẹp|
| Xác nhận: bịa thay đổi vật,48 ca hình học |36/48|29/48|Có cải thiện hẹp|
| Xác nhận: bịa khác biệt khi hai ảnh giống hệt |16/16|6/16|LoRA giảm lỗi; guard RGB riêng xử lý chắc chắn ca trùng pixel|
| Xác nhận: lỗi vật/ánh sáng/visibility/giải thích hình học |44/48|44/48|Không cải thiện tổng thể|
| Xác nhận: fact thật nhận đúng |19/24|20/24|Không mất tổng fact trong bộ này|
| Xác nhận: cặp tự nhiên có claim bịa |9/16|9/16|Không giảm|

Các nhãn do trợ lý chấm, lưu đánh giá che tên model trước khi mở khóa; chưa có người chấm độc lập. Bộ xác nhận có16 cặp nguồn nhưng11 cặp thuộc bối cảnh quen, chỉ5 bối cảnh Real ít quen và không có Render mới hoàn toàn. Biến đổi2D tổng hợp không đại diện đầy đủ cho đổi góc chụp3D.

Đối chứng cùng ảnh/thứ tự/khởi tạo nhưng bỏ loss âm làm mất fact thật, nên không chọn. Bản chia đều10 kiểu câu hỏi cũng mất fact ở Real, nên không chọn. Probe4 ca ×10 câu hỏi không chứng minh hiệu quả chỉ đến từ một kiểu prompt. Câu “more visible” có thể ám chỉ khung hình rộng hơn; không tự coi mọi câu như vậy là sai ánh sáng.

Căn chỉnh ảnh xấp xỉ không được dùng để tự kết luận không đổi: kiểm tra mở rộng đã chặn nhầm20/56 ca stress có sửa nội dung. Chỉ guard RGB trùng từng pixel được phép bỏ qua model. Lọc câu lặp là xử lý văn bản, không sửa claim bịa.

## Mang sang máy khác

Giải nén `m3diff_portable.zip`, đọc README, mở `m3diff-inference-portable.ipynb` trên Linux/WSL2/server GPU với Python3.10. Tải base đúng revision một lần, sửa đường dẫn hai ảnh rồi chạy. Chỉ tải/cài và inference, không train lại. Base khoảng14GB không nằm trong ZIP.

Adapter SHA256: `6b8d81729b03f83e9c03de9a78fb1aa895a47088c32c4435115ac39b77a1fb5f`. Đã kiểm tra hash đủ4 file, CRC weights, nạp đúng392 tensor và portable runner khớp caption2/2 với runner đánh giá trên GPU. Notebook kiểm tra cú pháp; chưa RunAll trên một máy GPU mới độc lập.

## Hồ sơ và credit

- `mixed_full_benchmark/results/summary_x100.json`: mọi metric và xử lý của cả hai bản.
- `mixed_full_benchmark/results/completion_audit.json`: đủ/thiếu ID.
- `mixed_full_benchmark/results/caption_behavior_audit.json`: độ dài/tần suất caption, không phải nhãn đúng sai.
- `invariance_confirmation/KET_QUA.md`: tradeoff và giới hạn bộ xác nhận.
- `modal_budget/`: log ngân sách, reservation và báo cáo chi phí.
- Chụp ngân sách lúc 2026-10-27T23:59:00.565765+00:00: API consumption upper $29.26; còn $0.26 sau dự phòng của sổ theo dõi. Đây không phải số dư tiền mặt thời gian thực. Không mua thêm credit.

Đã kiểm tra lúc 2026-10-27T23:59:56.830547+00:00: không còn app của công việc này chạy, các app gần đây đều stopped và0 task. GPU đã được trả. Nguồn kiểm tra: `modal_budget/final_apps.json`.

## Kiểm tra độ dài caption bổ sung

Thử nghiệm sau benchmark, không đổi điểm full hoặc mặc định1024 token. Không train thêm. Các ca dài được chọn từ lỗi đã biết, không phải mẫu ngẫu nhiên.

| Bản | Số ca | Natural khớp cache cũ | Natural chạm cap | Ca dài chạm cap |
|---|---:|---:|---:|---:|
| LoRA256 | 23 | 8/19 | 0 | 4/4 |
| base256 | 23 | 6/19 | 0 | 4/4 |
| base128 | 23 | 6/19 | 1 | 4/4 |

Cache natural cũ chạyA100, lượt mớiA10/A10G. Không dùng sự khác nhau với cache đó để kết luận giới hạn token làm mất fact. Không có timing1024 cùng lượt cho các ca dài nên không khẳng định hệ số tăng tốc.

Đối chứng cùng model/GPU: 18/19 caption natural ở128 token khớp hoàn toàn lượt1024 ngay trước đó. Các ca khác được lưu trong `CAP_AUDIT.json` để xem phần bị cắt.

Giới hạn token là tùy chọn vận hành, không sửa nhận diện xoay/zoom hoặc câu bịa. Giữ mặc định1024 cho tái lập; nếu chọn cap nhỏ cho demo cần chấp nhận khả năng thiếu mô tả.
