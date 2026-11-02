# Pilot SFT trên ảnh thật

64 cặp test cố định: 32 Real, 32 Render. Điểm dưới đây nhân 100; CIDEr dùng document frequency của từng tập con 32 cặp.
Không so trực tiếp CIDEr ở đây với lần full test hoặc tập con khác. Không dùng test để chọn mẫu train.

| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Cặp lặp câu ≥3 lần |
|---|---|---:|---:|---:|---:|---:|
| Real | baseline | 18.77 | 22.50 | 35.84 | 58.18 | 0 |
| Real | old_ft | 18.80 | 21.28 | 33.52 | 56.04 | 0 |
| Real | random_sft | 19.20 | 23.13 | 35.56 | 61.70 | 0 |
| Real | hard_sft | 18.54 | 21.52 | 34.85 | 43.25 | 0 |
| Render | baseline | 7.05 | 16.80 | 32.84 | 37.83 | 2 |
| Render | old_ft | 8.96 | 16.88 | 32.49 | 37.63 | 1 |
| Render | random_sft | 9.68 | 17.14 | 33.76 | 53.54 | 2 |
| Render | hard_sft | 9.56 | 17.37 | 33.17 | 40.27 | 2 |

## Chênh lệch CIDEr và bất định

Bootstrap ghép cặp 10.000 lần trên điểm CIDEr từng cặp, giữ nguyên document frequency của tập con. Khoảng này không tính phụ thuộc giữa các cặp chung scene hay biến thiên giữa các seed train.
- Real, old_ft minus baseline: -2.14, CI 95% [-44.16, +36.98].
- Real, random_sft minus baseline: +3.52, CI 95% [-26.26, +28.55].
- Real, hard_sft minus baseline: -14.93, CI 95% [-47.22, +9.18].
- Real, hard_sft minus random_sft: -18.45, CI 95% [-43.73, +0.24].
- Render, old_ft minus baseline: -0.19, CI 95% [-19.97, +22.44].
- Render, random_sft minus baseline: +15.71, CI 95% [-8.55, +44.11].
- Render, hard_sft minus baseline: +2.44, CI 95% [-13.07, +19.98].
- Render, hard_sft minus random_sft: -13.27, CI 95% [-31.90, +2.56].

## Phạm vi

Hai nhánh mới học 256 cặp/nhánh, một epoch, LoRA r16/alpha32, MDP trainable, vision/projector frozen, LR 1e-5. Nhánh hard chọn 128 mẫu có train-CIDEr thấp; nhánh random chọn 128 ngẫu nhiên từ cùng nhóm ứng viên. Cùng 128 mẫu replay, cùng seed và số optimizer update. Các mẫu chính của hai nhánh có thể trùng một phần.
Checkpoint gốc đã học dữ liệu gốc; đây là continued SFT, không phải bộ nhãn mới. Train/ảnh test không trùng đường dẫn; chưa bảo đảm tách scene. Mẫu khó tự động chưa được con người xác minh đầy đủ. Một pilot nhỏ không chứng minh cải thiện khả năng chống xoay góc/zoom; cần bộ đánh giá riêng cho từng yếu tố đó.
Checkpoint fine-tune cũ khác cả dữ liệu, rank và tham số train nên chỉ là đối chiếu thực dụng, không dùng riêng chênh lệch đó để quy nguyên nhân cho dữ liệu tổng hợp.
Caption đầy đủ: comparison.json. Trọng số nằm trên Volume, các thư mục m3diff-random_sft-lora và m3diff-hard_sft-lora. Không tạo dịch vụ hoặc lịch GPU thường trực.
