# M3Diff — Tái lập và cải thiện mô tả khác biệt giữa hai ảnh

> **Bằng chứng cập nhật đến 04/11/2026.** Đã tái lập đánh giá trên 1.570 cặp. MBR tăng CIDEr trên Render; chưa có adapter fine-tune đủ bằng chứng thay baseline. **Base greedy vẫn là mặc định.**

[Tổng quan](docs/OVERVIEW.md) · [Kết quả](docs/RESULTS.md) · [Thí nghiệm](docs/EXPERIMENTS.md) · [Cách chạy](docs/RUNNING.md) · [Báo cáo BTL](outputs/bao_cao_btl_20261104/BAO_CAO_BTL_M3DIFF.md)

## 1. Bài toán

**Đầu vào:** hai ảnh trước–sau. **Đầu ra:** caption mô tả sự khác biệt.

Mục tiêu là phân biệt thay đổi thật của vật thể (thêm, xóa, đổi màu, di chuyển, đổi kích thước) với biến đổi do camera (zoom, xoay, dịch khung hình). Một cải tiến phải giảm mô tả sai đồng thời giữ các thay đổi thật.

Repo tập hợp code, notebook, protocol và bằng chứng thực nghiệm của nhóm, bắt đầu từ checkpoint M3Diff công bố. Không huấn luyện model từ đầu; không phải bản sao đầy đủ source/weights upstream hoặc repo SCST bên ngoài.

## 2. Kết quả chính

### MBR: giữ nguyên weights, thay cách chọn caption

Sinh **1 caption greedy + 8 caption sampling** cho mỗi cặp, chọn một trong 9 câu bằng consensus CIDEr-D với IDF tập train. Selector không dùng reference val/test để chọn câu.

| Miền test | Số cặp | Base greedy | Base + MBR | Δ CIDEr | CI 95% của Δ |
|---|---:|---:|---:|---:|---|
| Real | 803 | 34,58 | 34,36 | −0,22 | [−3,56; +3,32] |
| Render | 767 | 30,18 | 33,80 | **+3,62** | **[+1,09; +5,98]** |

CIDEr ×100. Full benchmark ghép từ 3 phiên; CI bootstrap theo nhóm ảnh dùng chung. **Có bằng chứng tăng CIDEr trên Render; Real chưa thấy cải thiện.** Điểm reference chưa trực tiếp chứng minh giảm hallucination hoặc hiểu camera tốt hơn. [Báo cáo và dữ liệu gốc](outputs/mbr_pilot_20261103/KET_QUA_FULL1570.md).

### Fine-tune và kiểm tra camera

| Nhánh | Kết quả cuối | Quyết định |
|---|---|---|
| Mixed LoRA cũ | Full test giảm CIDEr: Real 33,75 → 32,13; Render 30,49 → 20,00 | Không thay baseline |
| Control / revised, 02/11 | Hai adapter LoRA-only không đạt đầy đủ gate bảo toàn thông tin thật | Không chạy full cho hai ứng viên |
| r64 và V2 cuối | Có tín hiệu camera trên proxy; trượt gate giữ thông tin ở các bộ khác | Không chọn adapter |
| MBR camera | Partial 174/240; cờ vật thể 127 → 121; thiếu 60 cặp camera + add/remove | Chưa chứng minh cải thiện camera hoặc retention |

**Baseline của hai phép so sánh có điểm khác nhau.** Chỉ so trong cùng protocol, không lấy baseline Mixed để tính gain MBR. [Kết quả chi tiết và giới hạn](docs/RESULTS.md).

## 3. Đọc theo nhu cầu

| Bạn muốn | Điểm bắt đầu |
|---|---|
| Hiểu đề tài trong vài phút | [Tổng quan nghiên cứu](docs/OVERVIEW.md) |
| Xem số liệu có nguồn | [Kết quả](docs/RESULTS.md) |
| Tra từng nhóm thí nghiệm | [Mục lục](docs/EXPERIMENTS.md) → [research/](research/README.md) |
| Chạy inference với hai ảnh | [Điều kiện chạy](docs/RUNNING.md) → [portable](outputs/m3diff_portable/README.md) |
| Tìm notebook | [notebooks/](notebooks/README.md) |
| Tiếp nhận công việc | [Bàn giao hiện tại](docs/HANDOFF.md) |
| Xem thay đổi cấu trúc | [Ánh xạ đường dẫn](docs/STRUCTURE.md) |

## 4. Cấu trúc thư mục

```text
xla-m3diff/
├── README.md                 # Tổng quan và kết luận
├── docs/                     # Phương pháp, kết quả, cách chạy, bàn giao
├── research/                 # Mục lục theo 5 nhóm nghiên cứu
│   ├── 01-baseline/
│   ├── 02-finetuning/
│   ├── 03-decoding/
│   ├── 04-diagnostics/
│   └── 05-reports/
├── notebooks/archive/        # 6 notebook lịch sử từ root
├── outputs/                  # Code + protocol + bằng chứng gốc
└── work/                     # Script hỗ trợ, dữ liệu trung gian lịch sử
```

research/ tổ chức theo chủ đề và dẫn tới artifact gốc trong outputs/. Giữ bố cục outputs/ vì runner có phụ thuộc tương đối giữa các thư mục.

## 5. Điều kiện chạy và tái lập

Git chứa source và bằng chứng dạng text; **không chứa** base checkpoint (~14 GB), vision weights, adapter binary hoặc ảnh dataset. Clone chưa đủ để Run All.

Inference portable dùng Linux/WSL2 + NVIDIA CUDA, Python 3.10; notebook mặc định USE_ADAPTER=False. Runner Modal cần quyền truy cập Volume và artifact lịch sử. Đọc [RUNNING.md](docs/RUNNING.md) trước khi chạy; nhiều script có side effect ngay khi import.

## 6. Nguồn và phạm vi

| Thành phần | Nguồn / revision đã dùng |
|---|---|
| M3Diff upstream | [Yuan-Liu-01/M3Diff](https://github.com/Yuan-Liu-01/M3Diff), commit 4e346e52185620ec6fa17235d93b0c26a9d47a71 |
| Base checkpoint | IVC-liuyuan/M3Diff, revision d6a8880dc789b0816660278c087ac9ebdfe18dd0 |
| Dataset | OmniDiff, revision ed4a84cc51912c73e3d54c8643256d9469657552 |
| SCST tham khảo | [ducmanh202005/xla](https://github.com/ducmanh202005/xla); checkpoint ngoài chưa được nhóm đánh giá độc lập tại đây |

Source, model và dữ liệu upstream giữ điều khoản của chủ sở hữu tương ứng; repo này không cấp lại giấy phép cho chúng. Ghi chú GPU/chi phí là snapshot lịch sử, không phải trạng thái tài khoản trực tiếp hay quyền mở job mới.
