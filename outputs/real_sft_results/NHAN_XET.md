# Kết quả thử cải thiện M3Diff bằng SFT

Đã hoàn tất hai lượt SFT và đánh giá 64 cặp test cố định. Mỗi lượt học 256 cặp ảnh thật/caption gốc, một epoch. Không dùng LocateAnything hoặc ảnh tổng hợp mới. Đã xác nhận mọi app của lần thử đều dừng, tasks = 0.

| Nhánh | CIDEr Real | CIDEr Render |
|---|---:|---:|
| M3Diff baseline | 58,18 | 37,83 |
| Checkpoint fine-tune cũ | 56,04 | 37,63 |
| SFT chọn ngẫu nhiên | **61,70** | **53,54** |
| SFT ưu tiên mẫu có train-CIDEr thấp | 43,25 | 40,27 |

Điểm nhân 100, mỗi miền gồm 32 cặp. Chỉ so các nhánh trong cùng lần thử; không so CIDEr trực tiếp với điểm full test trước đây vì document frequency khác nhau.

SFT ngẫu nhiên có tín hiệu tốt hơn, đặc biệt trên Render. Tuy nhiên, CI 95% của mức tăng CIDEr so baseline là [-26,26; +28,55] cho Real và [-8,55; +44,11] cho Render; đều chứa 0. Chưa đủ bằng chứng kết luận cải thiện ổn định. Đây không phải kết quả đã xác nhận trên toàn benchmark hay trên bộ xoay/zoom riêng.

Chọn mẫu khó chỉ bằng CIDEr thấp chưa hiệu quả: điểm Real giảm và cả hai miền thấp hơn nhánh ngẫu nhiên. Không nên mở rộng cách chọn mẫu này ngay. CIDEr thấp có thể phản ánh khác biệt cách diễn đạt hoặc nhãn phức tạp, không tự chứng minh model nhận diện sai.

Checkpoint cũ chưa thể hiện lợi thế rõ trong tập nhỏ này. Vì cấu hình và dữ liệu train khác nhau, không dùng kết quả này để kết luận riêng dữ liệu tổng hợp là nguyên nhân.

Lỗi lặp vẫn tồn tại: trên Render, baseline và cả hai nhánh SFT mới đều có 2/32 caption lặp một câu từ ba lần trở lên; checkpoint cũ có 1/32. Chưa giải quyết được lỗi này bằng SFT nhỏ.

Hướng đáng kiểm tra tiếp là giữ nhánh SFT dữ liệu thật, đánh giá rộng hơn trước khi tăng quy mô train. Nếu làm hard-example SFT tiếp, cần xem ảnh và xác minh lỗi ngữ nghĩa, sửa caption mục tiêu khi có căn cứ; không chỉ chọn theo điểm CIDEr. Lần thử hiện tại dùng annotation gốc, chưa tạo bộ nhãn sửa lỗi do con người xác minh.

- [Báo cáo chi tiết](REPORT.md): toàn bộ metric và khoảng bất định.
- [Caption từng cặp](comparison.json): baseline, checkpoint cũ, hai nhánh mới và reference.
- [Cấu hình](prepared.json), [điểm từng cặp](per_pair_cider.json), [bảng điểm](summary_x100.csv).

Trọng số giữ trên Volume `m3diff/real_sft_pilot_v1/m3diff-random_sft-lora` và `m3diff-hard_sft-lora`. Hai adapter mới đều bắt đầu từ checkpoint công bố; không ghi đè checkpoint cũ. Script chạy và giải thích cách tái lập nằm ở thư mục outputs của workspace.
