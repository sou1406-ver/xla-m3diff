# SFT trên caption được rà ảnh

44 cặp train được trợ lý rà trực quan (22 Real, 22 Render), từ 48 ứng viên. Chưa có người gán nhãn độc lập xác nhận.
Hai nhánh học cùng ảnh và thứ tự: 44 cặp x 2 lượt xuất hiện + 128 cặp replay = 216 bản ghi, một epoch, 27 optimizer update. Chỉ caption mục tiêu khác nhau.
Đã kiểm tra hash LoRA và MDP trước train trùng nhau ở cả ba nhánh; thứ tự 216 chỉ số mẫu thực tế cũng trùng nhau. Seed42 đặt trước khi tạo model; tắt group_by_modality_length. Xem control_verification.json và initialization_audit.json/sample_order.json của từng model.
Nhánh corrected_lora_only dùng đúng nhãn sửa/thứ tự/số bước, nhưng đóng băng MDP thay vì cập nhật MDP. Đã kiểm tra non_lora_trainables.bin rỗng để xác nhận không cập nhật trọng số ngoài LoRA.
Nhãn sửa đồng thời thay đổi độ chi tiết và cách diễn đạt; đây không phải phép đo tách riêng độ chính xác ngữ nghĩa khỏi độ dài caption.
Đánh giá trên 256 cặp chưa dùng ở các pilot chọn mẫu trước đó (128 mỗi miền). Baseline chính chạy lại trên họ GPU A100/BF16; mọi nhánh cùng yêu cầu A100-40GB, nhưng Modal cấp A100-SXM4-80GB cho lượt baseline. Đây là đối chiếu cùng họ A100, chưa kiểm chứng trùng SKU vật lý tuyệt đối. cached_A10_baseline giữ caption baseline cũ. Cả 128 cặp Real dùng ảnh chưa xem ở các pilot chọn mẫu; Render chỉ có 9 cặp như vậy. Các cặp còn lại có thể dùng ảnh đã xem trước, nhưng không đưa ảnh test vào train.
Đây là nghiên cứu một seed, chưa bảo đảm tách scene. Nhánh previous_random có dữ liệu/số bước khác nên chỉ là đối chiếu thực dụng.
Các nhánh _dedup chỉ loại câu lặp nguyên văn sau sinh, không cập nhật model. Điểm nhân 100; CIDEr cùng document frequency trong từng miền.

| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Lặp câu >=3 |
|---|---|---:|---:|---:|---:|---:|
| Real | baseline | 11.33 | 19.23 | 32.64 | 35.49 | 1 |
| Real | cached_A10_baseline | 12.20 | 19.78 | 32.28 | 33.27 | 0 |
| Real | previous_random | 11.17 | 19.48 | 32.87 | 41.33 | 1 |
| Real | original_labels | 11.23 | 19.49 | 32.65 | 41.36 | 1 |
| Real | corrected_labels | 13.10 | 19.51 | 32.58 | 39.36 | 0 |
| Real | corrected_lora_only | 12.91 | 19.75 | 32.98 | 38.79 | 0 |
| Real | baseline_dedup | 12.79 | 19.57 | 32.77 | 35.49 | 0 |
| Real | cached_A10_baseline_dedup | 12.23 | 19.78 | 32.30 | 33.28 | 0 |
| Real | previous_random_dedup | 12.60 | 19.82 | 33.00 | 41.33 | 0 |
| Real | original_labels_dedup | 12.66 | 19.82 | 32.82 | 41.36 | 0 |
| Real | corrected_labels_dedup | 13.09 | 19.50 | 32.58 | 39.37 | 0 |
| Real | corrected_lora_only_dedup | 12.96 | 19.76 | 32.98 | 38.79 | 0 |
| Render | baseline | 15.38 | 19.85 | 35.10 | 32.90 | 3 |
| Render | cached_A10_baseline | 17.25 | 20.23 | 34.59 | 34.74 | 2 |
| Render | previous_random | 16.69 | 19.92 | 35.04 | 29.60 | 2 |
| Render | original_labels | 15.31 | 19.70 | 34.89 | 31.60 | 3 |
| Render | corrected_labels | 13.87 | 19.14 | 34.30 | 29.19 | 4 |
| Render | corrected_lora_only | 15.09 | 19.50 | 34.94 | 30.13 | 3 |
| Render | baseline_dedup | 19.30 | 20.84 | 35.68 | 34.05 | 0 |
| Render | cached_A10_baseline_dedup | 19.27 | 20.88 | 34.98 | 35.06 | 0 |
| Render | previous_random_dedup | 19.27 | 20.58 | 35.38 | 30.27 | 0 |
| Render | original_labels_dedup | 19.05 | 20.65 | 35.45 | 32.27 | 0 |
| Render | corrected_labels_dedup | 19.17 | 20.38 | 35.07 | 30.06 | 0 |
| Render | corrected_lora_only_dedup | 19.15 | 20.49 | 35.50 | 31.31 | 0 |

## Bất định theo cụm ảnh chung

Bootstrap 10.000 lần theo thành phần liên thông ảnh chung; mỗi lần lấy lại các cụm rồi tính chênh lệch trung bình theo cặp. Cụm ảnh chung chưa nhất thiết bao trùm toàn bộ scene; không tính biến thiên giữa seed train.

Real: 128 cặp, 18 cụm.
- corrected_labels minus baseline: +3.87; CI95% [-1.64, +12.71].
- original_labels minus baseline: +5.87; CI95% [-2.35, +19.36].
- corrected_labels minus original_labels: -2.00; CI95% [-8.63, +2.40].
- previous_random minus baseline: +5.84; CI95% [+0.23, +12.32].
- baseline_dedup minus baseline: +0.00; CI95% [+0.00, +0.00].
- corrected_labels_dedup minus corrected_labels: +0.01; CI95% [+0.00, +0.03].
- previous_random_dedup minus baseline_dedup: +5.84; CI95% [+0.23, +12.32].
- corrected_labels_dedup minus baseline_dedup: +3.88; CI95% [-1.64, +12.75].
- corrected_lora_only minus baseline: +3.30; CI95% [-1.58, +8.85].
- corrected_lora_only minus corrected_labels: -0.57; CI95% [-8.60, +5.14].
- corrected_lora_only_dedup minus baseline_dedup: +3.30; CI95% [-1.58, +8.85].
- baseline minus cached_A10_baseline: +2.23; CI95% [-1.26, +5.26].

Render: 128 cặp, 13 cụm.
- corrected_labels minus baseline: -3.71; CI95% [-11.46, +5.00].
- original_labels minus baseline: -1.31; CI95% [-7.32, +3.92].
- corrected_labels minus original_labels: -2.41; CI95% [-10.02, +5.63].
- previous_random minus baseline: -3.30; CI95% [-12.45, +4.21].
- baseline_dedup minus baseline: +1.15; CI95% [+0.00, +2.88].
- corrected_labels_dedup minus corrected_labels: +0.87; CI95% [+0.00, +2.84].
- previous_random_dedup minus baseline_dedup: -3.78; CI95% [-12.71, +3.16].
- corrected_labels_dedup minus baseline_dedup: -3.99; CI95% [-11.66, +4.62].
- corrected_lora_only minus baseline: -2.77; CI95% [-13.22, +5.99].
- corrected_lora_only minus corrected_labels: +0.94; CI95% [-6.02, +7.04].
- corrected_lora_only_dedup minus baseline_dedup: -2.74; CI95% [-13.11, +5.72].
- baseline minus cached_A10_baseline: -1.84; CI95% [-7.17, +3.13].

## Tệp kiểm tra

annotations.json và review_manifest.json ghi nhãn gốc, caption baseline, nhãn sửa và bằng chứng cho 48 cặp train.
final_comparison.json dùng baseline A100 khớp phần cứng; comparison.json từ bước GPU ban đầu còn giữ baseline A10 cũ. Dùng final_comparison.json khi đọc báo cáo cuối.
blind_audit.json và blind_audit_images.zip: 16 cặp test dùng ảnh mới, baseline và cả hai nhánh SFT nhãn sửa đều đã qua cùng bộ lọc lặp rồi được xáo thứ tự. Đánh giá nói sai và bỏ sót riêng; blind_key.json là khóa giải sau khi chấm trực quan.
image_clean_metrics.json chấm lại từng nhánh trên nhóm ảnh mới. Không so CIDEr giữa tập con này và toàn bộ 128 cặp vì document frequency khác nhau.
Trọng số lưu trên Volume m3diff/curated_sft_v4/m3diff-original_labels-lora, m3diff-corrected_labels-lora và m3diff-corrected_lora_only-lora. GPU được giải phóng khi mỗi function experiment trả về.
