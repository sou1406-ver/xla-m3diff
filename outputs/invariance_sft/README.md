# Pilot LoRA có đối chứng không-thay-đổi

`protocol.json` khóa một cấu hình trước output: 256 bản ghi, 64 negative từ 16 ảnh official train (8/domain), 192 positive (128 replay + 44 caption đã rà + 20 lặp), seed42, LoRA r16/alpha32, LR 5e-6, một epoch/32 update. Vision, projector và MDP đóng băng. Không train từ đầu. Caption đã rà là trợ lý Codex xác nhận, chưa có người gán nhãn độc lập.

`data_audit.json` xác nhận 360 ảnh gốc train và 40 ảnh gốc test không trùng hash RGB sau giải mã. Đây là loại trùng chính xác, không chứng minh scene train/test độc lập. Checkpoint công bố đã học official train. Negative chỉ dùng ảnh `/train/`, không dùng 104/24 stress hoặc ảnh test để fit.

108 cặp đánh giá: 60 cặp diagnostic cũ và 48 cặp mới (40 geometry + 8 natural). Baseline và candidate chạy cùng prompt gốc, BF16/greedy, cùng một GPU container. Không dùng bộ chặn căn chỉnh hoặc prompt camera-aware để tính kết quả model này. Hai nhánh cùng lọc câu lặp rồi ẩn tên theo cặp. `eval_rubric.json` khóa 22 fact tự nhiên cũ và 12 fact mới; 1 cặp quần áo mới chưa chắc được tách riêng.

Trước đó đã xem các ảnh test và đo nhiều cách, nên đây là nghiên cứu phát triển thích ứng, không phải external test/preregistered evaluation. Phép biến đổi train/eval cùng họ 2D, có thể có shortcut do resampling. Chỉ một seed và một cấu hình; không dò tiếp cấu hình theo kết quả pilot này. Các tiêu chí giữ model nằm trong protocol, đặc biệt kiểm tra khả năng tìm thay đổi thật để tránh học thành luôn nói không đổi.

Chạy lại trong workspace hiện tại:

```powershell
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_modal.py --stage prepare
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_modal.py --stage experiment
```

Chỉ chạy GPU sau khi data_audit qua kiểm tra. Script dùng Volume `m3diff` với repo/model/cache và dữ liệu replay của workspace hiện tại; không phải bộ cài mới từ tài khoản trắng. Không thay protocol/dataset khi tái dùng tên run. Model nằm ở `m3diff/invariance_sft_v1/m3diff-invariance-lora`; job GPU giới hạn 3.600 giây, tự giải phóng khi trả về, không có endpoint thường trực.

`train_seeded.py` gốc tại `../curated_sft/` đặt seed trước tạo LoRA, lưu hash khởi tạo, danh sách trainable và thứ tự lấy mẫu. GPU stage yêu cầu chỉ LoRA trainable, `non_lora_trainables.bin` rỗng, trainer_state có đủ 32 update và loss hữu hạn. Các log và dự đoán lưu đầy đủ; metadata thực tế GPU và phiên bản môi trường được ghi khi chạy.
