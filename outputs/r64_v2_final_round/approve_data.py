from pathlib import Path
import json,hashlib,datetime,ast
P=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in json.loads((P/'LOCK.json').read_text())['files'].items():assert sha(P/n)==h,n
for p in P.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
review={'rater':'Codex assistant, visual inspection; not independent human annotation','sample_size':32,'selection_sha256':sha(P/'DATA_REVIEW_SELECTION.json'),'boards_reviewed':[f'data_review_{i:02d}.jpg' for i in range(8)],'observations':{'light_same_jpeg':'Observed effects match selected labels; same identity separately pixel-validated.','single_color_multi':'Selected examples show actual colour/other object edits. Coarse HSV colour-name disagreements corrected in all600 generated colour captions before training.','camera_only':'Selected zoom in/out and rotate/pan effects agree with canonical prefixes.','camera_object':'Selected object add/remove and camera edits present. Hardcoded center location removed from all100 labels before training.'},'limitations':['Only32 of1800 synthetic pairs visually inspected, not a full human audit.','Boards retain original pre-cleanup text; final text changes logged in PRETRAIN_CAPTION_FIX.json and FINAL_LABEL_AUDIT.json.','Cutout compositing and 2D camera transformations do not establish real3D robustness.'],'final_train_sha256':sha(P/'data/train.json')}
(P/'DATA_VISUAL_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
validated=json.loads((P/'VALIDATED_DATA.json').read_text());assert validated['train_json_sha256']==review['final_train_sha256']
validated['image_review']='Completed assistant visual check32 stratified examples, see DATA_VISUAL_REVIEW.json; not independent human labels.'
(P/'VALIDATED_DATA.json').write_text(json.dumps(validated,indent=2))
approval={'stage':'APPROVED_BEFORE_FIRST_TRAIN_ATTEMPT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'train_json_sha256':review['final_train_sha256'],'records':7200,'optimizer_steps':450,'no_training_started':True,'files':{n:sha(P/n) for n in ['DATA_RECIPE.json','ROUND_BUDGET.json','CAPTION_POLICY.json','DATA_AUDIT.json','VALIDATED_DATA.json','DATA_VISUAL_REVIEW.json','FINAL_LABEL_AUDIT.json','PRETRAIN_CAPTION_FIX.json','LOCK.json','data/synthetic_manifest.jsonl','data/replay_manifest.json']}}
(P/'DATA_APPROVED.json').write_text(json.dumps(approval,indent=2));print(json.dumps(approval,indent=2))
