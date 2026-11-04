# Kết quả và giới hạn diễn giải

[← Trang chủ](../README.md) · [Tổng quan](OVERVIEW.md) · [Thí nghiệm](EXPERIMENTS.md)

## 1. Quy tắc đọc số liệu

CIDEr trong các bảng dưới được báo cáo ×100. Chỉ so trong cùng cohort, preprocessing và protocol. Baseline khác giữa các vòng không được tráo cho nhau. Không so trực tiếp điểm val với test khác cohort.

## 2. MBR full test

| Miền | N | Greedy CIDEr | MBR CIDEr | Δ | CI 95% |
|---|---:|---:|---:|---:|---|
| Real | 803 | 34,5844 | 34,3619 | −0,2225 | [−3,5640; +3,3177] |
| Render | 767 | 30,1822 | 33,7996 | +3,6174 | [+1,0924; +5,9766] |

Nguồn: [báo cáo full](../outputs/mbr_pilot_20261103/KET_QUA_FULL1570.md), [METRICS](../outputs/mbr_pilot_20261103/resume1020_v1/combined_full1570/METRICS.json), [CI](../outputs/mbr_pilot_20261103/resume1020_v1/combined_full1570/CONFIDENCE_INTERVALS.json).

Đủ 1.570 cặp, ghép từ 3 phiên; giữ nguyên 550 raw đầu. CI bootstrap 5.000 lượt theo nhóm ảnh liên thông, DF reference cố định. Có bằng chứng tăng Render CIDEr. CI Real chứa 0: chưa chứng minh cải thiện hoặc tương đương. Test từng được dùng trong các vòng trước, không gọi là test hoàn toàn chưa được xem.

## 3. Fine-tuning

| Vòng | Đánh giá | Kết quả / quyết định | Bằng chứng |
|---|---|---|---|
| Mixed LoRA cũ | Full 1.570 | CIDEr Real 33,7526 → 32,1295; Render 30,4928 → 19,9975; không chọn | [Summary](../outputs/mixed_full_benchmark/results/summary_x100.json) |
| Control / revised 02/11 | 448 caption, nhiều biến thể chung source | Stress facts: base 19/29, control 16/29, revised 13/29; không full | [Kết quả](../outputs/invariance_v2_20261102/KET_QUA.md) |
| r64 | Camera 240, synth 600, matched val 200 | Synth camera 33/600; color 69 → 61/90; val CIDEr giảm hai miền | [Synth](../outputs/r64_synth_eval_20261102/KET_QUA.md), [val](../outputs/r64_val_precheck_20261102/KET_QUA.md) |
| V2 cuối | Train 450 bước; camera 240 và synth 600 | Qua camera gate, trượt synth; không val/full/v3 | [Kết quả](../outputs/r64_v2_final_round/KET_QUA.md) |

Không dùng điểm full Mixed cũ đại diện r64, control/revised hoặc V2 cuối. Giảm training loss chưa chứng minh caption tốt hơn.

## 4. MBR camera — partial 174/240

| Proxy trên 174 cặp camera-only | Greedy | MBR |
|---|---:|---:|
| Cờ thay đổi vật thể | 127/174 | 121/174 |
| Nhắc camera | 0/174 | 0/174 |

Thiếu 6 pan và toàn bộ 60 camera + add/remove. Chưa đo được retention; không diễn giải 0/0 thành đạt gate. Prefix không ngẫu nhiên, regex chưa được xác nhận bằng nhãn người độc lập. Job bị cancellation, chưa xác định nguồn hủy; không gọi là timeout/preemption.

Nguồn: [camera partial](../outputs/mbr_pilot_20261103/camera240/KET_QUA.md).

## 5. Kết luận được hỗ trợ

- Giữ base greedy làm mặc định.
- MBR có kết quả dương trên Render và tốn thêm suy luận.
- Chưa có adapter đủ bằng chứng cải thiện tổng thể.
- Chưa chứng minh khắc phục lỗi camera, giảm hallucination tổng thể hoặc robustness 3D.

Kết luận phản ánh artifact đến 04/11/2026; lần sắp xếp này không chạy lại thí nghiệm.
