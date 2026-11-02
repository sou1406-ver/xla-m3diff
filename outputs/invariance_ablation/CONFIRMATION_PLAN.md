# Kế hoạch xác nhận trên scene mới

Ghi trước khi có kết quả hai nhánh ablation. Nếu còn credit, kiểm tra cả hai adapter và baseline trên một bộ cố định mới; không chọn scene theo caption hoặc kết quả gate cũ.

- Lấy ngẫu nhiên bằng seed2026102802 tám cặp official test mỗi miền Real/Render. Loại mọi ảnh trùng RGB với360 ảnh train đã dùng,40 ảnh diagnostic cũ hoặc gallery32 ảnh đã xem; không dùng caption baseline để chọn. Ghi ID và hash trước inference.
- Mỗi cặp: ảnh A giống hệt; A→crop zoom1.10; A→roll8 an toàn; crop→A zoom out; A→B tự nhiên. Tổng80 cặp,240 caption cho ba model. Prompt và greedy1024 giữ nguyên; các adapter đều FP32 không merge.
- Xem16 cặp tự nhiên và khóa fact/rubric trước khi đọc caption mới. Chấm ẩn tên như lượt trước. Không dùng nhãn model tự sinh làm ground truth.
- Đây là kiểm tra scene mới trong cùng dataset, không phải benchmark ngoài miền; có thể vẫn trùng cảnh theo nghĩa ngữ nghĩa dù khác hash.
- Báo cả hai nhánh, không đổi ngưỡng/siêu tham số theo kết quả này. Kiểm tra48 biến thể xoay/zoom,16 identity và fact tự nhiên theo từng miền. Nếu có điều kiện pilot mới và bộ mới đạt, mới coi là hướng khả quan để đánh giá benchmark rộng hơn; chưa tuyên bố hoàn tất cải thiện chỉ từ pilot.
- Chi phí GPU giới hạn theo credit còn lại, tuần tự, lưu kết quả và trả GPU sau mỗi job. Không tăng credit hoặc đổi billing.
