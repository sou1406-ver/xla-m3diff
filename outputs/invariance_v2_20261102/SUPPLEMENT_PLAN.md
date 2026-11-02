# Positive-plus-geometry stress test

Added after reading the initial base/old-adapter check, while new arms are still training and before seeing ANY new-arm captions. This supplements rather than replaces the original96-pair gate.

Use the SAME16 natural source pairs and SAME29 locked minimum facts. For even scene indices rotate AFTER by-10degrees with full-field containment; for odd indices show AFTER at88% scale on a neutral canvas. BEFORE remains original. All original content retained. No image/pair selection based on captions.

Evaluate base, old mixed, new control and revised with identical original greedy1024 setup. Report natural fact retention, unsupported claims and correct synthetic-display acknowledgement separately. These are dependent stress variants of the original16 pairs, not16 additional independent scenes or a new holdout.

Purpose: check whether training merely encourages abstention or can retain true changes alongside a nuisance. Do not infer real3D robustness from2D display transformations. This stress set has synthetic borders; do not claim border-independent improvement.

One CPU preparation timeout300seconds and one A10 evaluation timeout1200seconds, reserved through the credit guard. Save results and return GPU. No extra training is introduced by this supplement.
