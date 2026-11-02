from pathlib import Path
import json,hashlib,datetime
root=Path(__file__).parent
old=json.loads((root.parent/'viewpoint_diagnostic/scoring_rubric.json').read_text())
new={
 'computer_desk':['A camera with large lens newly visible on front-left desk','Gray mouse/round patterned item relative arrangement changes'],
 'snowy_street':['Daylight changes to dark/night appearance with artificial lights on'],
 'basin_shelf':['Pink and white soap-bar appearances swap left/center positions'],
 'city_intersection':['Round-headed streetlamp becomes visible beside left sidewalk/crosswalk','Right terrace round-table arrangement changes'],
 'bunk_bedroom':['Broad room lighting dims to a localized brighter patch over beds'],
 'bicycle_alley':['Blue lidded containers newly visible near rear doorway'],
 'render_kitchen':['Person appears at counter','Blue pitcher changes to clear/amber appearance','Right chair shifts toward viewer','Blue floor text kitchen appears']}
obj={'locked_before_reading_candidate_outputs':True,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'Codex assistant, not independent human adjudication',
 'facts':{'old':old['natural_pairs']['facts'],'new':new},
 'excluded_natural':{'new':['clothesline']},
 'geometry':'Record physical unsupported change (0/1), explicit global camera/frame acknowledgement (0/1), illumination inference separately, and uncertainty about apparent image-coordinate motion. Do not force ambiguous apparent-scale/position statements into physical errors.',
 'natural':'Record hit fact indices, clear unsupported claims, uncertainties and explicit suppression of a visible scene change. Keep illumination-only facts separate from physical object count.',
 'masking':'Read masked_predictions only; save all per-candidate assessments before reading mask_key. Stylistic clues may reveal training, so this is procedural masking, not independently blinded human validation.',
 'source_protocol_sha256':hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()}
(root/'eval_rubric.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Locked 22 old and 12 new natural facts before candidate outputs.')
