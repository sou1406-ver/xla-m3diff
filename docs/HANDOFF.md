# Bàn giao hiện tại — bằng chứng đến 04/11/2026

[← Trang chủ](../README.md) · [Kết quả](RESULTS.md) · [Thí nghiệm](EXPERIMENTS.md) · [Cách chạy](RUNNING.md)

## Trạng thái cuối

| Hạng mục | Trạng thái | Nguồn chính |
|---|---|---|
| Cấu hình mặc định | Base greedy | [Kết quả](RESULTS.md) |
| Fine-tune | Chưa có adapter đủ bằng chứng thay base | [V2 cuối](../outputs/r64_v2_final_round/KET_QUA.md) |
| MBR full1570 | COMPLETE_SCORED; Real −0,22, Render +3,62 CIDEr | [Báo cáo full](../outputs/mbr_pilot_20261103/KET_QUA_FULL1570.md) |
| MBR camera | Đóng partial174/240, không GPU retry | [Camera partial](../outputs/mbr_pilot_20261103/camera240/KET_QUA.md) |
| Báo cáo BTL | Hoàn tất; Git giữ text, manifest và script tái tạo | [Báo cáo](../outputs/bao_cao_btl_20261104/BAO_CAO_BTL_M3DIFF.md) |

Các report cuối ghi nhận app đã dừng. Đây là trạng thái được lưu trong repo, không phải xác minh trực tiếp GPU hoặc billing hiện tại. Lần sắp xếp tài liệu không chạy job mới.

## Trước khi làm tiếp

- Đọc RESULTS và protocol của nhánh được chọn; giữ base làm mặc định.
- Bảo toàn raw, assessment, selection policy và kết quả; thí nghiệm mới dùng folder mới.
- Không gán gain Render thành gain cả hai miền hoặc giải quyết camera.
- SCST ngoài repo chưa được kiểm chứng độc lập tại đây; feature-consistency là hướng chưa triển khai.
- Khôi phục weights, ảnh và quyền Volume theo RUNNING trước khi chạy. Chỉ thị chi phí trong lịch sử không phải ủy quyền mới.

## Tra lịch sử

[HANDOFF_HISTORY.md](HANDOFF_HISTORY.md) giữ nguyên nội dung bàn giao trước khi sắp xếp, gồm cả các dòng LIVE đã lỗi thời. Ưu tiên trạng thái cuối ở trang này và artifact kết quả, không dùng snapshot cũ để suy ra job đang chạy.

## Bố cục mới

Đọc [STRUCTURE.md](STRUCTURE.md) để biết notebook đã chuyển đâu. outputs/ và work/ giữ bố cục hiện hữu; research/ cung cấp điều hướng theo chủ đề. AGENTS.md vẫn áp dụng.
