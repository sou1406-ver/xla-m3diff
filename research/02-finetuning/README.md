# Fine-tuning và bảo toàn thông tin

[← Mục lục nghiên cứu](../README.md) · [Kết quả tổng hợp](../../docs/RESULTS.md)

Caption SFT qua nhiều recipe; chưa có adapter đạt đủ bằng chứng thay base.

| Artifact gốc | Nội dung / kết luận |
|---|---|
| [real_sft_results](../../outputs/real_sft_results/) | SFT random/hard; chưa gain cross-domain ổn định |
| [curated_sft](../../outputs/curated_sft/) | Sửa nhãn; thử LoRA + MDP và LoRA-only |
| [invariance_sft](../../outputs/invariance_sft/) | Invariance v1; trượt retention |
| [invariance_ablation](../../outputs/invariance_ablation/) | Control/mixed matched; tín hiệu giảm physical FP |
| [invariance_confirmation](../../outputs/invariance_confirmation/) | Confirmation; chưa gain tổng thể |
| [prompt_balanced_sft](../../outputs/prompt_balanced_sft/) | Cân bằng template; chưa cứu retention |
| [mixed_full_benchmark](../../outputs/mixed_full_benchmark/) | Mixed cũ giảm CIDEr ở full test |
| [invariance_v2_20261102](../../outputs/invariance_v2_20261102/) | Hai adapter r16, 128 bước mỗi model; trượt gate tổng hợp |
| [r64_camera_eval_20261102](../../outputs/r64_camera_eval_20261102/) | r64 camera240; tín hiệu regex |
| [r64_synth_eval_20261102](../../outputs/r64_synth_eval_20261102/) | r64 synth600; trượt camera/color |
| [r64_val_precheck_20261102](../../outputs/r64_val_precheck_20261102/) | Matched val200; giảm CIDEr cả hai miền |
| [r64_v2_final_round](../../outputs/r64_v2_final_round/) | V2: 450 bước, LoRA + MDP/projector; trượt synth gate |

Đọc report kết quả trước protocol và raw. Các file khóa lựa chọn, assessment và prediction gốc giữ nguyên. Thư mục này là mục lục theo chủ đề; code và bằng chứng nằm tại đường dẫn được liên kết.
