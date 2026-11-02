# M3Diff — kết quả vòng thử nghiệm ngày 02/11/2026

**Đã train xong hai checkpoint LoRA mới, đánh giá xong và tắt toàn bộ GPU. Chưa có checkpoint mới đủ điều kiện giữ lại làm model cải thiện.** Nhánh sửa dữ liệu không tốt hơn đối chứng. Đối chứng có tín hiệu nhỏ trên bộ không đổi, nhưng mất thông tin khi vừa có thay đổi thật vừa có biến đổi hình học. Vì vậy không chạy full 1570 cho hai ứng viên này và không tiêu tiếp chỉ để dùng hết credit.

## 1. Đã thực hiện

- Kiểm chứng lại model gốc và mixed adapter cũ trên 96 cặp đã khóa.
- Train 2 nhánh từ model gốc: đối chứng và dữ liệu sửa. Mỗi nhánh 512 record, 2 epoch, 128 cập nhật, batch 1/accum 8, LR 1 e-5, seed 42, LoRA r16/alpha32. Tổng 2048 lượt mẫu qua hai nhánh, không phải 2048 cặp độc lập.
- Chỉ LoRA được cập nhật; vision, MDP, projector và trọng số ngôn ngữ gốc đóng băng. Không có SCST hoặc LocateAnything trong vòng này.
- Xác nhận cùng khởi tạo LoRA/MDP, cùng thứ tự index ở hai epoch, loss hữu hạn, chỉ LoRA trainable, 392 tensor adapter được khôi phục chính xác ở FP32 khi suy luận.
- Model gốc/mixed cũ/đối chứng/sửa dữ liệu:4 × 96=384 caption. Kiểm tra bổ sung 4 × 16=64 caption. Tổng 448 caption mới; không phải 448 scene độc lập.

## 2. Nhánh sửa khác gì?

Đối chứng lặp lại 192 record replay/positive và 64 record nuisance cũ để đủ 512 record. Nhánh sửa giữ 192 replay gốc, thêm 192 bản augmentation:96 biến đổi cả hai ảnh, 96 chỉ biến đổi ảnh sau và thêm mô tả chính xác về display rotation/scale. Toàn bộ trường ảnh được giữ trên canvas trung tính.128 nuisance gồm 64 mẫu cũ với nhãn riêng theo điều kiện, 32 lượt lặp và 32 mẫu chỉ sáng/tối.

Đây là so sánh một gói sửa dữ liệu/nhãn, không cô lập từng thành phần. Nhãn cũ đã có mô tả framing/orientation; không được nói lần này mới bổ sung khái niệm đó. Replay có nhãn tác giả và các sửa nhãn do trợ lý thực hiện trước đây; không phải toàn bộ được người chấm độc lập xác nhận. Xem `PROVENANCE_NOTES.md`.

## 3. Bộ kiểm tra chính

16 cặp nguồn, 13 nhóm nền cảnh, mỗi nguồn gồm identity, zoom-in, zoom-out, roll, brightness và natural:96 cặp. Loại trùng decoded RGB với 958 hash trong các bộ train/chẩn đoán đã chọn. Không đồng nghĩa scene độc lập hoặc test chưa từng dùng: toàn official test đã được chạy trước đây. Rubric ảnh và 29 ý tối thiểu được khóa trước caption mới. Chấm do trợ lý, ẩn tên model; chưa có người chấm độc lập.

“Ca có khẳng định sai” đếm hợp của lỗi vật thể, nói sai ánh sáng và giải thích hình học sai. Không đồng nghĩa mọi ca còn lại đều mô tả đầy đủ: câu chung chung có thể tránh bịa nhưng bỏ sót điều kiện. Ý chính natural và nhận đúng nuisance được ghi riêng.

| Chỉ số — thấp hơn tốt hơn | Gốc | Mixed cũ | Đối chứng 128 | Dữ liệu sửa 128 |
|---|---:|---:|---:|---:|
| Có khẳng định sai /80 synthetic | 73 | 54 | 53 | 63 |
| Có khẳng định sai /48 xoay-zoom | 48 | 44 | 43 | 45 |
| Bịa thay đổi vật thể /48 xoay-zoom | 42 | 28 | 30 | 32 |
| Nói sai ánh sáng /48 xoay-zoom | 18 | 28 | 26 | 31 |
| Giải thích hình học sai /48 xoay-zoom | 4 | 3 | 5 | 11 |
| Khẳng định sai /16 ảnh giống hệt | 15 | 8 | 7 | 15 |
| Khẳng định sai /16 chỉ tăng sáng | 10 | 2 | 3 | 3 |

| Natural — ý chính cao hơn tốt hơn | Gốc | Mixed cũ | Đối chứng 128 | Dữ liệu sửa 128 |
|---|---:|---:|---:|---:|
| Ý chính Real /14 | 9 | 9 | 10 | 8 |
| Ý chính Render /15 | 10 | 11 | 11 | 8 |
| Tổng ý chính /29 | 19 | 20 | 21 | 16 |
| Cặp có khẳng định phụ sai /16 | 12 | 11 | 10 | 10 |

Đối chứng mới chỉ hơn mixed cũ 1 ca xoay/zoom theo đánh giá này; không đủ gọi là bước nhảy chất lượng. Nhánh sửa tăng lỗi giải thích hình học và ánh sáng, đồng thời mất ý chính natural. Nó có một số câu zoom đúng và nhận đúng tăng sáng nhiều hơn, nhưng dùng các mẫu giải thích ấy sai điều kiện: cả ảnh giống hệt cũng bị nói đã xoay 90 độ hoặc zoom. Đây là dấu hiệu đáng kiểm tra về học mẫu câu; chưa chứng minh được cơ chế bên trong.

## 4. Thay đổi thật kèm biến đổi hình học

Thêm 16 biến thể phụ thuộc của chính 16 cặp natural: ảnh sau xoay-10 độ có containment hoặc hiển thị ở 88% scale. Không cắt nội dung; dùng cùng 29 ý tối thiểu. Supplement được ghi sau khi xem kiểm tra gốc/mixed cũ, trước caption của hai model mới. Đây không phải một holdout mới.

| Chỉ số stress | Gốc | Mixed cũ | Đối chứng 128 | Dữ liệu sửa 128 |
|---|---:|---:|---:|---:|
| Ý chính Real /14 | 8 | 6 | 6 | 6 |
| Ý chính Render /15 | 11 | 10 | 10 | 7 |
| Tổng ý chính /29 | 19 | 16 | 16 | 13 |
| Cặp có khẳng định sai /16 | 11 | 9 | 10 | 13 |

Ngưỡng giữ lại: không giảm ý chính ở TỪNG miền và không tăng cặp có khẳng định sai so với model gốc. Đối chứng giảm Real 8→6 và Render 11→10; nhánh sửa giảm Real 8→6 và Render 11→7, còn tăng cặp sai. Vì vậy cả hai không đạt kiểm tra an toàn này. Các số nhỏ, nhiều chi tiết còn chưa chắc; kết luận phù hợp là chưa đủ cơ sở giữ checkpoint, không phải chứng minh mọi hướng chống nhiễu hình học đều vô ích.

## 5. Ví dụ có thể xem lại

- `v2_Real_00__identity` — nhánh sửa: “The image has been rotated 90 degrees clockwise.”
- `v2_Real_06__zoom_in` — nhánh sửa: “The second image is zoomed in.”
- `v2_Real_03__natural` — nhánh sửa: “The second image is zoomed in.”

Ví dụ đầu là ảnh giống hệt nhưng bị nói xoay 90 độ; ví dụ thứ hai nhận đúng crop zoom; ví dụ thứ ba chỉ nói zoom và bỏ sót sự kiện xe đạp tiền cảnh đã khóa trong rubric. Có thể tra từng câu, nhãn, phần chưa chắc và hash raw trong `case_scores.csv`.

Trong 96 caption chính, nhánh sửa có 2 caption từ 500 từ trở lên (dài nhất 900 từ), trong khi 3 model còn lại không có. Đây là cảnh báo về output dài/lặp trên mẫu này, không phải tỷ lệ lỗi toàn benchmark. Xem `caption_behavior.json`.

## 6. Quyết định và giới hạn

- Không đổi model mặc định; không chạy full 1570 cho ứng viên không đạt gate.
- Đối chứng qua gate chính nhưng không qua supplement giữ thông tin. Nhánh sửa không qua cả hai. Xem `decision.json` và quy tắc đã ghi trong `SELECTION_POLICY.md`.
- Chưa có CIDEr/BLEU full-test mới; không lấy điểm của các lượt trước gán cho hai checkpoint này.
- Một seed, ít nền cảnh lặp, biến đổi2D, nhãn/đánh giá có phần do trợ lý, prompt nuisance vẫn tập trung một kiểu trong khi replay có 10 kiểu. Cùng decoding nhưng hai nhóm main predictions dùng hai container A 10-family; không gọi tất cả là cùng một physical GPU. Supplement chạy cả 4 model trong một container.
- Đơn thuần tăng train với công thức dữ liệu sửa này chưa được kết quả ủng hộ. Nếu nghiên cứu tiếp, cần thiết kế lại tín hiệu học/đối chiếu đặc trưng và dữ liệu viewpoint thật, cùng kiểm tra giữ thay đổi thật; những phần đó CHƯA được triển khai ở vòng này.

## 7. Checkpoint và tài nguyên

Trọng số đã lưu trong Volume Modal `m3diff`:

- `/invariance_v2_20261102/m3diff-control-lora/`
- `/invariance_v2_20261102/m3diff-revised-lora/`

Đây là checkpoint LoRA suy luận thử nghiệm, không được chọn thay model gốc. Folder tương ứng ở máy hiện chỉ giữ metadata/log kiểm chứng; trọng số thực nằm trên Volume. Script `download.py` có thể lấy từng file qua SDK mà không mở GPU. Cần đúng base M3Diff và loader FP32 unmerged; chưa xuất một gói portable mới hoặc tuyên bố chạy được trong demo SCST của repo khác. Không lưu đầy đủ optimizer/RNG để exact-resume train.

Tất cả 6 app của vòng này đã stopped, 0 task (`FINAL_GPU_CHECK.json`). Billing snapshot `2026-11-02T10:38:30.676476+00:00` ghi nhận consumption upper khoảng $2.10, billed cost 0; số liệu có thể trễ, không phải endpoint số dư credit trực tiếp. Chưa dùng hết gói $30. Không mua credit, không đổi billing.

Một job CPU bổ sung bị lỗi import lúc startup đã được dừng và sửa; job train chính không bị ảnh hưởng. Không có GPU chạy chờ người chấm.

## 8. File kiểm chứng

`PLAN.md`, `SUPPLEMENT_PLAN.md`, `SELECTION_POLICY.md`, `SELECTION_LOCK.json`, `data_audit.json`, `REVIEW_APPROVED.json`, `MATCHED_TRAIN_DONE.json`, hai `TRAIN_DONE.json`, các raw JSONL, masked assessments/key, `ACK_DERIVATION_AUDIT.json`, `metrics_all_models.json`, `positive_stress/metrics.json`, `decision.json`, `case_scores.csv`, `caption_behavior.json`, `PROVENANCE_NOTES.md`, `FINAL_GPU_CHECK.json`.
