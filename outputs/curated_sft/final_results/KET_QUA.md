# Kết quả cải thiện M3Diff

**Bản nên dùng hiện tại: checkpoint M3Diff công bố + bộ lọc câu lặp nguyên văn. Các checkpoint SFT được giữ để nghiên cứu, chưa chọn thay baseline.**

## Đã làm

- Rà trực quan 48 cặp train, giữ 44 cặp (22 mỗi miền), sửa caption theo bằng chứng trong ảnh. Người rà là trợ lý Codex, chưa có gán nhãn độc lập bởi con người.
- Train ba đối chứng: nhãn gốc + LoRA/MDP; nhãn sửa + LoRA/MDP; nhãn sửa + chỉ LoRA. Mỗi nhánh 216 bản ghi, 172 cặp duy nhất, 27 update. Đã xác nhận hash khởi tạo và thứ tự mẫu thực tế trùng nhau.
- Đánh giá 256 cặp (128 mỗi miền), chạy lại baseline trên GPU họ A100 và chấm BLEU/METEOR/ROUGE/CIDEr. Modal cấp baseline A100-SXM4-80GB dù yêu cầu 40GB; chưa xác nhận cùng SKU vật lý cho mọi nhánh.
- Xem ảnh trước caption và chấm ẩn tên model trên 16 cặp; lưu nhận xét rồi mới giải khóa. Đây là đánh giá của trợ lý, không phải nghiên cứu chấm mù độc lập bởi con người.

## SFT trên cùng 256 cặp

Điểm nhân 100. Đây là điểm trên tập con, không so CIDEr trực tiếp với điểm toàn test ở bảng sau.

| Nhánh | Real CIDEr | Render CIDEr | Real BLEU-4 | Render BLEU-4 |
|---|---:|---:|---:|---:|
| Checkpoint gốc, chạy lại A100 | 35.49 | 32.90 | 11.33 | 15.38 |
| SFT nhãn gốc | 41.36 | 31.60 | 11.23 | 15.31 |
| SFT nhãn sửa + MDP | 39.36 | 29.19 | 13.10 | 13.87 |
| SFT nhãn sửa, MDP đóng băng | 38.79 | 30.13 | 12.91 | 15.09 |
| SFT ngẫu nhiên pilot trước | 41.33 | 29.60 | 11.17 | 16.69 |

Nhãn sửa + MDP tăng CIDEr Real +3,87 nhưng giảm Render −3,71; chỉ LoRA tăng Real +3,30 và giảm Render −2,77. Nhánh nhãn sửa + MDP còn thấp hơn nhãn gốc trên cả hai miền. Chưa chứng minh sửa nhãn theo cách này giúp model tốt hơn; chưa thể quy kết nguyên nhân từ một seed và bộ train nhỏ. Bootstrap theo cụm ảnh chung cho nhánh nhãn sửa + MDP ở Real có CI95% chứa 0 (−1,64 đến +12,71).

Chấm trực quan cùng bộ lọc lặp trước khi so:
- Nhãn sửa + MDP: 2 thắng / 3 thua / 11 hòa so với baseline trên 16 cặp.
- Nhãn sửa, MDP đóng băng: 3 thắng / 2 thua / 11 hòa so với baseline trên 16 cặp.

Nhiều trường hợp cả ba caption cùng sai: thay tư thế bị mô tả thành nằm xuống, vật vẫn còn bị nói biến mất, màn hình xoay bị nhầm thành thay bàn phím/ghế. Thắng tương đối không đồng nghĩa caption đã đúng. Cả hai nhánh đều không đạt điều kiện tăng CIDEr ở cả hai miền, nên không chạy tiếp full-test SFT hoặc dò thêm cấu hình.

## Cải thiện giữ lại: loại câu lặp

Đã chấm lại toàn bộ **803 Real + 767 Render**, dùng đúng caption gốc và sau xử lý trên cùng nguồn dự đoán baseline đã lưu. Không cần GPU cho bước lọc.

| Miền | BLEU-4 trước → sau | CIDEr trước → sau |
|---|---:|---:|
| Real | 14.265 → 14.861 | 33.753 → 33.754 |
| Render | 16.917 → 19.479 | 30.493 → 30.647 |

15/1.570 caption được xử lý lặp, 1.555 giữ nguyên. Bộ lọc chỉ xóa phần lặp, không thêm mô tả mới. BLEU tăng chủ yếu nhờ cắt vòng lặp dài; CIDEr tăng rất ít. Đây là cải thiện chất lượng đầu ra, **chưa phải cải thiện khả năng hiểu xoay góc hoặc zoom**.

## Dùng ngay

```powershell
python postprocess_jsonl.py --input captions_raw.jsonl --output captions_clean.jsonl --audit dedup_audit.json
```

`README.md` hướng dẫn chạy lại; `dedup_full_results/` có caption sau lọc và điểm đủ test; `final_results/` có caption, điểm, log và kiểm tra đối chứng SFT; `masked_assessments.json` và `decoded_audit.json` ghi chấm ẩn tên và giải khóa. `decision.json` ghi điều kiện chọn model và quyết định.

## Giới hạn và hướng tiếp theo

Tập đánh giá được dùng cho nhiều phép thử nên không còn là test độc lập cho lựa chọn model. 128 cặp Real dùng ảnh mới so với pilot; Render chỉ 9 cặp ảnh mới, các cặp còn lại chia sẻ ảnh đã xem. Có cụm ảnh chung; bootstrap theo cụm vẫn chưa bảo đảm bao hết scene. Một seed, ít dữ liệu sửa, độ dài/cách viết nhãn cũng thay đổi cùng độ chính xác.

Hướng nghiên cứu tiếp hợp lý là lập validation tách scene và tập kiểm tra riêng cho thay góc/zoom nhưng không thay vật; mở rộng nhãn sửa bằng người rà độc lập rồi thử huấn luyện nhất quán theo góc nhìn với đối chứng. Chưa có kết quả để khẳng định hướng đó sẽ tăng điểm.

Tất cả app thử nghiệm đã ở trạng thái stopped, 0 task khi kiểm tra cuối. Trọng số và dữ liệu vẫn lưu trên Modal Volume m3diff/curated_sft_v4; không có endpoint GPU thường trực.
