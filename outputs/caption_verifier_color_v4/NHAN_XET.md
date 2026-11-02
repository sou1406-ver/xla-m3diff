# Kết quả sửa tối thiểu caption

Đã hoàn tất thử nghiệm trên cùng 24 cặp phát triển của pilot trước. Tất cả App CPU/GPU được kiểm tra qua Modal CLI đều stopped, tasks=0 sau khi chấm xong.

## Thay đổi cuối cùng

M³Diff vẫn sinh caption chính. Bộ kiểm chứng chỉ xét một số mệnh đề xuất hiện/biến mất có tên vật và màu rõ. LocateAnything tìm vùng vật trong cả hai ảnh; SIFT/homography kiểm tra vị trí tương ứng; màu được kiểm tra từ pixel phía trong vùng vật sau căn chỉnh và hiệu chỉnh lệch sáng toàn cảnh. Không viết lại toàn bộ caption.

Ở `render_test_pair_000549`, pipeline tự sửa:

- Cũ: `The blue ladder on the right side of the lower bed has disappeared.`
- Mới: `The ladder has changed from blue to black.`

Hai ảnh và nhãn tham chiếu xác nhận đây là một sửa lỗi đúng. LocateAnything tìm một thang ở mỗi ảnh; box sau căn chỉnh đạt IoU 0.862. Có 535 pixel nội vùng được phân loại xanh ở ảnh trước, và tất cả chuyển sang lớp màu đen ở ảnh sau theo bộ phân loại màu thô. Đáp án tham chiếu không được dùng để tạo câu sửa.

23 caption còn lại giữ nguyên. Các trường hợp nhiều vật, định vị không chắc, hoặc căn chỉnh kém đều không sửa. Đây là độ bao phủ thấp có chủ đích, không phải bộ kiểm chứng tổng quát.

## Điểm trên tập con (×100)

| Tập | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr |
|---|---|---:|---:|---:|---:|
| Real (12) | Gốc | 10.77 | 15.38 | 26.82 | 11.43 |
| Real (12) | Sửa tối thiểu | 10.77 | 15.38 | 26.82 | 11.43 |
| Render (12) | Gốc | 15.98 | 19.89 | 33.85 | 16.42 |
| Render (12) | Sửa tối thiểu | 15.56 | 19.77 | 33.57 | 20.87 |

CIDEr Render tăng, còn BLEU-4/METEOR/ROUGE-L giảm nhẹ. Không được nói mọi metric đều tăng hoặc mô hình đã cải thiện toàn diện.

## Những cách đã thử nhưng chưa dùng làm kết quả cải thiện

- Viết lại cả đoạn với tọa độ: làm giảm điểm Render và có câu sửa sai.
- Chỉ dựa vào độ giống pixel hoặc đường nét: quá chặt, không sửa được câu nào.
- Hỏi LocateAnything nhiều màu trên crop: ảnh thang sau nhận đồng thời nhiều nhãn màu; hệ thống từ chối sửa thay vì chọn một nhãn tùy ý.

## Giới hạn

V4 được phát triển qua các ca lỗi trên chính 24 cặp này, trong đó đã xem ca chiếc thang. Vì vậy đây chỉ là proof of concept trên tập phát triển, không phải bằng chứng held-out hay cải thiện benchmark. Phân loại màu thô có thể bị ảnh hưởng bởi ánh sáng, che khuất, nền và thay vật cùng loại. Chưa xử lý đầy đủ tư thế, OCR, danh từ bị bỏ sót hoặc matching nhiều vật.

Bước đánh giá tiếp theo cần khóa thuật toán/ngưỡng rồi chạy trên ảnh chưa dùng để phát triển, kiểm tra thủ công mọi câu bị sửa và báo cả số sửa đúng/sửa sai. Chưa chạy bước đó để giữ giới hạn chi phí hiện tại.

File: `comparison.json` chứa caption trước/sau và bằng chứng; `metrics.json`/`summary_x100.csv` chứa điểm; `edit_1_render_test_pair_000549.jpg` minh họa ca sửa. Mã kiểm chứng ở `outputs/caption_verifier.py`, script chạy CPU ở `outputs/run_caption_verifier_v21.py --mode color` và cần cache thử nghiệm đã lưu trên Volume.
