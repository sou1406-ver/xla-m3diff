# Script hỗ trợ và dữ liệu trung gian lịch sử

[← Trang chủ](../README.md) · [Cách chạy](../docs/RUNNING.md)

| Nhóm file | Vai trò |
|---|---|
| build_baseline_notebook.py / check_baseline_notebook.py | Dựng và kiểm tra notebook baseline trong outputs/ |
| build_r64_*.py / prepare_val200_local.py | Chuẩn bị các lượt đánh giá lịch sử |
| blind_detail_crops.py / review_detail_crops.py | Hỗ trợ kiểm tra chi tiết ảnh |
| prepare_git_handoff.py | Script export lịch sử; đã cập nhật nguồn notebook sang notebooks/ |
| train.py / builder.py / pyproject.toml | Source hỗ trợ được lưu trong quá trình thực nghiệm |
| JSON / JSONL | Dữ liệu chuẩn bị, audit và caption trung gian; giữ nguyên |

Đây không phải package ứng dụng hoặc quy trình Run All. Một số file chứa đường dẫn máy cũ hoặc side effect; đọc source trước khi chạy. Không di chuyển dữ liệu ở đây chỉ để phân nhóm vì có thể làm mất liên kết với script lịch sử.
