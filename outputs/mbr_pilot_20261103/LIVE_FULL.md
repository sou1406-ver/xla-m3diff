# Full MBR đã dừng,không hoàn thành

**Trạng thái cuối:** `STOP_ERROR_NO_RETRY`,550Real/0Render;app stopped09:04:17GMT+7,03/11/2026. [Báo cáo cuối](full1570/CLOSED_REPORT.md). Không có full metrics;không resume. Billing riêng app4,70657624USD.

Nội dung bên dưới là snapshot khởi chạy trước khi preemption,không phải trạng thái hiện tại.

# MBR full1570 đang chạy

User đã chọn **Chạy full, trần18đô**. Khóa admission trước prediction tại commit `c303d9b`; không train hoặc sửa cấu hình theo test.

[Theo dõi app Modal](https://modal.com/apps/sou1406-ver/main/ap-6kENLEhpd83ypqw6H1aAC8). Snapshot `2026-11-03T00:32:01.627622+00:00`: 7/1570 cặp đã lưu; NVIDIA A10080GB PCIe, batch2. Đây là snapshot lúc khởi chạy, không phải tiến độ hiện tại sau nhiều giờ.

- Sinh mới greedy +8sample cho803Real+767Render trong cùng GPU/session; giữ selector train-only IDF và hyperparameter val200.
- Trần18USD; reservation upper17,70USD gồm GPU17,45,CPUscore0,09,CPUcoordinator0,12,misc0,04. Đây không phải hóa đơn.
- GPU hard19200giây,soft18900; CPUscore hard900; coordinator hard21060. Không retry/resume tự động.
- CPU coordinator bền vững gọi GPU rồi CPUscorer; đóng browser/client vẫn chạy. GPU scaledown2giây khi inference kết thúc, không giữ trong lúc chấm.
- Nếu hết thời gian/lỗi: lưu partial/error và dừng; partial không phải full benchmark. Không tự đổi model mặc định.

Kết quả trên Volume `m3diff`, thư mục `mbr_pilot_20261103/full1570/`:

- `PROGRESS.json`: tiến độ đang chạy.
- `FULL_DONE.json`: đủ1570haypartial.
- `METRICS.json`, `PER_PAIR.json`, `SELECTION.json`: kết quả CPU sau inference đủ.
- `PIPELINE_DONE.json`: COMPLETE_SCORED hoặc STOP_PARTIAL_NO_RETRY hoặc STOP_ERROR_NO_RETRY.
- `results1570.jsonl`:9ứng viên mỗi cặp; không dùng oracle test chọn câu.

Đọc `FULL_PROTOCOL.json` và `ADMISSION.json` cho hash/budget chính thức. `PROPOSED_PROTOCOL.json` là proposal cũ, giữ để audit; runner mới bổ sung durable CPU orchestration trước khi dispatch. `KET_QUA_VAL200.md` là kết quả pilot, không phải điểm full. Chưa có kết luận full.
