# Hai baseline và gate development SCST — kiểm tra không GPU

## Hai lượt baseline

Đã đọc caption trực tiếp từ `results/OmniDiff_{Real,Render}/` trên Volume và so với `outputs/mixed_full_benchmark/results/*_baseline_raw.jsonl` của lượt dựng lại:

| Miền | Cặp / ID chung | Caption giống nguyên văn | Caption khác |
|---|---:|---:|---:|
| Real | 803 /803 | 347 | 456 |
| Render | 767 /767 | 767 | 0 |

Không thiếu/trùng ID trong hai tập caption. Trong Real, ID1–122 không khác caption; khác biệt đầu tiên là123. Đây là mẫu hình cần đối chiếu lịch sử resume, không tự chứng minh nguyên nhân.

File question và reference hiện còn trên Volume dưới `baseline_reproduction_v1/repo/data/evaluation/` khớp cả4 SHA256 đã ghi trong `outputs/baseline_results/run_config.json`. Reference Real trong fullbenchmark cũng giống dữ liệu JSON đó (chỉ khác serialization). Không tìm thấy bản source repo `/root/M3Diff` cũ trên Volume: notebook lịch sử clone vào filesystem container tạm. Vì vậy **chưa có bản annotation/question độc lập của lượt35.54 để chứng minh hai lượt dùng cùng hay khác file**.

Kết luận: chênh lệch Real có ít nhất456 caption khác; giả thuyết chỉ thay reference không đủ giải thích hiện tượng này. Chưa xác định khác biệt sinh câu đến từ source patch, config/model revision, precision, ảnh/preprocess hay resume. Render trùng caption hoàn toàn là bằng chứng tốt cho miền đó, không chứng minh mọi cấu hình Real giống nhau. Notebook cũ có resume bỏ qua ID đã tồn tại, nên cần kiểm chứng provenance trước khi dùng cache làm mốc matched.

Điểm35.53796249 là score file lịch sử đã đọc, chưa phải kết quả tái chấm caption cũ bằng scorer hiện tại. Giữ riêng baseline35.54 và33.75; không gọi một lượt là sai chỉ từ số điểm.

## SCST development: đã xác nhận từ notebook công khai

Notebook `ducmanh202005/xla/notebooks/M3Diff_LoRA_SCST_4_O.ipynb` chứa output **development_failed**, báo cáo HTML200cặp:

| All ×100 | G | A | B |
|---|---:|---:|---:|
| BLEU4 | 29.9999 | 32.0408 | 30.0360 |
| CIDEr | 147.9351 | 143.7987 | 155.8563 |
| Real CIDEr | 107.9426 | 105.4306 | 107.6818 |

Lý do ghi rõ: **CIDEr Real giảm so G**,107.9426→107.6818. Confirmation chưa sinh caption (G/A/B đều0). Không diễn giải BLEU gần nhau thành không tăng CIDEr: All CIDEr tăng nhưng không qua gate từng miền. Không gọi B đã qua development/confirmation dựa trên fulltest về sau. Đây là output công bố của repo ngoài, chưa được nhóm tái chạy.

Nguồn: https://github.com/ducmanh202005/xla/blob/main/notebooks/M3Diff_LoRA_SCST_4_O.ipynb (đã lưu snapshot để kiểm chứng). Không có job GPU nào được mở trong lần kiểm tra này.

## Phân công tiếp theo

Kiểm chứng G/A/B cùng decoding trên Colab của người giữ weights. Modal dành cho checkpoint r64 `/ft` chưa được đánh giá: trước tiên pilot camera-only hallucination + camera/object fact retention, đo throughput, rồi quyết định full. Không cần đưa adapter SCST khác loader sang Modal chỉ để đánh giá.
