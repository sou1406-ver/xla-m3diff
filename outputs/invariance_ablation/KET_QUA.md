# Đối chứng loss không đổi: hai nhánh LoRA

Cùng256 record, khởi tạo và hai thứ tự epoch đã đối chiếu. Mỗi nhánh64 update, LR2e-5; chỉ khác loss của64 mẫu không đổi là0 hay1. Base, vision, projector và MDP đóng băng. Hai adapter được nạp FP32 riêng; baseline gốc được chạy lại cùng GPU.

| Nhóm | Baseline | Chỉ loss positive | Thêm loss không đổi |
|---|---:|---:|---:|
| Bịa thay vật,32 cặp xoay/zoom | 31 | 27 | 21 |
| Đoán ánh sáng thay đổi,32 cặp | 7 | 12 | 15 |
| Có lỗi vật/ánh sáng/giải thích camera sai,32 cặp | 32 | 30 | 29 |
| Bịa khác biệt,20 cặp ảnh giống nhau | 19 | 16 | 12 |
| Fact đúng,12 fact mới | 5 | 5 | 5 |
| Fact đúng,22 fact cũ | 9 | 6 | 10 |
| Cặp tự nhiên có chi tiết sai,7 cặp | 6 | 6 | 3 |

Từng miền Real/Render và từng nhãn nằm trong metrics.json / decoded_assessments.json. Chỉ chọn thử rộng hơn nếu giảm bịa vật và không giảm fact ở bất kỳ miền/nhóm cũ-mới nào; không tăng số cặp tự nhiên có chi tiết sai.

Quyết định: mixed_objective đủ điều kiện pilot để kiểm tra rộng hơn.

Điều kiện pilot đạt không đồng nghĩa caption sạch: mixed vẫn có lỗi vật/ánh sáng/giải thích hình học ở29/32 cặp, so với32/32 baseline. Số đoán ánh sáng tăng7→15; một câu nói xoay90độ trong cặp chỉ zoom-out là sai. Câu sai này đã ghi rõ trước giải khóa, không được coi là hiểu camera đúng.

Đã tái dùng 80/216 nhãn khi ID, toàn bộ câu hỏi và caption trùng chính xác. Các câu mới được trợ lý chấm trước khi mở khóa; không phải người chấm độc lập. Ảnh đã được dùng trong quá trình phát triển, augmentation2D không chứng minh góc nhìn3D.
