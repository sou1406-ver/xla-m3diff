# M³Diff + LocateAnything: bộ kiểm chứng caption tối thiểu

M³Diff vẫn sinh caption chính. LocateAnything tìm vùng vật; bộ kiểm chứng dùng căn chỉnh hình học và màu nội vùng để sửa một số mệnh đề nhầm “biến mất” thành “đổi màu”. Không yêu cầu viết lại toàn bộ caption và không sửa khi bằng chứng chưa rõ.

## Chạy trên tài khoản Modal hiện tại

Từ thư mục này, dùng Modal CLI đã cài:

```powershell
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach .\modal_app.py
```

Mặc định chạy 24 cặp mới (12 Real + 12 Render), loại các ảnh đã dùng để phát triển V4 và các ảnh demo ban đầu. Các cặp trong đợt mới cũng không dùng chung ảnh. Mẫu được chọn từ caption baseline có mệnh đề xuất hiện/biến mất, trước khi đọc nhãn tham chiếu.

Đây là kiểm tra một tập con tập trung vào loại lỗi, không phải toàn bộ benchmark. Không bảo đảm tách biệt hoàn toàn theo scene. Ngưỡng/thuật toán đã khóa; muốn thay đổi phải đặt tên run mới và ghi nhận đó là bước phát triển.

## Điều kiện dữ liệu

Pipeline này dùng Volume `m3diff` của thí nghiệm hiện tại, cần có:

- `baseline_reproduction_v1/`: prompt, caption M³Diff baseline, cấu hình và script chấm.
- `baseline_cache/OmniDiff/`: ảnh test gốc.
- `locateanything_cache/model/`: weights/model code LocateAnything đã tải.
- `grounded_caption_pilot_v1/selection.json` và `locateanything_demo_v1/results.json`: danh sách ảnh đã dùng để phát triển, phục vụ loại trùng.

Lần đánh giá này **tái sử dụng caption M³Diff đã sinh**, không gọi M³Diff lại để tạo kết quả khác. Không train thêm model. Đây là gói triển khai thử nghiệm trên cache hiện có, chưa phải dịch vụ nhận ảnh bất kỳ.

## Luồng tài nguyên và lưu kết quả

1. CPU chọn mẫu và căn chỉnh ảnh.
2. Chỉ gọi A10 nếu có mệnh đề nằm trong phạm vi cần định vị.
3. GPU xong thì trả về; CPU kiểm chứng, chấm điểm và đóng gói.
4. Các function tự kết thúc và có thời gian chờ hạ container ngắn. Không tạo endpoint, lịch chạy hay dịch vụ thường trực.

Kết quả ở `m3diff/caption_verifier_validation_v1/`, gồm `REPORT.md`, `metrics.json`, `summary_x100.csv`, `comparison.json`, `manual_review.csv`, ảnh minh họa các ca sửa và `validation_results.zip`.

```powershell
..\.modal-client\Scripts\python.exe -X utf8 -m modal volume get m3diff caption_verifier_validation_v1/validation_results.zip .\validation_results.zip --force
```

## Phạm vi và giới hạn

- Chỉ xử lý một số câu vật có màu sắc bị mô tả là biến mất; chưa xử lý đầy đủ tư thế, OCR, nhiều vật hay vật bị che.
- Bộ định vị và ghép hình học đều có thể sai. Thay vật cùng loại có thể bị nhầm với đổi màu.
- V4 được phát triển từ một số ca đã xem; không lấy điểm tập phát triển làm bằng chứng khái quát.
- Cần xem thủ công mọi caption bị sửa, báo cả sửa đúng lẫn sửa sai. Không tự động điền nhãn đánh giá của người.
- Source checksum, seed, ảnh bị loại, cấu hình baseline và toàn bộ quyết định được lưu trong từng run.
