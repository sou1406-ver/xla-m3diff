# V2 final round — audited, training pending

One authorized candidate from original base; no GPU training yet at this snapshot. Total round cap7USD includes preparation/train/evaluation. Frozen gates unchanged; first failure stops, no v3.

7200 records:5400 unique official replay(3039Real/2361Render) +1800 synthetic,450 optimizer updates,LoRAr64/alpha128,LR4e-5,projector1e-5.1115 replay pairs overlap oldr64, deliberately retained. No path/RGB overlap with lockedval200; all2649 source train images hashed.

Assistant visually checked32 generated examples. Coarse HSV colour names removed from600 generated colour captions before training; change claims retained, multi-object examples remain2–3sentences. Camera-object hardcoded center removed. Original replay labels untouched. See DATA_APPROVED.json for exact final hashes and the two caption-cleanup logs.

Assistant reviewed12 Realval camera claims:2 plausible/correct,6 incorrect,4 uncertain; not independent human labels and not a gate.

A10080GB training hardtimeout88min,softstop85min; incomplete training is not a valid candidate and will not be retried. Reserved upper bounds:train4.92,evaluation1.79,CPUprep.25,total6.96USD. Reservations are not actual billed costs.

Evaluate camera240 first, stop on failure; otherwise synth600, then matchedval200base/v2. Full1570 requires every gate plus remaining same7USD budget admission. Model remains baseline by default.

Remote Volume prerequisites:existing m3diff baseline checkpoint/pinned source, synth test600, ft camera240, cached objects and val200. Checkpoints and images intentionally excluded from Git.
