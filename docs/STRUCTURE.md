# Cấu trúc và ánh xạ đường dẫn

[← Trang chủ](../README.md) · [Mục lục nghiên cứu](../research/README.md)

## Nguyên tắc

Tổ chức điểm đọc theo tổng quan → kết quả → thí nghiệm → cách chạy. Giữ code và bằng chứng outputs/ tại chỗ vì có phụ thuộc chéo. research/ là mục lục theo chủ đề, không phải bản sao dữ liệu.

## File đã chuyển

| Đường dẫn cũ từ root | Đường dẫn mới |
|---|---|
| m3diff-baseline-full.ipynb | [notebooks/archive/m3diff-baseline-full.ipynb](../notebooks/archive/m3diff-baseline-full.ipynb) |
| m3diff-can-chinh-anh.ipynb | [notebooks/archive/m3diff-can-chinh-anh.ipynb](../notebooks/archive/m3diff-can-chinh-anh.ipynb) |
| m3diff-modal-eval.ipynb | [notebooks/archive/m3diff-modal-eval.ipynb](../notebooks/archive/m3diff-modal-eval.ipynb) |
| m3diff-nb-finetune.ipynb | [notebooks/archive/m3diff-nb-finetune.ipynb](../notebooks/archive/m3diff-nb-finetune.ipynb) |
| m3diff-nb1-bo-test-tong-hop.ipynb | [notebooks/archive/m3diff-nb1-bo-test-tong-hop.ipynb](../notebooks/archive/m3diff-nb1-bo-test-tong-hop.ipynb) |
| m3diff-phan-tich-loi.ipynb | [notebooks/archive/m3diff-phan-tich-loi.ipynb](../notebooks/archive/m3diff-phan-tich-loi.ipynb) |
| docs/HANDOFF.md | [docs/HANDOFF_HISTORY.md](../docs/HANDOFF_HISTORY.md) |
| docs/EXPERIMENTS.md | [docs/EXPERIMENTS_HISTORY.md](../docs/EXPERIMENTS_HISTORY.md) |

File di chuyển giữ nguyên byte; SHA256 ghi trong [REORGANIZATION.json](REORGANIZATION.json). Tài liệu lịch sử vẫn chứa tên file cũ như một phần provenance.

## Script được cập nhật

- work/build_baseline_notebook.py đọc notebook nguồn tại notebooks/archive/.
- work/prepare_git_handoff.py tìm notebook trong notebooks/ thay vì root.

Manifest export cũ được giữ nguyên như bằng chứng lịch sử, không sửa hash để giả inventory mới. Bố cục outputs/ và toàn bộ artifact gốc ở đó được kiểm tra nguyên nội dung trong lần sắp xếp.

## Điểm vào mới

README tổng quan; docs/README, OVERVIEW, RESULTS, HANDOFF, EXPERIMENTS; research/ với 5 nhóm; outputs/README; notebooks/README; work/README. Mục lục nhóm phủ đủ 32 thư mục con của outputs/.

## Kiểm tra sau sắp xếp

[Biên bản QA](REORGANIZATION_QA.json): 1.433 file gốc trong outputs/ giữ nguyên SHA256; 6 notebook di chuyển giữ nguyên byte và parse JSON hợp lệ; 219 link nội bộ mới/cập nhật đều tồn tại tại thời điểm kiểm tra. Đây là kiểm tra tĩnh, không chạy benchmark hay runner GPU.
