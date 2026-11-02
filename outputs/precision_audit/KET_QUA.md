# LoRA FP32 riêng so với merge BF16

Cùng checkpoint invariance_sft_v1, không train thêm: so sánh merge vào base BF16 với giữ LoRA riêng bằng FP32. Hai chế độ chạy cùng108 cặp, cùng prompt/greedy trong cùng GPU container. Đã xác nhận392 tensor adapter được nạp, tất cả LoRA-B khác0, và chế độ FP32 khôi phục đúng từng giá trị đã lưu.

## Phép đo số học

Lấy mẫu21 ma trận ở tầng0,14,27: chỉ5,539% phần tử trọng số nền thay đổi sau merge BF16; sai sốL2 trung bình của cập nhật so với phép cộngFP32 là0,951. Đây là bằng chứng làm tròn cập nhật nhỏ, không phải tỷ lệ mất accuracy hay tỷ lệ caption sai.

## Caption thực tế

| Nhóm | Số cặp | Merge BF16: bịa thay vật | Giữ FP32 riêng: bịa thay vật |
|---|---:|---:|---:|
| 8 scene mới, xoay/zoom | 32 | 28 | 30 |
| 12 scene cũ, xoay/zoom | 36 | 29 | 30 |

| Nhóm/miền | Tổng fact tự nhiên | Merge BF16 | Giữ FP32 riêng |
|---|---:|---:|---:|
| new/Real | 4 | 2 | 2 |
| new/Render | 8 | 3 | 3 |
| old/Real | 12 | 7 | 6 |
| old/Render | 10 | 2 | 2 |

Có 51/108 cặp có caption hiển thị giống hệt giữa hai chế độ. 172/216 nhãn được tái dùng vì ID/câu hỏi và toàn bộ caption trùng khớp; 44 câu mới đã được trợ lý chấm trước khi giải khóa tên chế độ. Đây là procedural masking, không phải người chấm mù độc lập.

Chế độ không merge chưa đạt điều kiện tăng chất lượng caption đã định. Mất mát số học là có thật nhưng không đủ giải thích/sửa điểm yếu model trong pilot nhỏ này.

Các ảnh này đã được dùng trong quá trình phát triển; chỉ một checkpoint, một họ augmentation2D, ít scene và đánh giá trợ lý. Không suy ra độ bền góc nhìn3D. Điều kiện, từng nhãn, raw caption và dtype audit đều được lưu. Không thay ngưỡng/nhãn sau khi mở khóa.

`load_wrapper.py` giữ phương thức generate của multimodal LM và các LoRA Linear đang hoạt động; không sửa mã repo và không gộp trọng số. Có thể dùng để kiểm tra các lượt train tiếp theo mà không làm tròn delta vào trọng số nền trước inference.
