# Viewpoint extension và pipeline chỉ gợi ý

Đọc `KET_QUA.md` cho kết luận. V1 có phản ví dụ với thay đổi appearance nhỏ, nên **không dùng approximate registration để tự ghi caption “không đổi”**. `safe_pipeline.py` chỉ tự thay khi RGB sau giải mã giống hệt; còn căn chỉnh gần đúng chỉ gắn cờ review.

Mặc định cần NumPy và Pillow. Cờ `--registration-advice` cần thêm `opencv-python-headless==4.10.0.84`; môi trường đối chiếu là `numpy<2`, `Pillow==11.1.0`.

```powershell
python safe_pipeline.py --manifest pairs.json --image-root images --input captions.jsonl --output captions_safe.jsonl --audit flags.json
```

Manifest là mảng JSON, mỗi bản ghi có `id` và `image: [before_path, after_path]`, đường dẫn tương đối so với image-root. Input JSONL có `id`, `caption`, metadata tùy chọn. Các file input/output/audit/manifest phải khác nhau. Script không sửa ảnh và giữ caption model cho mọi cặp không giống hệt pixel. Gợi ý căn chỉnh vẫn cần đọc phần ảnh không chồng lấp và sai khác nhỏ, không phải chứng minh hai scene giống nhau.

`registration_gate_frozen.py` và `registration_protocol_frozen.json` là v1 giữ nguyên để tái lập, không phải chính sách ghi đè hiện tại. `selection_locked.json` khóa 8 scene trước khi đo feature. `composed_locked.json` khóa stress vừa xoay/zoom vừa sửa mảng trước khi đọc outcome extension. `natural_review.json` ghi 7 nhãn chắc và 1 chưa chắc, được viết từ ảnh trước khi đọc outcome. Người rà là trợ lý Codex, chưa có đánh giá độc lập của con người.

`results/audit.json` chứa 104 trường hợp; `composed_results/composed_audit.json` chứa 24 trường hợp bổ sung. `case_results.csv` có kết quả từng cặp. `safe_check/` là kiểm tra CLI thực tế, không phải caption model mới; các caption sentinel chỉ dùng kiểm tra giữ nguyên dữ liệu. `failure_previews/` và `natural_review/natural_boards/` là preview JPEG, không thay thế PNG inference trong Volume.

Chạy lại CPU trong workspace hiện tại bằng `run_cpu.py --stage gallery|prepare|audit|composed` qua Modal. Các script dùng Volume `m3diff`, repo/model/dataset cache đã có, không cài từ tài khoản trắng. Không chạy lại selection/đổi ngưỡng sau khi xem outcome; nếu làm nghiên cứu mới hãy đổi tên run. `check_safe_cpu.py` kiểm tra đầu-cuối 5 phản ví dụ bằng CPU. `report.py` tổng hợp từ feature đã lưu, không sinh nhãn hay tìm ngưỡng.

Không có model weights hoặc PNG dataset lớn trong gói. Dữ liệu gốc và dẫn xuất vẫn nằm ở `m3diff/viewpoint_extension_v1/dataset`. Thử nghiệm này chỉ đo bộ chặn, không cung cấp CIDEr/BLEU hoặc kết quả suy luận M3Diff mới trên ảnh extension.
