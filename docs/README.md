# Tài liệu dự án

[← Trang chủ](../README.md)

| Tài liệu | Dùng khi |
|---|---|
| [OVERVIEW](OVERVIEW.md) | Hiểu câu hỏi, phương pháp và thiết kế đánh giá |
| [RESULTS](RESULTS.md) | Xem kết quả có nguồn và giới hạn |
| [EXPERIMENTS](EXPERIMENTS.md) | Tìm code và artifact theo nhóm |
| [RUNNING](RUNNING.md) | Chuẩn bị môi trường, weights và Volume |
| [HANDOFF](HANDOFF.md) | Tiếp nhận trạng thái cuối |
| [STRUCTURE](STRUCTURE.md) | Tra ánh xạ sau sắp xếp |
| [CONFIG_AUDIT_20261102](CONFIG_AUDIT_20261102.md) | Đối chiếu config/checkpoint |
| [BASELINE_SOURCE_AUDIT_20261102](BASELINE_SOURCE_AUDIT_20261102.md) | Kiểm tra hai baseline và nhánh SCST |

## Lịch sử và integrity

- [Bàn giao nguyên bản](HANDOFF_HISTORY.md), [mục lục nguyên bản](EXPERIMENTS_HISTORY.md): có snapshot đã lỗi thời.
- [Manifest export cũ](GIT_EXPORT_MANIFEST.json), [QA export cũ](EXPORT_QA.json): bằng chứng tại thời điểm export, không phải inventory mới.
- [Ánh xạ sắp xếp](REORGANIZATION.json): đường dẫn cũ/mới và hash file di chuyển.
