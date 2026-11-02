# Đối chứng cân bằng10 cách hỏi

Giữ nguyên256 ảnh/target/order và64 update LR2e-5, chỉ đổi phân phối câu hỏi của64 negative. Đã khớp khởi tạo LoRA/MDP và cả hai thứ tự epoch. Không khẳng định dropout mask giống nhau vì độ dài câu hỏi thay đổi.

| Nhóm | Baseline | Balanced |
|---|---:|---:|
| Bịa thay vật,32 cặp | 31 | 20 |
| Lỗi vật/ánh sáng/camera,32 cặp | 32 | 29 |
| Fact cũ Real | 7 | 6 |
| Fact cũ Render | 2 | 3 |
| Fact mới Real | 1 | 1 |
| Fact mới Render | 4 | 4 |

Gate factual đã định: chưa đạt.

Phát hiện mất cân bằng template đến từ code/data trước khi đọc caption confirmation80. Chưa chứng minh model đã học shortcut; probe10 template kiểm tra riêng. Không thay nhãn sau khi mở khóa.127/144 nhãn trùng chính xác được tái dùng,17 câu mới đã chấm trước giải khóa. Trợ lý chấm, không phải người chấm độc lập.
