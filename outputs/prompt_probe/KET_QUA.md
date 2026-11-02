# Probe10 cách hỏi ×4 cặp ảnh cố định

Baseline, mixed cũ và balanced chạy cùng A10, tổng120 caption. Khóa tên model chỉ mở sau khi lưu toàn bộ nhãn. Đây là4 source case phát triển lặp10 cách hỏi; không phải40 scene độc lập.

| Chỉ số /40 câu | Baseline | Mixed cũ | Balanced |
|---|---:|---:|---:|
| Bịa thay vật | 40 | 22 | 20 |
| Vật/ánh sáng/độ rõ, nhãn rộng | 40 | 39 | 40 |
| Loại câu độ rõ mơ hồ khỏi lỗi chắc | 40 | 29 | 30 |
| Chỉ nói more visible, chưa rõ cơ chế | 0 | 10 | 10 |

Cụm “more visible” có thể nói về khung hình rộng hơn, không chắc là bịa ánh sáng. Giữ nguyên nhãn visibility từ rubric trước và báo thêm phân tích độ nhạy, không đổi nhãn sau giải khóa. Không coi câu mơ hồ này là đã hiểu đúng camera.

Nguy cơ shortcut câu hỏi có trong phân phối train, nhưng probe nhỏ này chưa chứng minh model chỉ cải thiện ở câu đã dùng cho negative. Bản balanced không được chọn vì đã giảm fact cũ Real; không dùng probe để đảo điều kiện bảo toàn fact.

Từng source/cách hỏi và caption nằm trong metrics.json/decoded_assessments.json. Trợ lý chấm, chưa được người chấm độc lập xác nhận.
