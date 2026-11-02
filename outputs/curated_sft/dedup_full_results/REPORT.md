# Loại câu lặp trên toàn bộ OmniDiff test

Chỉ hậu xử lý caption baseline đã sinh: loại câu lặp nguyên văn. Không train hay gọi lại model, không dùng LocateAnything.
Quy tắc đã cố định trước khi xem điểm full test. Điểm nhân 100.

| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Caption thay đổi |
|---|---|---:|---:|---:|---:|---:|
| Real | baseline | 14.265 | 19.495 | 32.606 | 33.753 | 0 |
| Real | dedup | 14.861 | 19.593 | 32.653 | 33.754 | 3 |
| Render | baseline | 16.917 | 20.141 | 35.751 | 30.493 | 0 |
| Render | dedup | 19.479 | 20.646 | 36.046 | 30.647 | 12 |

Đây là cải thiện ở pipeline đầu ra nếu điểm tăng; không phải bằng chứng model hiểu ảnh tốt hơn. Caption bịa vật, nhầm xoay góc hay zoom vẫn có thể tồn tại.

contrast.json có bootstrap theo cặp, chưa xét phụ thuộc giữa các cặp chung ảnh/scene. audit.json ghi chính xác caption nào bị sửa.
