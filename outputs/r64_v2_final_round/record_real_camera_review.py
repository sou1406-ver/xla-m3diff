from pathlib import Path
import json,collections
HERE=Path(__file__).parent/'real_camera_review'
rows=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
labels=[
('uncertain','Dog becomes smaller and field/framing shifts; cannot distinguish animal distance, zoom and camera translation reliably from this pair. Camera-only caption still omits posture/mouth changes.'),
('uncertain','Camera orientation/framing visibly differs, but claimed zoom-out is not clearly established; many object changes omitted.'),
('correct','Shoe rack and room undergo global roll/perspective change consistent with camera counterclockwise roll (image clockwise). Reference same refers to semantic scene, not pixel identity.'),
('uncertain','Panda and wooden background scale/framing differ; possible zoom mixed with posture/position. Claim type not certain; misses bamboo changes.'),
('incorrect','Tub rim/background scale stays similar; toys relocate/rotate/disappear. Claimed zoom-out unsupported by global frame.'),
('incorrect','Dog retreats/turns while background car/tree scale remains similar; no convincing global zoom-out. Also misses most semantic changes.'),
('uncertain','Panda pose and background framing both change; cannot confidently separate camera zoom from subject distance and viewpoint change.'),
('incorrect','Desk/phone/background remain similarly framed while hands/cup move. Global zoom-in unsupported.'),
('correct','The wooden backdrop as well as panda is enlarged/cropped, supporting zoom-in even though reference focuses on posture/bamboo. Caption still omits semantic changes.'),
('incorrect','Dog position/head/lighting change; stable background scale does not support asserted zoom-out.'),
('incorrect','Dog retreats and lighting changes while background scale is comparable; zoom-out not supported.'),
('incorrect','Image goes from close view to wider framing, opposite to claimed zoom-in. Reference no change does not mean no camera nuisance.')]
for row,(label,note) in zip(rows,labels):row.update({'assistant_camera_claim':label,'assistant_note':note,'rater':'assistant; images+reference visible; not independent human; not a gate'})
result={'n':len(rows),'counts':dict(collections.Counter(r['assistant_camera_claim'] for r in rows)),'rubric':'Judge the specific camera claim including direction using visible global background/framing, not reference silence. Keep uncertainty for confounded subject/camera motion. Correct camera claim does not imply correct complete caption.','rows':rows}
(HERE/'ASSISTANT_ASSESSMENTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['counts'])
