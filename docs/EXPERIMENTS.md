# Bản đồ code và bằng chứng

Các đường dẫn bên dưới nằm trong `outputs/`. Mỗi folder thường có runner `.py`, protocol/config, raw `.jsonl`, metric/decision `.json` và report `.md`. Giữ nguyên đường dẫn để đọc được các phụ thuộc tương đối.

| Nhóm | Folder / entrypoint | Đã làm và kết luận |
|---|---|---|
| MBR pilot03/11 | [mbr_pilot_20261103](../outputs/mbr_pilot_20261103/KET_QUA_VAL200.md) | Decoding-only;val200 qua +1CIDEr mỗi miền,Real+20,91/Render+5,23. User đã duyệt18USD;[full đang chạy](../outputs/mbr_pilot_20261103/LIVE_FULL.md),chưađiểmfull. |
| V2 cuối03/11 | [r64_v2_final_round](../outputs/r64_v2_final_round/KET_QUA.md) | Train450steps;từbase;camera40/180và41/60qua,synthcamera124/600và4typefail. Dừng;khôngval/full/v3;giữbase. |
| Dựng lại baseline | [baseline_results](../outputs/baseline_results), [notebook](../outputs/m3diff-baseline-full.ipynb), [Modal runner](../outputs/run_baseline_modal.py) | Full1570 từ checkpoint gốc; hoàn thành inference reproduction |
| SFT đầu tiên | [real_sft_results](../outputs/real_sft_results), [runner](../outputs/run_real_sft_modal.py) | Random/hard caption SFT; không có gain cross-domain bền vững |
| Sửa nhãn SFT | [curated_sft](../outputs/curated_sft) | Original/corrected labels, có LoRA+MDP và LoRA-only; không chọn làm model cuối |
| Invariance v1 | [invariance_sft](../outputs/invariance_sft) | 32 updates; không qua gate giữ natural facts |
| Precision | [precision_audit](../outputs/precision_audit) | BF16 merge vs FP32 unmerged; có numerical difference nhưng không phải quality fix |
| Matched ablation | [invariance_ablation](../outputs/invariance_ablation) | 64 updates control vs mixed; giảm physical FP, còn lỗi ánh sáng/geometry |
| Confirmation | [invariance_confirmation](../outputs/invariance_confirmation) | 80 cases; mixed physical FP36→29/48 nhưng joint44→44; không phải overall gain |
| Prompt | [prompt_balanced_sft](../outputs/prompt_balanced_sft), [prompt_probe](../outputs/prompt_probe) | Cân bằng template và crossed prompt probe; không cứu factual retention |
| Full mixed benchmark | [mixed_full_benchmark](../outputs/mixed_full_benchmark) | Đủ1570; mixed giảm raw CIDEr Real33.75→32.13, Render30.49→20.00 |
| **Vòng mới nhất** | [invariance_v2_20261102](../outputs/invariance_v2_20261102) | 2×128 updates,448 captions; cả hai không qua mọi gate; không promote |
| LocateAnything | [locateanything_demo](../outputs/locateanything_demo), [locateanything_robustness](../outputs/locateanything_robustness), [locateanything_coco](../outputs/locateanything_coco) | Localization probes; không phải train M3Diff; mẫu COCO nhỏ, không suy rộng absence reliability |
| Grounded rewrite | [grounded_caption_pilot](../outputs/grounded_caption_pilot) | Pilot24: RealCIDEr11.43→19.06, Render16.42→7.47; rewrite confounds |
| Caption verifier | [m3diff_caption_verifier](../outputs/m3diff_caption_verifier), [caption_verifier_color_v4](../outputs/caption_verifier_color_v4) | Dev24 sửa1caption, fresh24 sửa0; chưa có gain ổn định |
| Registration | [viewpoint_diagnostic](../outputs/viewpoint_diagnostic), [viewpoint_extension](../outputs/viewpoint_extension) | Approximate alignment gate false-suppressed20/56 syntheticchange probes; chỉ exactRGB guard an toàn trong pipeline đã chọn |
| Cleanup/cap | [caption_cleanup_v2](../outputs/caption_cleanup_v2), [caption_cap_probe](../outputs/caption_cap_probe) | Cleanup tăng lexical metric nhỏ, không image understanding; cap chưa là quality fix |
| Portable inference | [m3diff_portable](../outputs/m3diff_portable) | Default base; optional mixed experimental; binary không commit |
| Báo cáo lịch sử | [báo cáo dài](../outputs/bao_cao_m3diff_chi_tiet/BAO_CAO_M3DIFF_CHI_TIET.md) | Giai đoạn trước02/11; đọc training sections9–10,14–19; không chỉ LocateAnything |

## Đọc vòng mới nhất theo thứ tự

1. `KET_QUA.md`, `PROVENANCE_NOTES.md`, `decision.json`.
2. `PLAN.md`, `SUPPLEMENT_PLAN.md`, `SELECTION_POLICY.md`, `SELECTION_LOCK.json`.
3. `train_control.json`, `train_revised.json`, `data_audit.json`, `MATCHED_TRAIN_DONE.json`, metadata trong hai folder adapter.
4. `metrics_all_models.json`, `positive_stress/metrics.json`, `case_scores.csv`.
5. Raw `baseline.jsonl`, `old_mixed.jsonl`, `control.jsonl`, `revised.jsonl` và bản trong `positive_stress/`; masked assessments + keys cho phép kiểm tra cách chấm.
6. Code `prepare_modal.py`, `train_audited.py`, `run_modal.py`, `supplement_modal.py`, các script report/review. Đọc prerequisites trước khi chạy.

Không lấy số ở các bộ pilot khác nhau cộng chung; chúng khác mẫu, rubric, prompt và mức độ đã nhìn thấy dữ liệu. Raw vs dedup phải so cùng processing. File manifest cũ có thể nhắc ảnh/ZIP/weights đã được cố ý loại khỏi Git.
