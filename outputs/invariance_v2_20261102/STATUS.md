# Completed — M3Diff invariance v2, 02/11/2026

- Both new LoRA checkpoints trained and saved:128 updates/1024 sample presentations each. Same initialization and index orders verified; only LoRA trainable, finite losses.
-448 new captions completed:384 main +64 dependent positive/geometry stress captions. All qualitative assessments, uncertain cases and model keys saved.
- Revised-data arm does not beat the control. Control passes the narrow main gate but fails positive-change retention under geometry. Revised arm fails both gates.
- Neither candidate is promoted; no new full1570 run. Existing baseline remains unchanged.
- All6 own Modal apps stopped;0 active tasks verified in `FINAL_GPU_CHECK.json`. No GPU is waiting for review.
- Latest billing snapshot records about$2.10 credit consumption, not a direct final credit balance. The$30 allowance was not exhausted.
- Full result: `KET_QUA.md`. Tables/decisions: `metrics_all_models.json`, `positive_stress/metrics.json`, `decision.json`. Per-caption evidence: `case_scores.csv`.
- Actual weights remain in Modal Volume `m3diff`, `/invariance_v2_20261102/m3diff-control-lora/` and `/invariance_v2_20261102/m3diff-revised-lora/`. Local model folders contain metadata only.
- One supplemental CPU startup import failure was stopped and fixed. Main training was unaffected; successful supplemental preparation and evaluation completed.
