# V2 final round — train complete, staged evaluation running

Completed450/450updates,oneepoch,7200records on A10080GB. Parameters finite,fresh original-base LoRA initialization confirmed. Training4606.35s(76m46s); whole job4808.64s(80m9s). First logged loss.655 atstep5,last.5458 atstep450; loss does not establish model quality.

Checkpoint saved on Volume m3diff:r64_v2_final_round/m3diff-v2-final-lora (adapter_model.bin646058922bytes,non_lora_trainables.bin161524428bytes,configs and trainer state). Metadata only in Git. Original base remains default.

A100 app ap-iDhdDwfZ12VfuvEGX0kOQw stopped2026-11-03 00:19:08+07. A10 staged evaluation dispatched2026-11-03:[app](https://modal.com/apps/sou1406-ver/main/ap-qGtoiJmu0YFjsOKgD5yMnD). Startcamera240; first failed gate stops all later stages. If camera passes,run synth600; if both pass,matchedval200base/v2. No full1570 admitted.

Whole-round conservative upper after actualtrain timing plus worst-case A10evaluation is6.62USD under7USD,including CPUprep,failed pre-training launcher startup,CPU/RAMandstartupallowances. Not actual billed spend. See EVALUATION_ADMISSION.json/ROUND_BUDGET_REVISION1.json. No retraining,no v3,gates frozen.

Data:5400unique ordered replay pairs(3039Real/2361Render),2621sourceimages,271imageconnectedcomponents;1115pairsoverlapoldr64 deliberately retained.1800syntheticpairs from580backgrounds. Unique pairs are not independent scenes; exactrecords notoversampled,oneepoch. No path/RGB overlap with lockedval200.

Pretrain assistant review32syntheticexamples; pretrain colour/location caption corrections logged and hashed. Assistant review12Real camera claims:2correct/plausible,6incorrect,4uncertain; not independent human annotation or a gate. See manifests,audits and originalfrozengates in this folder.

Camera240 completed: objectflags40/180<=54; jointtype+name41/60>=35. Both camera gates PASS. Frozen regex proxies, not human verified semantic rates. Zoom direction only11/90; generic camera descriptions common. Camera240367.31s includingload,~345s generation. Synth600 now running; overall gates not decided, no fulltest.
