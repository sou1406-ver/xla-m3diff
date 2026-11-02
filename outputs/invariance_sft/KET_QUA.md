# Pilot học đối chứng không-thay-đổi

**Candidate chưa đạt đủ điều kiện đã định; giữ checkpoint gốc làm bản chính. Không dò thêm cấu hình sau kết quả này.**

## Đã chạy

Một LoRA r16, LR 5e-6, 32 update; vision/projector/MDP đóng băng. Batch train gồm 64 mẫu không-thay-đổi từ 16 ảnh train và 192 mẫu có thay đổi. Đã kiểm tra 360 ảnh train gốc với 40 ảnh test gốc: không trùng hash RGB sau giải mã. Đây là loại trùng chính xác, không bảo đảm scene độc lập.

Checkpoint gốc và candidate chạy 108 cặp cùng prompt gốc/BF16/greedy trong cùng GPU container, không dùng bộ chặn căn chỉnh hoặc prompt camera-aware. Cả hai caption cùng lọc lặp trước khi xáo tên nhánh. Trợ lý ghi nhận xét rồi mới mở khóa tên; không phải chấm mù độc lập bởi con người.

## Bịa thay đổi vật trên cặp chỉ đổi hình học

| Nhóm | Cặp | Baseline | Candidate |
|---|---:|---:|---:|
| 8 scene mới: chỉ xoay/zoom | 32 | 31 | 28 |
| 8 scene mới: ảnh giống hệt | 8 | 7 | 7 |
| 12 scene diagnostic cũ: chỉ xoay/zoom | 36 | 29 | 29 |
| 12 scene diagnostic cũ: ảnh giống hệt | 12 | 8 | 8 |

Khẳng định ánh sáng thay đổi và sai khác giả trên ảnh giống hệt được ghi riêng; ít bịa thay vật không tự chứng minh đã hiểu camera. CSV có chi tiết và phần chưa chắc.

## Khả năng giữ thay đổi thật

| Nhóm | Miền | Tổng fact | Baseline nhận đúng | Candidate nhận đúng | Cặp có phát biểu không được hỗ trợ: gốc → mới |
|---|---|---:|---:|---:|---:|
| Scene mới | Real | 4 | 1 | 2 | 2 → 2 |
| Scene mới | Render | 8 | 4 | 3 | 4 → 4 |
| Diagnostic cũ | Real | 12 | 7 | 7 | 5 → 5 |
| Diagnostic cũ | Render | 10 | 2 | 2 | 5 → 6 |

Một cặp quần áo mới có lẫn thay khung hình/che khuất chưa được gán nhãn chắc nên không vào số fact chính. Đủ nhãn và ghi chú ở eval_rubric và masked_assessments; không dựa vào caption model tự chấm.

## Điều kiện đã kiểm tra

- new_scene_geometry_physical_fp_decreases: đạt
- old_Real_natural_fact_hits_do_not_drop: đạt
- old_Render_natural_fact_hits_do_not_drop: đạt
- new_Real_natural_fact_hits_do_not_drop: đạt
- new_Render_natural_fact_hits_do_not_drop: không đạt
- new_natural_unsupported_pairs_do_not_increase: đạt

Chỉ một seed/cấu hình. Những ảnh đánh giá đã được xem trong các lượt phát triển trước; cùng họ phép biến đổi với augmentation train, nên resampling shortcut là khả năng cần kiểm tra trên dữ liệu ngoài. Tập nhỏ nhiều cặp chung scene; chưa có bằng chứng cho góc nhìn 3D/parallax. Chưa chạy full-test benchmark cho candidate này, không suy CIDEr/BLEU toàn bộ từ diagnostic.

Trọng số ở Volume `m3diff/invariance_sft_v1/m3diff-invariance-lora`. Code, train recipe, hash dữ liệu, log, caption raw, chấm từng cặp và khóa giải đều được lưu. Các job phải được kiểm tra dừng ở modal_final_status trước khi giao kết quả.
