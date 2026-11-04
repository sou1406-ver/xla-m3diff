# Bản đồ thí nghiệm

[← Trang chủ](../README.md) · [Kết quả](RESULTS.md) · [Kho artifact](../outputs/README.md)

## Chọn nhóm nghiên cứu

| Nhóm | Phạm vi |
|---|---|
| [Baseline và triển khai](../research/01-baseline/README.md) | Tái lập inference, kiểm tra nguồn và chuyển môi trường. |
| [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Caption SFT qua nhiều recipe; chưa có adapter đạt đủ bằng chứng thay base. |
| [Giải mã và chọn caption](../research/03-decoding/README.md) | Giữ weights; đánh giá consensus MBR và xử lý câu lặp. |
| [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Các phép thử kiểm tra nguồn lỗi; không đồng nghĩa giải pháp đã được xác nhận. |
| [Báo cáo và vận hành](../research/05-reports/README.md) | Báo cáo tổng hợp, tài liệu lịch sử và snapshot vận hành. |

## Các mốc chính

| Mốc | Bằng chứng | Kết luận |
|---|---|---|
| Baseline | [baseline_results](../outputs/baseline_results/) | Đã tái lập full1570 từ checkpoint công bố |
| Mixed full | [summary](../outputs/mixed_full_benchmark/results/summary_x100.json) | CIDEr giảm cả hai miền |
| Hai adapter 02/11 | [kết quả](../outputs/invariance_v2_20261102/KET_QUA.md) | Không đạt đủ retention gate |
| r64 / V2 cuối | [V2](../outputs/r64_v2_final_round/KET_QUA.md) | Tín hiệu camera chưa đủ, trượt synth |
| MBR full 03/11 | [full1570](../outputs/mbr_pilot_20261103/KET_QUA_FULL1570.md) | Hoàn thành sau resume; tăng Render, chưa tăng Real |
| MBR camera 04/11 | [partial](../outputs/mbr_pilot_20261103/camera240/KET_QUA.md) | Đóng ở 174/240; chưa đo retention |

## Cách kiểm tra một thí nghiệm

1. Đọc báo cáo kết quả, quyết định cuối và giới hạn.
2. Đọc protocol, gate và selection lock để biết điều kiện đã khóa.
3. Đối chiếu metric với raw caption/assessment và provenance.
4. Đọc runner cùng prerequisite trước khi chạy lại.

Không gộp pilot khác cohort/rubric. Không lấy 448 caption biến thể thành 448 scene độc lập. Trạng thái lỗi của phase1 MBR không thay thế trạng thái cuối COMPLETE_SCORED của full1570.

[Mục lục bàn giao nguyên bản](EXPERIMENTS_HISTORY.md) giữ nguyên để tra lịch sử; các từ “mới nhất” trong đó chỉ áp dụng tại thời điểm viết.
