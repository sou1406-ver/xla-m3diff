from pathlib import Path
import hashlib,json,datetime
from registration_gate import decide
root=Path(__file__).parent
thresholds={'minimum_overlap':0.95,'upper_bounds':{'mean_absolute_rgb_error':1.5,'p99_max_channel_error':10,
 'fraction_max_channel_above_30':0.0,'largest_opened_residual_pixels':0}}
rows=json.loads((root/'registration_dev_features.json').read_text());decisions=[(r,decide(r['features'],thresholds)) for r in rows]
assert not any(d['accept_no_scene_change'] for r,d in decisions if r['condition']=='natural')
protocol={'locked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'SIFT + RANSAC global similarity transform; dense comparison in common visible region; exact-pixel identity fast path',
 'thresholds':thresholds,'threshold_selection':'Selected on six dev scenes only. Conservative: no compared pixel may differ by more than 30 RGB levels after registration; no opened coherent residual, at least 95% valid area. Dev furniture transformations deliberately fall back rather than relax thresholds.',
 'registration_source_sha256':hashlib.sha256((root/'registration_gate.py').read_bytes()).hexdigest(),
 'code_note':'Only import cv2 moved inside features() after dev extraction, to permit offline policy application without local OpenCV. Feature extraction math unchanged.',
 'fallback':'Published baseline caption with the same locked exact-sentence dedup. Do not combine with camera-aware prompt.',
 'success_gate':'On six scene-held-aside validation scenes, accept some geometry-only controls and suppress NONE of the six natural changed pairs; reject all 18 locked synthetic appearance-change stress controls. Otherwise approximate registration stays disabled; exact decoded-pixel identity routing may still be used.',
 'validation_access':'No registration validation features read before this lock. These source images and earlier M3Diff captions were already viewed: this is procedural holdout for this gate, not independent external validation.',
 'stress_plan':'For each validation source, invert central 8x8 patch, invert central 2x32 line, or increase all RGB channels by 8. Known visible appearance changes must not be declared unchanged. Synthetic stress only.',
 'limits':['Not a proof that all unchanged pixels are equal. RGB tolerance and downsampling can miss tiny/low-contrast changes.','Similarity transform handles 2D roll/scale/translation, not arbitrary 3D viewpoint, parallax or nonrigid changes.','Only shared visible content is checked; a crop can hide a real change.','Thresholds learned from six reused dev scenes, one small validation; human independent validation still needed.'],
 'dev_counts':{'geometry':sum(r['condition']!='natural' for r,d in decisions),'geometry_routed':sum(d['accept_no_scene_change'] for r,d in decisions if r['condition']!='natural'),'natural':6,'natural_wrongly_routed':0}}
(root/'registration_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf8')
print(json.dumps(protocol['dev_counts']))
