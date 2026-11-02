# Invariance v2 — protocol locked before new predictions

User authorizes a new credit-only experiment within $30 renewed Modal credit. Stop below $29.50 consumption, including reservations; no purchases. Save each result and release GPUs after each bounded job.

## Correction to the prior explanation
The old targets already distinguished framing/orientation from object change. This experiment therefore does NOT claim to introduce that distinction for the first time. It tests a package of more explicit nuisance targets, illumination examples, and positive-pair augmentation while keeping natural-caption replay.

## Matched training arms
Both start from the published M3Diff checkpoint, not the degraded prior adapter. Frozen vision/MDP/projector/base; FP32 unmerged language LoRA r16/alpha32. Seed42, LR1e-5, 512 records, 2 epochs, batch1/accum8, 128 updates. Same initial adapter and index sampler order verified; different image/text contents imply RNG consumption need not match.

- `control`: 192 old positive records repeated twice, 64 old negatives repeated twice.
- `revised`: the same192 positives unchanged plus one full-field geometric augmentation of each positive pair (192);128 negatives consisting of the original64 with explicit transform-specific labels,32 identity/geometry repeats and32 brightness-only pairs. No generated model captions as ground truth.
- 96 augmented positives apply a shared rotation/scale to BOTH images, retaining the original caption.96 apply that transform to AFTER only and append the known additional display rotation/scale to the original change caption. The entire original field stays visible on a neutral canvas. This refinement was frozen during image/data review, before any new captions. These are2D perturbations, not real3D camera views. This is a package comparison, not an isolated loss ablation.

## Evaluation and gates
1. Recheck base and existing mixed adapter on a new locked image sample, same decoding.
2. Train only after data and sample previews are reviewed.
3. Evaluate both new arms and base on the same sample. Freeze image-based factual rubric before outputs, mask model names for caption review. Report object, illumination, viewpoint and missed-fact errors jointly.
4. Candidate gate: fewer nuisance cases with ANY unsupported claim than base, no loss in natural-change fact recall in either domain, and no additional unsupported natural claims. Report uncertainty and scene overlap; exact RGB separation does not mean scene independence.
5. Only a passing candidate is eligible for broader evaluation; do not run full1570 merely to spend the allowance. No SCST in this round.

Decoding: original qwen_2 prompt, greedy, max1024, BF16 base, unmerged FP32 adapters, no new repetition penalty. Keep raw captions; any cleanup is identical across arms and separately reported.

## Limits
Old data and official test have previously been observed. New pairs must exclude previous image hashes where possible, but background scenes may repeat. Assistant assessment is not independent human annotation. No claim of unseen-scene or real3D robustness.
