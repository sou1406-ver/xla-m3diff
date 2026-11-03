# Full MBR bị gián đoạn: 550/1.570 cặp, không có điểm benchmark

**Trạng thái cuối: `STOP_ERROR_NO_RETRY`.** Lượt full không hoàn thành và đã đóng. Không chạy lại hoặc resume theo yêu cầu của người dùng. Không thay đổi model mặc định.

| Nội dung | Đã xác minh |
|---|---|
| Cặp đã lưu đầy đủ greedy +8 sample | **550** |
| Real | 550/803 |
| Render | **0/767** |
| Cặp tiếp theo chưa được lưu | `real_test_pair_000551` |
| Pipeline kết thúc | **09:04:14 ngày03/11/2026, GMT+7** |
| App stopped theo Modal CLI | **09:04:17 ngày03/11/2026, GMT+7** |
| Thời gian pipeline | 5.731,47 giây, khoảng95phút31giây |
| Thời gian GPU function, gồm setup | 5.711,37 giây, khoảng95phút11giây |
| Chi phí theo billing report riêng của app | **4,70657624 USD** |
| Trần đã được duyệt | 18 USD |
| App/container hiện hoạt động | **0/0** |

## Vì sao dừng?

[Log Modal có timestamp](FINAL_APP_LOGS.txt) ghi kernel chết (`DeadKernelError`) và container bị thu hồi (`Container terminated due to preemption`) lúc09:04:10. Modal khởi động lại function với cùng input trong container khác lúc09:04:14. Chốt `FULL_ATTEMPT.json` đã chặn lần khởi động này trước khi nạp model/sinh caption mới, nên pipeline trả về `STOP_ERROR_NO_RETRY`.

`retries=0` không ngăn được việc nền tảng restart input do preemption; lớp chốt attempt đã thực thi chính sách không tiếp tục inference. Không gọi đây là hết budget, timeout cứng hoặc một lỗi chất lượng của MBR. Log không đủ để kết luận chi tiết nguyên nhân hạ tầng dẫn tới preemption, hoặc khẳng định CUDA OOM.

Lượt dừng lúc09:04, sớm hơn timeout dự kiến khoảng12:50. Phần tiền dự phòng18USD không được tiêu hết.

## Dữ liệu và những kết quả không tồn tại

[Raw output](results1570.jsonl) có đúng550 dòng,550ID riêng biệt, khớp đúng550câu hỏi đầu của thứ tự đã khóa. Mỗi dòng có1greedy+8sampling không rỗng. Tên file `results1570.jsonl` là tên đích theo kế hoạch, **không có nghĩa file đủ1.570cặp**. Xem [audit máy đọc được](STOPPED_AUDIT.json) và SHA256 raw `9c2d55ad4d4cf6cb556255340c2cf2f7894d838d4eec7cf4f7d21089e4aa47fe`.

Các file sau **không có trên Volume**: `FULL_DONE.json`, `METRICS.json`, `PER_PAIR.json`, `SELECTION.json`. CPU scorer chỉ chạy khi inference đủ1.570, nên không được gọi. Không tạo file metric giả/placeholder, không chọn subset thuận lợi, không tính CIDEr hoặc bootstrap rồi trình bày thành benchmark full.

Vì chưa có Render nào, chưa có bằng chứng full để trả lời Render tăng hay giảm. Kết quả val200 vẫn là kết quả pilot đã ghi nhận trước đó (Real+20,91,Render+5,23); lượt gián đoạn này không xác nhận hoặc bác bỏ mức tăng ấy.

## Tiền và trạng thái tài nguyên

[Billing report](APP_BILLING_REPORT.json) truy vấn chính app `ap-6kENLEhpd83ypqw6H1aAC8`, theo các giờ UTC00/01/02 của03/11, ghi nhận4,70657624USD. Đây là mức sử dụng do nhà cung cấp ghi nhận theo app, có thể được đối soát lại; không phải lấy reservation17,70USD làm số tiền đã tiêu.

Snapshot workspace sau lượt chạy: credit đã sử dụng15,31USD; `billed_cost=0`. Với hạn mức30USD đã được xác nhận trước đó, phần credit còn lại tham chiếu khoảng14,69USD, trước các bộ đệm bảo thủ nội bộ. Hiệu số workspace so với snapshot trước full là khoảng4,71USD và phù hợp với report theo app.

Ledger giải phóng reservation17,70, thay bằng upper bảo thủ5,39USD dựa vào runtime đã kết thúc và allowance startup/misc; upper này **không phải chi phí thực tế**. Không có job mới được khởi chạy khi tải kết quả và kiểm tra billing.

[App list](FINAL_APPS.json) và [container list](FINAL_CONTAINERS.json) đều rỗng khi kiểm tra. CLI xác nhận app đã stopped09:04:17. [Kết quả pipeline nguyên bản](PIPELINE_DONE.json), [lỗi notebook](FULL_ERROR.txt), [thời gian GPU function](FULL_JOB_TIMING.json) được giữ nguyên. Executed notebook chỉ tải về máy để audit, không commit outputs hoặc ảnh/weights lên Git.

**Kết luận:** đây là lượt full bị gián đoạn do hạ tầng, đã dừng đúng chính sách không resume. Nhóm có pilot MBR dương, chưa có kết quả full MBR; chưa thể tuyên bố cải thiện full benchmark hoặc giữ điểm Render.
