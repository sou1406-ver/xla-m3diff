# Kết quả pilot M³Diff + LocateAnything

Đã hoàn tất 24 cặp tập trung vào vật thể: 12 Real và 12 Render. Có 72 lượt định vị và 48 caption viết lại. Không train thêm. Job Modal đã hoàn tất.

Ba nhánh chạy trên cùng ảnh và cùng đáp án tham chiếu:

1. Baseline: caption M³Diff đã sinh trong lần tái lập.
2. Control: M³Diff xem lại ảnh và caption nháp, không có định vị.
3. Grounded: giống control, thêm tên loại vật và box của LocateAnything trong hai ảnh.

## Bảng điểm (nhân 100)

| Tập / nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr |
|---|---:|---:|---:|---:|
| Real / baseline | 10.77 | 15.38 | 26.82 | 11.43 |
| Real / control | 10.55 | 14.88 | 26.28 | 11.70 |
| Real / grounded | 10.40 | 14.95 | 26.92 | 19.06 |
| Render / baseline | 15.98 | 19.89 | 33.85 | 16.42 |
| Render / control | 10.93 | 17.00 | 30.51 | 6.54 |
| Render / grounded | 10.96 | 16.76 | 31.92 | 7.47 |

Đây là điểm trên các tập con 12 cặp; CIDEr tính lại với document frequency của từng tập con. Không so trực tiếp với điểm toàn bộ benchmark. Không gộp hai số CIDEr thành một kết luận tổng quát.

## Kết luận hiện tại

V1 chưa cải thiện ổn định: CIDEr tăng trên Real, giảm trên Render; METEOR và BLEU-4 của grounded thấp hơn baseline trên cả hai tập con. Grounded nhỉnh hơn control về CIDEr ở cả hai tập, nhưng điều này chưa đủ để kết luận pipeline tốt hơn M³Diff gốc.

Grounded giữ nguyên từng ký tự caption baseline ở 8/24 cặp; control giữ nguyên ở 11/24. Đây là thống kê thay đổi văn bản, không phải số câu đúng/sai.

## Ví dụ đã kiểm tra ảnh và caption

- `render_test_pair_000549`: baseline nói thang xanh biến mất, trong khi thang vẫn còn và đổi màu. Grounded bỏ mệnh đề biến mất. Tuy nhiên vẫn bỏ sót thay đổi màu, nên mới chỉ loại một lỗi chứ chưa mô tả đầy đủ.
- `render_test_pair_000575`: baseline nói ghế đẩu bên phải biến mất, phù hợp ảnh/nhãn. Grounded đổi thành ghế xuất hiện, tạo thêm lỗi. Đưa box vào prompt không bảo đảm kiểm chứng đúng chiều thay đổi.
- `real_test_pair_000577`: baseline và grounded giống hệt nhau, vẫn diễn đạt lặp việc thay thế xe đồ chơi. Định vị không tự sửa được chất lượng diễn đạt.
- `real_test_pair_000567`: grounded bỏ mệnh đề cây đổi màu nhưng vẫn nói thêm đồ chơi xanh. Trong hai ảnh được kiểm tra không thấy bằng chứng cho đồ chơi đó; việc sửa một phần không bảo đảm caption hết bịa.

## Những giới hạn đã biết

- Trích tên vật bằng từ điển từ chính caption nháp: có thể bỏ sót vật thật hoặc chọn một vật ngữ cảnh như giường thay vì chiếc gối thay đổi.
- LocateAnything chưa được đánh giá đầy đủ trên OmniDiff. Không thấy box không chứng minh vật mất, và hai box cùng loại không chứng minh cùng một vật.
- V1 chưa có bộ ghép identity, chưa đưa crop/đặc trưng vùng vật vào M³Diff. Bổ sung bằng văn bản tên loại và tọa độ không tương đương bổ sung bằng chứng thị giác chi tiết.
- Nhánh control cũng giảm trên Render: prompt yêu cầu viết lại có thể góp phần làm giảm chất lượng. Đây là giả thuyết được gợi ý từ đối chứng, chưa tách được mọi nguyên nhân.
- Chưa gán nhãn tay đầy đủ 24 cặp; `manual_review.csv` để trống các cột phán xét chủ quan. Không báo tỷ lệ giảm hallucination khi chưa chấm.
- Tập nhỏ, chọn theo danh từ trong caption, có thể chung cảnh; chỉ dùng như tập phát triển thăm dò. Chưa chứng minh ý nghĩa thống kê hay khả năng khái quát.

## Hướng V2 nên thử

Giữ caption gốc mặc định, chỉ sửa mệnh đề khi có kiểm chứng thị giác rõ. Tách phát hiện thay đổi, ghép vật và kiểm tra thuộc tính; dùng crop có ngữ cảnh để kiểm tra mệnh đề thay vì chỉ thêm tọa độ. Cần tập validation riêng và sau đó tập đánh giá chưa dùng để chỉnh pipeline. Chưa nên chạy lại toàn bộ benchmark hoặc tuyên bố cải thiện từ V1 này.

File gốc: `comparison.json`, `metrics.json`, `grounding_cache.json`, `rewrite_questions.json`, `review_1.jpg` đến `review_6.jpg`, `manual_review.csv`. Gói ZIP từ Modal chứa log và đầy đủ output; file nhận xét này được bổ sung sau kiểm tra tại máy.
