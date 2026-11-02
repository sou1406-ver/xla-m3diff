# Thử cải thiện caption M3Diff

Kết luận cuối ở **`KET_QUA.md`**. Giữ checkpoint công bố + bộ lọc lặp; cả hai nhánh SFT nhãn sửa đều giảm CIDEr Render nên không được chọn. `decision.json` và `decoded_audit.json` lưu quyết định và chấm trực quan sau giải khóa. Gói giao kết quả ở `../m3diff_improvement_results.zip`, không gồm trọng số hoặc bộ ảnh lớn.

Có hai thay đổi được kiểm tra riêng:

1. Continued SFT trên caption được rà trực quan, đối chứng với caption gốc trên cùng ảnh.
2. Loại câu lặp nguyên văn sau sinh, không đổi nội dung các câu còn lại.

## Dữ liệu SFT

Đã xem 48 cặp train cùng caption baseline và annotation gốc. Giữ 44 cặp (22 Real, 22 Render); loại 4 cặp mơ hồ hoặc baseline đã mô tả hợp lý. Rà bởi trợ lý Codex, **chưa phải bộ nhãn được người gán nhãn độc lập xác nhận**.

`review_manifest.json` ghi ảnh, caption baseline và nhãn gốc. `annotations.json` ghi quyết định giữ/loại, nhãn sửa, loại lỗi và bằng chứng. `REVIEW.md` là bản đọc thuận tiện. Ảnh/crop gốc lưu ở `images/`; `review_images.zip` là bộ ảnh đã tải.

Hai nhánh mới dùng cùng 44 cặp, mỗi cặp xuất hiện hai lần, cộng cùng 128 cặp replay: **216 bản ghi / 172 cặp duy nhất**, một epoch, 27 optimizer update. Chỉ caption mục tiêu của 44 cặp khác nhau. Cùng thứ tự, seed42, LoRA r16/alpha32, LR 1e-5, batch1/accum8; vision và projector đóng băng, MDP trainable. Cả hai bắt đầu từ checkpoint M3Diff công bố.

Có thêm nhánh `corrected_lora_only`: đúng nhãn sửa/thứ tự/số bước như nhánh nhãn sửa, nhưng MDP cũng đóng băng. Kiểm tra sau train yêu cầu `non_lora_trainables.bin` không chứa tensor nào để xác nhận chỉ LoRA được cập nhật. Cấu hình này được quyết định trước khi đọc điểm đánh giá mới.

Caption gốc có trung vị 77,5 từ, nhãn sửa 42 từ. Cách sửa vừa thay đổi độ chính xác, vừa thay đổi độ chi tiết và cách diễn đạt; kết quả không tách riêng ba yếu tố này. Checkpoint gốc đã học từ dataset gốc; đây là continued SFT, không phải dữ liệu hoàn toàn mới.

## Đánh giá

256 cặp mới, 128 mỗi miền, loại ID và cặp ảnh không thứ tự đã dùng trong các pilot trước. Cả 128 cặp Real dùng ảnh chưa được xem ở các pilot; Render chỉ có 9 cặp như vậy, các cặp khác có thể dùng ảnh đã xem. Không đưa ảnh test vào train.

Các cặp có thể dùng chung ảnh. Báo cáo dùng bootstrap theo cụm ảnh chung, đồng thời ghi rõ chưa bảo đảm tách scene. Có thêm điểm cho nhóm ảnh mới và một lượt xem 16 cặp: baseline, SFT nhãn sửa/MDP trainable và SFT nhãn sửa/MDP frozen đều qua cùng bộ lọc lặp rồi được che tên nhánh. Lựa chọn và quy tắc phân tích cố định trước khi đọc điểm từng mẫu; `analysis_locked.json` lưu hash source.

Đối chiếu thêm checkpoint SFT ngẫu nhiên từ lần thử trước; nhánh đó khác số bước và dữ liệu, nên không dùng để suy nguyên nhân riêng việc sửa nhãn.

## Dùng bộ lọc lặp ngay

Chạy trong thư mục này với Python 3.10+:

```powershell
python postprocess_jsonl.py --input captions_raw.jsonl --output captions_clean.jsonl --audit dedup_audit.json
```

Mỗi dòng input là JSON có `id` hoặc `image_id` và chuỗi `caption`. Metadata/ID được giữ nguyên. Input và output phải khác tệp. Bộ lọc không paraphrase, không sửa tên vật hoặc tự kết luận vật biến mất; chỉ loại câu trùng nguyên văn sau chuẩn hóa khoảng trắng và phần đuôi lặp bị cắt trong một vòng lặp rõ ràng. Có kiểm tra riêng dấu nháy, số thập phân, vị trí trái/phải và phần câu chưa hoàn tất.

Đã đánh giá trên toàn bộ 803 Real + 767 Render từ baseline lưu sẵn: 15 caption thay đổi; BLEU-4 Real 14,265 → 14,861, Render 16,917 → 19,479. CIDEr tăng rất nhẹ. Đây là sửa pipeline đầu ra, **không phải bằng chứng tăng năng lực hiểu ảnh hoặc khắc phục xoay/zoom**. Chi tiết ở `dedup_full_results/`.

## Chạy lại trên Modal hiện tại

Từ thư mục này:

```powershell
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_curated_sft_modal.py
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_curated_sft_modal.py --lora-only
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_matched_baseline.py
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach report_curated_sft.py
```

Chỉ chạy lệnh report sau khi có `SUCCESS.json`, `LORA_ONLY_SUCCESS.json` và `MATCHED_BASELINE_SUCCESS.json`. Các script dùng Volume `m3diff` và cache của workspace này: `baseline_reproduction_v1`, `baseline_cache`, `real_sft_pilot_v1`, `ft/code/ft_train.py`, cùng danh sách các pilot trước để loại trùng. Đây không phải bộ tải mọi dependency/dataset từ tài khoản trống.

Kết quả train/eval nằm ở `m3diff/curated_sft_v4`; báo cáo full-test lọc lặp ở `m3diff/dedup_full_baseline_v1`. GPU function có timeout hữu hạn và tự giải phóng khi trả về. Không tạo endpoint hoặc lịch chạy thường trực. Mỗi lần đổi nhãn/cấu hình cần đổi run name, không trộn kết quả cũ.

Đối chứng cuối dùng seed42 trước khi tạo model và tắt xếp mẫu theo độ dài. Hash trọng số LoRA/MDP khởi tạo và thứ tự lấy mẫu thực tế phải trùng nhau ở cả ba nhánh trước khi chấm điểm; control_verification.json ghi kết quả kiểm tra. Các lượt v1–v3 không đạt mức kiểm soát/thiết kế này không dùng làm kết luận nhân quả.

Baseline chính yêu cầu A100-40GB/BF16 như SFT, nhưng Modal thực tế cấp A100-SXM4-80GB cho baseline. Đối chiếu cùng họ GPU A100, chưa xác nhận cùng SKU vật lý cho mọi nhánh SFT. Caption baseline A10 cũ được giữ với tên cached_A10_baseline; báo cáo toàn test của bộ lọc lặp vẫn dùng đúng cặp caption A10 trước/sau nên không trộn ảnh hưởng phần cứng. Dùng final_comparison.json cho đối chiếu cuối.
