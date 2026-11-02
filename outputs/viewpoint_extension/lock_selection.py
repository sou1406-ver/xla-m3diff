"""Selection follows the gallery review, before any new gate outcomes."""
import datetime,hashlib,json
from pathlib import Path
root=Path(__file__).parent;old=root.parent/'viewpoint_diagnostic'
pool=json.loads((root/'gallery/candidates.json').read_text())
chosen=[(0,'clothesline'),(4,'computer_desk'),(8,'snowy_street'),(13,'basin_shelf'),
        (19,'city_intersection'),(21,'bunk_bedroom'),(23,'bicycle_alley'),(24,'render_kitchen')]
rows=[{**pool[i],'scene':name} for i,name in chosen]
assert [r['index'] for r in rows]==[i for i,n in chosen]
value={'locked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':rows,
 'reviewer':'Codex assistant visual gallery selection, not independent human scene adjudication',
 'freshness':'Eight different scene layouts from the previous twelve-scene geometry diagnostic. Official OmniDiff test images already used for earlier full-baseline inference; this is not an external unseen benchmark.',
 'selection_rule':'Four Real + four Render, scene diversity from a fixed-seed 32-image gallery, chosen by looking at source pictures only, before new gate feature extraction.',
 'frozen_registration_source_sha256':hashlib.sha256((old/'registration_gate.py').read_bytes()).hexdigest(),
 'frozen_thresholds':json.loads((old/'registration_protocol.json').read_text())['thresholds'],
 'nochange_conditions':['identity','zoom_in_1p10','zoom_out_reverse_1p10','roll_8_safe','roll_minus8_zoom'],
 'primary_stress':['square32_delta16','square8_invert','thin2x32_invert','brightness_plus8'],
 'sensitivity_stress':['square16_delta4','brightness_plus1','one_pixel_invert'],
 'natural_pair_rule':'First official question sorted by ID with source as first image, otherwise first containing source. Review paired photos before gate results; count only visually confirmed changes as natural positives.',
 'decision_rule':'Any accepted primary appearance-change stress or confirmed natural positive rules out automatic approximate-caption replacement. Do not retune thresholds on these outcomes. Exact decoded-pixel identity may remain automatic; approximate matching becomes advisory if it fails.',
 'scope':'CPU gate coverage and false-suppression only; no new M3Diff generations, no inferred fresh false-positive reduction or caption metrics.'}
(root/'selection_locked.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Locked eight scenes and unchanged thresholds before new outcomes.')
