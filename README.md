# M3Diff: dựng lại và nghiên cứu cải thiện

**Cập nhật21:43 ngày02/11:** [matched val200 cho r64](outputs/r64_val_precheck_20261102/KET_QUA.md) giảmCIDErở cảhai miền:Real94.41→84.83,Render203.17→163.91. Đây là cohortval, không so điểm với test. Đã tắtGPU; chưa trainv2. [Caption camera v2](outputs/r64_v2_final_round/CAPTION_POLICY.json) và200valđã khóa; exactrecipe/steps/trainbudget vẫn cần chốt.

**Mới nhất20:38 ngày02/11:** [r64 synth600 đã đánh giá xong](outputs/r64_synth_eval_20261102/KET_QUA.md), **trượt gate**: camera sai33/600=5.5% và color69→61/90. Các loại khác có tăng. Có [chấm ảnh40cặp camera bởi trợ lý](outputs/r64_synth_eval_20261102/ASSISTANT_REVIEW.md), không phải nhãn người. App stopped/0task; không full1570, không có điểm OmniDiff r64. Đọc kết quả này trước khi diễn giải tín hiệu camera240 bên dưới.

**Cập nhật19:57 ngày02/11:** [r64 camera240 đã chạy xong](outputs/r64_camera_eval_20261102/KET_QUA.md), GPUđã tắt. Chờ chấm gate semantic; chưa chạy full1570. [Đọc240caption](outputs/r64_camera_eval_20261102/CAPTIONS_240.md) hoặc [CSVđể chấm](outputs/r64_camera_eval_20261102/REVIEW_240.csv). Các kết luận về hai adapterr16 bên dưới vẫn là kết quả riêng, không gán cho r64.

**Đọc đầu tiên:** [Bàn giao context](docs/HANDOFF.md) → [Bản đồ thí nghiệm](docs/EXPERIMENTS.md) → [Kết quả mới nhất, 02/11/2026](outputs/invariance_v2_20261102/KET_QUA.md).

Repo này tập hợp **code thí nghiệm, notebook, caption dự đoán, metric và tài liệu** của nhóm. Đây không phải repo SCST của `ducmanh202005/xla`, cũng không phải bản sao đầy đủ source/weights M3Diff upstream.

## Kết luận hiện tại

- Đã dựng lại inference và đánh giá checkpoint M3Diff gốc trên **1.570 cặp: 803 Real + 767 Render**. Không phải pretrain từ đầu.
- Đã thực sự train nhiều LoRA, một số lượt cũ có cập nhật MDP. LocateAnything chỉ là một nhánh phụ, không phải toàn bộ công việc.
- **Chưa có adapter được chứng minh tốt hơn baseline tổng thể.** Mixed cũ giảm một loại lỗi trong pilot nhưng giảm điểm full benchmark. Hai adapter mới ngày 02/11 cũng không qua gate giữ thông tin thật.
- Giữ **model gốc làm mặc định**. Snapshot cuối cùng xác nhận GPU đã tắt. Chưa chọn hướng nghiên cứu tiếp theo; không tự chạy job trả phí khi chỉ đọc/bàn giao repo.

## Kết quả cần nhớ

Điểm full benchmark bên dưới là raw, ×100; xem [dữ liệu gốc](outputs/mixed_full_benchmark/results/summary_x100.json).

| Model | Real BLEU-4 | Real CIDEr | Render BLEU-4 | Render CIDEr |
|---|---:|---:|---:|---:|
| Baseline | 14.2652 | 33.7526 | 16.9167 | 30.4928 |
| Mixed LoRA cũ | 11.8809 | 32.1295 | 13.7128 | 19.9975 |

Vòng 02/11: 2 model mới, mỗi model 128 optimizer steps; tổng 448 caption đánh giá. Trên stress có thay đổi thật kèm biến đổi hình học, số ý đúng là **baseline 19/29, đối chứng 16/29, sửa dữ liệu 13/29**. Không chạy full benchmark cho hai ứng viên này; không gán điểm full của model cũ cho model mới.

## Cấu trúc và cách đọc

| Đường dẫn | Vai trò |
|---|---|
| [docs/HANDOFF.md](docs/HANDOFF.md) | Context mới nhất, giới hạn kết luận, các hướng chưa làm |
| [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) | Mục lục nhóm thí nghiệm, code và bằng chứng |
| [docs/RUNNING.md](docs/RUNNING.md) | Chạy lại, dữ liệu/weights ngoài Git và phụ thuộc Modal |
| [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md) | Điểm vào dành cho trợ lý đọc repo |
| `outputs/invariance_v2_20261102/` | Vòng mới nhất: code, protocol, nhãn chấm, raw caption, quyết định |
| `outputs/mixed_full_benchmark/`, `outputs/baseline_results/` | Full benchmark cũ và dựng lại baseline |
| `outputs/m3diff_portable/` | Code inference không phụ thuộc Modal; weights không nằm trong Git |
| `outputs/bao_cao_m3diff_chi_tiet/` | Báo cáo dài giai đoạn trước 02/11; không phải trạng thái mới nhất |
| `work/` và notebook ở root | Script hỗ trợ/notebook lịch sử; không phải entrypoint mới mặc định |

Giữ cấu trúc `outputs/` để các script tham chiếu folder anh em không bị hỏng. Đã bỏ output notebook, weights, ảnh, ZIP, virtualenv và file không liên quan. Các manifest lịch sử vẫn giữ nguyên nên có thể nhắc tới binary không được đưa lên Git. [Manifest xuất Git](docs/GIT_EXPORT_MANIFEST.json) liệt kê file được chọn và SHA256.

## Upstream và phạm vi

- M3Diff: https://github.com/Yuan-Liu-01/M3Diff — commit `4e346e52185620ec6fa17235d93b0c26a9d47a71`.
- Base: `IVC-liuyuan/M3Diff`, revision `d6a8880dc789b0816660278c087ac9ebdfe18dd0`.
- Dataset revision đã dùng: `ed4a84cc51912c73e3d54c8643256d9469657552`.
- Nhánh SCST tham khảo riêng: https://github.com/ducmanh202005/xla. Nhóm chưa chạy kiểm chứng checkpoint SCST trong vòng mới này.

Source upstream, model và dataset giữ điều khoản của chủ sở hữu tương ứng. Repo này không cấp lại giấy phép cho chúng. Việc đóng gói Git chỉ kiểm tra tính toàn vẹn/tài liệu, không chạy lại GPU.
