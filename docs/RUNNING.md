# Chạy code và khôi phục artifact ngoài Git

## Clone không có nghĩa sẵn sàng Run All

Repo gồm nguồn thí nghiệm và bằng chứng dạng text. Không có checkpoint base (~14GB), vision weights, adapter binary, ảnh OmniDiff, ảnh augmented, môi trường `.modal-client`, ZIP hay output notebook. Notebook root là lịch sử; baseline entrypoint được ưu tiên là `outputs/m3diff-baseline-full.ipynb` cạnh `outputs/run_baseline_modal.py`.

Không cần GPU để đọc caption/metric/decision. Chưa chạy GPU lại trong lần export. Script nghiên cứu có thể chứa đường dẫn Windows cũ hoặc `/mnt/m3diff`; chúng cần sửa theo môi trường hoặc khôi phục Volume, không phải mọi script đều portable.

## Inference trên máy GPU khác

Đọc [portable README](../outputs/m3diff_portable/README.md) và `requirements-linux.txt`. Đây là Linux/WSL2/CUDA, Python3.10; không phải CPU Windows Run All. Có `download_base.py`, `make_question.py`, `code/baseline_eval.py`, `code/run_caption.py`, notebook inference. Tải đúng base revision và SigLIP khi cần; **không phải train lại**.

Mặc định notebook `USE_ADAPTER=False`. Muốn dùng mixed adapter phải lấy đúng weights và kiểm tra manifest; repo text này không chứa chúng. README portable lịch sử mô tả bundle đầy đủ có weights; trên Git các binary đã bị loại nên cần bổ sung. Adapter mixed là thử nghiệm giảm full metrics, không khuyến nghị mặc định.

## Volume Modal hiện hữu

Các đường dẫn dưới đây là artifact đã ghi nhận trong tài khoản sở hữu Volume `m3diff`, không phải public URL. Cần tài khoản có quyền truy cập; đăng nhập bình thường, không ghi token vào repo.

| Artifact | Path trong Volume |
|---|---|
| Repo upstream pinned | `baseline_reproduction_v1/repo` |
| Eval code dựng lại | `baseline_reproduction_v1/code/baseline_eval.py` |
| Base checkpoint | `baseline_cache/M3Diff` |
| Dataset cache | `baseline_cache/OmniDiff` |
| Mixed adapter cũ | `invariance_ablation_v1/m3diff-mixed-objective-lora` |
| Control ngày02/11 | `invariance_v2_20261102/m3diff-control-lora` |
| Revised ngày02/11 | `invariance_v2_20261102/m3diff-revised-lora` |

`outputs/invariance_v2_20261102/download.py` tải các file được chỉ định bằng SDK, không mở GPU. Chỉ dùng tên file/path đã kiểm tra trong Volume. Metadata local không chứa full optimizer/scheduler/RNG; adapter dùng được inference nhưng không đảm bảo exact-resume training.

## Những dependency cần biết trước khi chạy thí nghiệm

- Baseline Modal runner có thể tạo Volume và chạy notebook; đây là hành động dùng GPU/credit, không phải bước setup miễn phí. Đọc notebook và cấu hình trước.
- `invariance_v2_20261102/prepare_modal.py` phụ thuộc artifact của `invariance_ablation_v1` trên Volume; không tự dựng toàn bộ lịch sử từ zero.
- `run_modal.py` phụ thuộc repo/base/eval code đã có, các approval/rubric của vòng cũ và `outputs/precision_audit/load_wrapper.py` bên cạnh. Các file `*_APPROVED.json` là khóa provenance của một run cũ, không phải giấy phép chạy lại/vượt ngân sách.
- Runner có kiểm tra output đã tồn tại. Muốn thí nghiệm mới: tạo run folder mới, protocol/gate mới; không ghi đè raw output hoặc tái dùng approval cũ cho data mới.
- Các script report/assessment lưu cách chấm của trợ lý; không biến chúng thành nhãn độc lập bằng cách chạy lại code.

## Kiểm tra integrity của export

`docs/GIT_EXPORT_MANIFEST.json` chứa SHA256 các source/evidence đã copy. Notebook đã xóa output/execution metadata, vì vậy hash khác bản gốc là có chủ ý. Các file text khác giữ nguyên byte. Root/docs handoff mới không thuộc manifest source; Git commit định danh chúng.

Không commit model/data binary; xem `.gitignore`. Không cài hoặc chạy hàng loạt mọi `.py` để kiểm tra repo: nhiều script có side effect ở top level và có thể gọi Modal. Lần export kiểm tra parse Python/JSON, schema notebook và secret patterns; đây không phải kiểm chứng end-to-end training trên fresh machine.
