# Locked V4 — new image-disjoint validation batch

24 pairs; 8 locator queries; 0 captions edited.
Frozen rules, no reference/score access until inference ended. Cached M3Diff captions reused.
Image-disjoint from development and within this batch; not guaranteed scene-disjoint. Claim-focused sample, not full benchmark.

|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|
|---|---|---:|---:|---:|---:|
|Real|baseline|5.54|14.83|27.37|7.95|
|Real|verified|5.54|14.83|27.37|7.95|
|Render|baseline|19.79|21.75|38.90|48.90|
|Render|verified|19.79|21.75|38.90|48.90|

CIDEr recomputed on each subset. Compare arms within the same split only.
No-edit cases retain baseline exactly. Low coverage or a false edit must be reported, not hidden.
Inspect comparison.json and every edited-image panel; manual_review.csv starts with blank human judgments.