# LocateAnything-3B — Thử xoay/zoom và ảnh không có vật

Đã hoàn tất 13 truy vấn trên Modal A10, BF16, SDPA, hybrid decoding. Mỗi ca đặt seed 42. Cấu hình và output đầy đủ nằm trong `run_config.json` và `results.json`.

## Quan sát

- Ảnh gốc, ảnh chụp nghiêng thật, hai phép xoay 2D, crop phóng to, thu ảnh còn 60% với viền xám và ảnh 384×384 đều trả khung quanh vùng hộp xanh khi kiểm tra bằng mắt. Trong ảnh có nhiều hộp xanh, nên một khung không chứng minh đã chọn nhất quán cùng một chiếc hộp.
- Prompt `Locate a single instance ...` trả box sai trên cả 3 ảnh không có hộp xanh được thử: chỉ sàn, phần cảnh phía dưới và cảnh đường phố.
- Trên cùng 2 ảnh âm là sàn và phần cảnh phía dưới, prompt `Locate all the instances ...` trả `<box>None</box>` thay vì box. Chưa thử prompt all trên cảnh đường phố trong lần này.

## Phạm vi kết luận

Đây là kiểm tra định tính nhỏ trên một cảnh chính và một cảnh đối chứng, không có ground truth bounding box và không tính IoU/mAP. Các phép xoay/scale ảnh 2D không tương đương thay đổi góc nhìn camera 3D; scale với viền xám không phải zoom-out vật lý.

Không dùng việc có/không có box từ prompt single làm bằng chứng vật xuất hiện/biến mất. Nếu tích hợp vào M3Diff, cần đánh giá prompt all trên nhiều cặp vật còn/vật mất, kiểm tra định vị và ghép đúng vật giữa hai ảnh trước khi kết luận cải thiện.

Xem `gallery.jpg` để so sánh toàn bộ ca; `summary.csv` để xem số box và thời gian. Đây không phải mô hình M3Diff đã cải tiến.
