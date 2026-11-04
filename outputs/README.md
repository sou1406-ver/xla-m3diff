# Kho code và bằng chứng thực nghiệm

[← Trang chủ](../README.md) · [Đọc theo chủ đề](../research/README.md) · [Kết quả](../docs/RESULTS.md)

Giữ nguyên bố cục thư mục anh em vì runner phụ thuộc đường dẫn. Không di chuyển raw/metric/protocol chỉ để đổi cách trình bày.

## Tra cứu toàn bộ thư mục

| Thư mục | Nhóm | Nội dung |
|---|---|---|
| [baseline_results](baseline_results/) | [Baseline và triển khai](../research/01-baseline/README.md) | Kết quả tái lập baseline |
| [baseline_source_audit_20261102](baseline_source_audit_20261102/) | [Baseline và triển khai](../research/01-baseline/README.md) | Đối chiếu hai baseline và nguồn SCST |
| [checkpoint_audit_20261102](checkpoint_audit_20261102/) | [Baseline và triển khai](../research/01-baseline/README.md) | Audit checkpoint |
| [m3diff_portable](m3diff_portable/) | [Baseline và triển khai](../research/01-baseline/README.md) | Inference portable; base mặc định, weights tải riêng |
| [real_sft_results](real_sft_results/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | SFT random/hard; chưa gain cross-domain ổn định |
| [curated_sft](curated_sft/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Sửa nhãn; thử LoRA + MDP và LoRA-only |
| [invariance_sft](invariance_sft/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Invariance v1; trượt retention |
| [invariance_ablation](invariance_ablation/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Control/mixed matched; tín hiệu giảm physical FP |
| [invariance_confirmation](invariance_confirmation/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Confirmation; chưa gain tổng thể |
| [prompt_balanced_sft](prompt_balanced_sft/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Cân bằng template; chưa cứu retention |
| [mixed_full_benchmark](mixed_full_benchmark/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Mixed cũ giảm CIDEr ở full test |
| [invariance_v2_20261102](invariance_v2_20261102/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Hai adapter r16, 128 bước mỗi model; trượt gate tổng hợp |
| [r64_camera_eval_20261102](r64_camera_eval_20261102/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | r64 camera240; tín hiệu regex |
| [r64_synth_eval_20261102](r64_synth_eval_20261102/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | r64 synth600; trượt camera/color |
| [r64_val_precheck_20261102](r64_val_precheck_20261102/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | Matched val200; giảm CIDEr cả hai miền |
| [r64_v2_final_round](r64_v2_final_round/) | [Fine-tuning và bảo toàn thông tin](../research/02-finetuning/README.md) | V2: 450 bước, LoRA + MDP/projector; trượt synth gate |
| [mbr_pilot_20261103](mbr_pilot_20261103/) | [Giải mã và chọn caption](../research/03-decoding/README.md) | MBR: full1570 tăng Render; camera partial174/240 |
| [caption_cleanup_v2](caption_cleanup_v2/) | [Giải mã và chọn caption](../research/03-decoding/README.md) | Lọc câu lặp; không kiểm chứng nội dung ảnh |
| [caption_cap_probe](caption_cap_probe/) | [Giải mã và chọn caption](../research/03-decoding/README.md) | Thử giới hạn độ dài; chưa là quality fix |
| [precision_audit](precision_audit/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | BF16 merge so với FP32 unmerged |
| [prompt_probe](prompt_probe/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Crossed prompt probe |
| [locateanything_demo](locateanything_demo/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Demo localization; không train M3Diff |
| [locateanything_robustness](locateanything_robustness/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Probe localization robustness |
| [locateanything_coco](locateanything_coco/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | COCO pilot nhỏ; chưa suy rộng absence reliability |
| [grounded_caption_pilot](grounded_caption_pilot/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Rewrite pilot24; gain không đồng đều giữa miền |
| [m3diff_caption_verifier](m3diff_caption_verifier/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Caption verifier; chưa gain ổn định |
| [caption_verifier_color_v4](caption_verifier_color_v4/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Color verifier; fresh24 sửa 0 caption |
| [viewpoint_diagnostic](viewpoint_diagnostic/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Chẩn đoán viewpoint/alignment |
| [viewpoint_extension](viewpoint_extension/) | [Chẩn đoán, grounding và alignment](../research/04-diagnostics/README.md) | Alignment có false suppression; chỉ exact RGB guard trong pipeline chọn |
| [bao_cao_btl_20261104](bao_cao_btl_20261104/) | [Báo cáo và vận hành](../research/05-reports/README.md) | Báo cáo BTL mới; text/manifest/script trong Git |
| [bao_cao_m3diff_chi_tiet](bao_cao_m3diff_chi_tiet/) | [Báo cáo và vận hành](../research/05-reports/README.md) | Báo cáo dài lịch sử trước 02/11 |
| [modal_budget](modal_budget/) | [Báo cáo và vận hành](../research/05-reports/README.md) | Snapshot chi phí; không phải quyền chạy job |

## Điểm vào ở cấp outputs

- [Notebook baseline](m3diff-baseline-full.ipynb) và [runner Modal](run_baseline_modal.py).
- [Portable inference](m3diff_portable/README.md).
- [MBR full](mbr_pilot_20261103/KET_QUA_FULL1570.md).

RESEARCH_STATE.json, M3DIFF_KET_QUA_MOI_NHAT.md và các snapshot ở root outputs là tài liệu lịch sử. Ưu tiên [bàn giao hiện tại](../docs/HANDOFF.md).
