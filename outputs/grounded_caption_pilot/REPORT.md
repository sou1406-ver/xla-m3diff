# Grounded-caption pilot: M3Diff + LocateAnything

24 object-focused pairs, 12 Real + 12 Render. No training. Fixed selection before grounding or scoring.
Baseline vs draft-only rewrite (control) vs draft + locator observations (grounded).
References never used in inference. Scores are for these subsets only; CIDEr is recomputed on each subset.
This is an exploratory pilot, not the full benchmark and not evidence of improvement by itself.

|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|
|---|---|---:|---:|---:|---:|
|Real|baseline|10.77|15.38|26.82|11.43|
|Real|control|10.55|14.88|26.28|11.70|
|Real|grounded|10.40|14.95|26.92|19.06|
|Render|baseline|15.98|19.89|33.85|16.42|
|Render|control|10.93|17.00|30.51|6.54|
|Render|grounded|10.96|16.76|31.92|7.47|

Inspect comparison.json and review_*.jpg. Fill manual_review.csv to distinguish corrected errors from new errors.
Locator output is fallible; same-class detections do not establish identity; misses do not establish absence.
Draft-only proposals cannot verify objects omitted from the initial draft. Both rewrite arms change the prompt distribution.