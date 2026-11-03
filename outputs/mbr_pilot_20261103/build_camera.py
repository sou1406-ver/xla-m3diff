"""Prepare a separate, no-retry camera diagnostic, without altering prior locks."""
from pathlib import Path
import json,hashlib,shutil,ast
H=Path(__file__).parent; P=H/'camera240';P.mkdir(exist_ok=True)
assert not (P/'ADMISSION.json').exists()
cfg=json.loads((H/'val200/PROTOCOL.json').read_text())
cfg.update(stage='camera240_matched_base_MBR',methods=['batch2_fixed'],batch_size=2,current_budget_cap_usd=2,gpu_timeout_seconds=4200,gpu_soft_stop_seconds=4080,no_retry=True,no_training=True)
(P/'PROTOCOL.json').write_text(json.dumps(cfg,indent=2))
for n in ['questions.json','manifest.jsonl']:shutil.copyfile(H.parent/'r64_camera_eval_20261102'/n,P/n)
src=(H/'evaluate200.py').read_text()
src=src.replace("P=Path('/mnt/m3diff/mbr_pilot_20261103/val200')","P=Path('/mnt/m3diff/mbr_pilot_20261103/camera240')")
src=src.replace("'VAL_ATTEMPT.json'","'ATTEMPT.json'").replace("'questions200.json'","'questions.json'")
src=src.replace("selection={x['id']:x for x in json.loads((P/'selection200.json').read_text())}","selection={x['id']:{'subset':'camera'} for x in questions}")
src=src.replace("/mnt/m3diff/r64_val_precheck_20261102/images/","/mnt/m3diff/ft/camtest/")
# Keep clean/generate/measured byte-for-byte semantics; fixed batch2, fail on OOM.
a=src.index('                errors=[]');b=src.index('            assert len(outputs)==8',a)
src=src[:a]+"                outputs,timing=measured(lambda:[x for _ in range(4) for x in generate(emb,2,True)]);effective=2\n"+src[b:]
src=src.replace("'results200.jsonl'","'results.jsonl'").replace("'planned':200","'planned':240").replace("'VAL_DONE.json'","'GEN_DONE.json'").replace('len(records)==200','len(records)==240')
src=src.replace("'budget_cap_usd':3.60","'budget_cap_usd':2")
(P/'evaluate_camera.py').write_text(src)
old=ast.parse((H/'evaluate200.py').read_text());new=ast.parse(src)
for name in ['clean','generate','measured']:
 f=lambda tree:ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
 assert f(old)==f(new),name
for srcname,dest in [('score_camera_frozen.py','score_camera.py'),('score_captions_frozen.py','score_captions.py'),('ft_common_frozen.py','ft_common.py'),('camera_detector.py','camera_detector.py')]:shutil.copyfile(H.parent/'r64_v2_final_round'/srcname,P/dest)
shutil.copyfile(H/'utility.py',P/'utility.py')
hashes={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in P.iterdir() if x.is_file()}
(P/'ARTIFACT_SHA256.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(hashes,indent=2))
