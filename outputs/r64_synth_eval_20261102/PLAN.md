# Locked before synth600 inference

Only evaluate existing r64 on synth600; A10. Reuse existing base answers but rescore both arms with the same scorer. No training, no OmniDiff full. Stop app after results.

Gates supplied by user: false camera mention <=5% (<=30/600) on this no-camera dataset; type recognition of each add/remove/color/move/size/light >= base, separately. Derive exact baseline counts from raw answers, not rounded quoted percentages. Report regex proxies and do not promote solely on them.

Camera-mention primary gate conservatively uses union of `ft_common.CAM` and the existing synth scorer `m_view`; report each separately. This rule is fixed before reading synth600 predictions. Keyword type accuracy follows original synth scorer `type_ok`; semantic correctness is not implied merely by mentioning a change word.

Review40camera rows chosen by fixed stratified random seed20261102 before synth results:6per pure-camera type (24),8per add/remove (16). Assistant semantic review with images; not human labels, not independent blind evaluation. Compare keyword classifier to semantic assessments and preserve uncertainties. No full evaluation until user reviews gate results.
