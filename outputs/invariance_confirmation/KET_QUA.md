# Xác nhận trên16 cặp ảnh khác

Baseline và hai LoRA chạy80 cặp/240 caption cùng A10, prompt gốc, greedy1024. Có48 biến thể xoay/zoom,16 identity và16 tự nhiên. Đã loại trùng RGB với ảnh train/diagnostic/gallery và khóa fact trước inference.

**11/16 cặp vẫn cùng background đã xem.** Chỉ5 background Real chưa có trong diagnostic; Render không có background lạ. Render00/04 và01/05 còn chia sẻ background trong bộ này. Không gọi đây là16 scene độc lập chưa thấy.

| Nhóm | Baseline | Chỉ loss positive | Thêm loss không đổi |
|---|---:|---:|---:|
| Bịa vật,48 cặp | 36 | 36 | 29 |
| Có lỗi vật/ánh sáng/giải thích hình học,48 cặp | 44 | 45 | 44 |
| Bịa khác biệt,16 identity | 16 | 12 | 6 |
| Fact đúng Real | 10 | 11 | 10 |
| Fact đúng Render | 9 | 9 | 10 |
| Cặp tự nhiên có chi tiết sai | 9 | 7 | 9 |
| Bịa vật ở5 background Real lạ,15 cặp | 11 | 8 | 5 |
| Fact đúng ở5 background Real lạ | 5 | 5 | 6 |

Kết quả gate cố định: {"positive_control": false, "mixed_objective": true}.

Nhãn do trợ lý chấm, không phải người chấm độc lập; từng caption và phần chưa chắc được giữ nguyên trước mở khóa. Một seed, augmentation2D, cùng dataset và scene lặp; cần benchmark rộng và/hoặc thêm seed để đánh giá độ ổn định. Không thay ngưỡng sau xem kết quả.
