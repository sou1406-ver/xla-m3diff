# Kết quả triển khai và kiểm tra

Đã đóng gói pipeline, chạy trên Modal và hoàn tất 24 cặp mới (12 Real + 12 Render). 48 ảnh trong đợt này không trùng nhau và không trùng ảnh tập phát triển/demo trước. Chưa bảo đảm tách biệt theo scene.

Thuật toán/ngưỡng V4 được khóa trước khi đọc nhãn và tính điểm của đợt mới. Hash source trong run_config.json khớp source đã đóng gói. M³Diff dùng caption baseline đã lưu; LocateAnything chạy 8 truy vấn cần thiết cho các mệnh đề nằm trong phạm vi hỗ trợ. Chấm điểm thực hiện sau mọi quyết định sửa.

**Kết quả: 0/24 caption được sửa; toàn bộ metric giữ nguyên baseline.**

| Tập con | BLEU-4 ×100 | METEOR ×100 | ROUGE-L ×100 | CIDEr ×100 |
|---|---:|---:|---:|---:|
| Real (12), cả hai nhánh | 5.54 | 14.83 | 27.37 | 7.95 |
| Render (12), cả hai nhánh | 19.79 | 21.75 | 38.90 | 48.90 |

Không so các số này với điểm tập con khác hoặc toàn bộ benchmark, đặc biệt CIDEr tính lại document frequency theo từng tập con.

## Kết luận

Bản triển khai chạy được và giữ được hành vi baseline khi bằng chứng chưa chắc. Tuy nhiên, độ bao phủ sửa lỗi quá thấp: ca sửa thang xanh thành đen trên tập phát triển chưa khái quát sang đợt ảnh mới này. Không được tuyên bố đã cải thiện caption tổng thể, giảm hallucination trên tập mới hay tăng điểm benchmark.

Không thay ngưỡng để ép có sửa sau khi thấy kết quả. Nếu phát triển tiếp, cần phiên bản mới và tập kiểm tra khác. Hướng cần nghiên cứu là kiểm chứng ngữ nghĩa từng mệnh đề hoặc học từ dữ liệu vùng-vật-thay-đổi, thay vì chỉ thêm nhiều quy tắc màu/hình học.

## Tài nguyên

App `ap-h0elIGkjq7A0j1pDCjAlYI` đã được kiểm tra trạng thái `stopped`, `tasks=0` sau khi hoàn tất. Không còn job CPU/GPU trong danh sách App đang hoạt động. Không tạo lịch chạy lại hay endpoint thường trực.

Các file ở `validation/` chứa cấu hình đã khóa, danh sách mẫu, caption trước/sau, định vị, quyết định kiểm chứng và metric. `manual_review.csv` không có ca sửa cần gán nhãn trong đợt này.
