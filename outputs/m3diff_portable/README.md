# Chuyển M3Diff đã fine-tune sang máy khác

**Không cần train lại.** Gói này lưu adapter LoRA đã train; cần model M3Diff gốc đúng revision và môi trường GPU để inference. Không cần tài khoản Modal để dùng gói này trên máy GPU khác.

Adapter là bản nghiên cứu `mixed_objective`: giảm bịa thay đổi vật trong các bộ xoay/zoom đã kiểm tra, nhưng chưa giảm lỗi tổng hợp gồm ánh sáng/giải thích hình học. Độ dài caption không đo tính đúng đắn. Model gốc vẫn là bản mặc định. Xem `EVALUATION.md`, không gọi adapter này là bản luôn tốt hơn.

Có thể mở `m3diff-inference-portable.ipynb` trong kernel Python3.10, sửa hai ảnh rồi chạy từng cell. Notebook mặc định `USE_ADAPTER=False` dùng model gốc vì LoRA giảm điểm full test; đổi `True` để chạy bản đã fine-tune. Notebook chỉ inference, không có cell training. Ví dụ CLI bên dưới chủ động chọn adapter thử nghiệm.

## Có trong gói

- `model/m3diff-mixed-lora/`: weights adapter, cấu hình và state ngoài LoRA (rỗng vì phần nền đóng băng).
- `code/run_caption.py`: nạp base + LoRA FP32 riêng, giữ đúng generate của multimodal model.
- `code/baseline_eval.py`: runner inference/resume, không chứa đường dẫn Modal.
- `requirements-linux.txt`: phiên bản thư viện đã dùng; Python3.10, torch2.2.2.

Model gốc khoảng14GB được tải riêng. Lần đầu máy mới có thể cần tải thêm SigLIP vision tower từ Hugging Face; đó là tải weights, không phải train. Đã chạy trên A10 khoảng24GB và A100. Quy trình bên dưới dành cho Linux/WSL2 hoặc server GPU; không phải môi trường Windows CPU thuần.

## Cài một lần trên máy GPU mới

Mở terminal trong thư mục gói:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-linux.txt
git clone https://github.com/Yuan-Liu-01/M3Diff.git M3Diff-code
git -C M3Diff-code checkout 4e346e52185620ec6fa17235d93b0c26a9d47a71
python -m pip install --no-deps -e ./M3Diff-code
python download_base.py --output ./M3Diff-base
```

Cần driver/CUDA phù hợp với torch đã cài. Nếu đã có đúng model base revision bên dưới thì dùng đường dẫn đó, không phải tải lại.

## Chạy hai ảnh của bạn

```bash
python make_question.py --before /path/before.jpg --after /path/after.jpg
python code/run_caption.py \
  --model-path ./model/m3diff-mixed-lora \
  --model-base ./M3Diff-base \
  --question-file ./questions.json \
  --image-folder . \
  --answers-file ./captions.jsonl
```

Mặc định BF16, greedy,1024 token, không FlashAttention và LoRA FP32 không merge—giống chế độ đang đánh giá. Caption được lưu trong JSONL; chạy lại cùng câu hỏi/file sẽ tiếp tục phần còn thiếu. Để chạy bộ ảnh, tạo nhiều record cùng schema với ID khác nhau.

Runner kiểm tra hash adapter theo manifest đã xác minh trên GPU, và lưu hash ảnh/câu hỏi/model cạnh file kết quả. Nếu đổi ảnh nhưng giữ cùng ID, dùng file kết quả mới; runner sẽ chặn việc lấy nhầm caption cũ.

Thêm `--exact-identity-guard` nếu muốn trả lời “hai ảnh giống hệt” trực tiếp khi RGB sau giải mã trùng từng pixel. Trường hợp này không cần nạp model. Ảnh chỉ gần giống, xoay hoặc zoom vẫn đi qua model; không dùng căn chỉnh xấp xỉ để chặn thay đổi thật. Mặc định guard tắt để giữ phép đo model riêng.

Tùy chọn lọc câu lặp nguyên văn:

```bash
python code/clean_captions.py --input captions.jsonl --output captions_clean.jsonl
```

Lọc lặp không xác minh nội dung ảnh và không sửa câu bịa. Mặc định v2 xử lý thêm câu dính liền kiểu `.The`; dùng `--version v1` để khớp bộ lọc của các pilot/so sánh chính. V2 đã kiểm tra bảo toàn các claim khác nhau trên3860 caption; chỉ1 caption cached khácv1, không coi đây là tăng khả năng nhận diện hình ảnh.

Để chạy bản gốc đối chiếu, dùng `--model-path ./M3Diff-base`, bỏ `--model-base` và chọn file `--answers-file` khác. Trong notebook chọn `USE_ADAPTER=False`.

## Phiên bản cần giữ

- Base: `IVC-liuyuan/M3Diff`, revision `d6a8880dc789b0816660278c087ac9ebdfe18dd0`.
- Repo: commit `4e346e52185620ec6fa17235d93b0c26a9d47a71`.
- Adapter: LoRA r16/alpha32,64 update, LR2e-5; vision/projector/MDP đóng băng.
- `adapter_config.json` có thể còn ghi đường dẫn base trên Modal lúc train; lệnh trên truyền base ở máy mới bằng `--model-base`, nên không phụ thuộc đường dẫn đó.
- Giữ đủ các file adapter. Chỉ copy notebook mà thiếu weights thì không mang theo phần đã học.

Kết quả kiểm tra load và hash weights nằm trong manifest khi gói xuất xong. Chuyển máy không đòi hỏi train lại; chỉ train tiếp khi muốn sửa/cải thiện model.
