"""Transcribe the assistant's image/text review, before opening the mask key.

Scores below are explicit manual judgements, not text-pattern-based automatic labels.
"""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
preds=json.loads((ROOT/'results/masked_predictions.json').read_text(encoding='utf8'))
rows=[]
def add(scene,condition,fp,light=(0,0),facts=([],[]),unsupported=([],[]),uncertain=([],[]),other=(0,0),note=''):
    rid=scene+'__'+condition;p=next(p for p in preds if p['id']==rid)
    r={'id':rid,'review_note':note}
    for i in range(2):
        r[f'candidate_{i+1}']={'caption':p[f'candidate_{i+1}'],'fp':fp[i],'ack':0,'illumination_fp':light[i],
         'other_error':other[i],'identity_difference':int(condition=='identity' and bool(fp[i] or light[i] or other[i])),
         'facts':facts[i],'unsupported':unsupported[i],'uncertain':uncertain[i]}
    rows.append(r)

add('furniture','identity',(0,0),note='Both correctly say unchanged.')
add('furniture','zoom_1p10',(0,0),(1,1),note='Both infer lighting from geometry-only crop; no object-change claim.')
add('furniture','roll_8_safe',(0,0),(1,1),note='Opposite lighting claims, no physical object change.')
add('furniture','roll_minus8_zoom',(1,1),(1,1),note='Both invent individual stool turning/3D orientation change; whole scene affine only.')
add('furniture','natural',(1,1),facts=([3],[1,3,4]),unsupported=(['Green cushion added to right stool','Blue pillow relocated to gray ottoman','Two new stools instead of total two'],['Existing stool physically moved between tables']),note='Goose present for both. Candidate 2 covers color and total stool count, neither covers cushion shape.')
add('exercise','identity',(0,1),note='Candidate 2 invents changed head direction on identical pixels.')
add('exercise','zoom_1p10',(1,1),note='Both invent head/gaze turning.')
add('exercise','roll_8_safe',(1,1),note='Both invent changed head/body facing.')
add('exercise','roll_minus8_zoom',(1,1),note='Both invent head movement.')
add('exercise','natural',(1,1),facts=([1,2],[1]),unsupported=(['Previous hands at chest instead of low in front'],['Previous hands at chest','New arm extended backward instead of overhead']),note='Candidate 1 captures squat-to-side-bend plus raised arm; candidate 2 only captures the main side bend.')
add('yoga','identity',(1,0),(0,1),note='Candidate 1 invents arm change; candidate 2 invents lighting difference on identical pixels.')
add('yoga','zoom_1p10',(0,1),(1,0),note='Candidate 2 invents limb pose changes.')
add('yoga','roll_8_safe',(1,1),(1,0),note='Both invent pose/orientation changes beyond global roll.')
add('yoga','roll_minus8_zoom',(1,1),(0,1),note='Both invent multiple posture/arm changes.')
add('yoga','natural',(1,1),unsupported=(['Lying on ground instead of standing forward bend','Initial both arms horizontal'],['Head/arms supporting ground instead of hands reaching spread feet','Initial arms horizontal']),note='Neither accurately states the locked standing wide-legged forward bend. No fact hit for merely mentioning a changed pose.')
add('mouse','identity',(0,1),note='Candidate 2 invents head turning/biting.')
add('mouse','zoom_1p10',(1,1),note='Candidate 1 invents head action; candidate 2 asserts food quantity change rather than cropped visibility.')
add('mouse','roll_8_safe',(0,1),uncertain=(['Unqualified moved left could describe global image-coordinate shift; conservatively not counted physical'],[]),note='Candidate 2 invents movement to the other side of box and feed tray.')
add('mouse','roll_minus8_zoom',(1,0),other=(0,1),note='Candidate 1 invents head action. Candidate 2 explicitly says left frame to right; this is a wrong apparent location description, recorded separately from physical relocation.')
add('mouse','natural',(0,0),facts=([1],[1]),uncertain=(['Food quantity comparison unreliable under changed camera framing'],['Food quantity decrease unreliable under changed camera framing']),note='Both correctly describe entry into hole; uncertain food amount is not a confirmed invented physical change.')
add('kitchen','identity',(0,0),(1,0),note='Candidate 1 invents lighting; candidate 2 correctly says unchanged.')
add('kitchen','zoom_1p10',(0,0),(1,1),note='Both infer brighter lighting/scene from crop only.')
add('kitchen','roll_8_safe',(0,1),(1,0),note='Candidate 2 falsely removes visible lid; lids remain in transformed frame.')
add('kitchen','roll_minus8_zoom',(0,0),(1,1),note='Both only infer brighter illumination.')
add('kitchen','natural',(1,1),unsupported=(['Green seasoning bottle replaced with red','Jar claimed only turned, not supported front movement'],['Green seasoning bottle replaced with red']),note='Red/green bottle already present. Neither captures forward jar movement or newly visible separate thermos correctly.')
add('silhouette','identity',(0,1),note='Candidate 2 invents arm movement on identical pixels.')
add('silhouette','zoom_1p10',(1,1),note='Both invent leg pose changes.')
add('silhouette','roll_8_safe',(1,1),note='Both invent leg geometry changes.')
add('silhouette','roll_minus8_zoom',(1,1),note='Both invent different leg pose.')
add('silhouette','natural',(1,1),facts=([1],[1]),unsupported=(['Initial legs apart','Both final arms forward'],['Initial legs/arms configuration','Both final arms forward']),uncertain=(['Only dimmer lighting does not satisfy locked larger-cloud/more-visible-sun fact'],[]),note='Both capture raised forward leg; neither covers the specified sky/framing fact.')
add('hospital','identity',(0,0),(1,1),note='Both claim lighting changes on identical pixels.')
add('hospital','zoom_1p10',(0,0),(1,1),other=(0,1),uncertain=([],['Smaller mats is wrong apparent-scale description; no explicit physical resizing, excluded from physical-FP count']),note='Crop magnifies rather than shrinks. Record scale error separately.')
add('hospital','roll_8_safe',(1,0),(1,1),note='Candidate 1 invents individual bed rotation toward window; candidate 2 only infers light.')
add('hospital','roll_minus8_zoom',(1,1),(1,1),note='Candidate 1 invents flower relocation relative to bed. Candidate 2 falsely removes end tables; known source geometry only.')
add('hospital','natural',(1,1),unsupported=(['Red waste bin added instead of bed end-panel color change'],['Visible flowers disappeared','Red bed panel mislabeled as wrong bedside table']),uncertain=(['Lighting decrease not independently established'],[]),note='Neither captures locked heart picture or correctly names changed bed panel.')
add('street','identity',(0,0),(1,1),note='Both invent darker illumination on identical pixels.')
add('street','zoom_1p10',(1,1),(1,0),uncertain=([],['No-longer-visible border flower pot could be crop; not counted as a physical deletion']),note='Both invent bicycle component/orientation change under pure zoom.')
add('street','roll_8_safe',(1,1),(0,1),uncertain=(['Border pot no longer visible can be crop'],[]),note='Bike facing flip or right-to-left-road relocation is not global 8-degree roll.')
add('street','roll_minus8_zoom',(1,1),(0,1),uncertain=([],['Border pot disappearance may be crop; not a separate confirmed physical error']),note='Candidate 1 invents fence replacement/plant color and bike relocation; candidate 2 invents bike relocation.')
add('street','natural',(1,0),facts=([],[2]),unsupported=(['Bike moved front left instead of toward right curb'],[]),note='Candidate 2 captures shift toward bucket, but neither mentions diagonal rotation.')
add('picnic','identity',(1,1),note='Both invent beach-chair turning on identical pixels.')
add('picnic','zoom_1p10',(1,1),(1,0),note='Both invent chair turning and cup replacement; flower count under crop is uncertain.')
add('picnic','roll_8_safe',(1,1),note='Both invent individual chair/basket relocation. Global mat image orientation alone would not be a physical error.')
add('picnic','roll_minus8_zoom',(1,1),(1,1),note='Both invent chair facing changes; candidate 2 also flower count changes.')
add('picnic','natural',(0,1),facts=([1],[]),unsupported=([],['Unchanged lounge chair added','New pastry mislabeled as plate of cookies']),note='Candidate 1 accurately captures new round pastry; both omit rock and waterfall width.')
add('office','identity',(0,1),(1,0),note='Lighting or cabinet size change on identical pixels is incorrect.')
add('office','zoom_1p10',(1,1),(0,1),note='Keyboard replacement/chair turning or chair removal is invented; middle-left chair remains.')
add('office','roll_8_safe',(1,1),(0,1),note='Multiple invented keyboard/monitor/chair changes, not global frame rotation.')
add('office','roll_minus8_zoom',(1,1),(0,1),note='Multiple individual keyboard/chair movements or relocation relative to table are invented.')
add('office','natural',(1,1),unsupported=(['Keyboard replacement','Trash can disappearance','Unchanged chair rotation'],['Unchanged chair rotation']),note='Both miss the actual rear monitor rotation.')
add('greenhouse','identity',(1,0),(0,1),note='Candidate 1 invents table rotation; candidate 2 invents lighting.')
add('greenhouse','zoom_1p10',(0,1),(1,1),uncertain=(['Several left-side objects shifting left can describe global zoom coordinates; no explicit relative relocation'],[]),note='Candidate 2 invents table facing and pot relocation across entrance.')
add('greenhouse','roll_8_safe',(1,1),(1,0),note='Both claim table set moves next to bench, altering a scene relation; candidate 2 adds hose length change.')
add('greenhouse','roll_minus8_zoom',(1,1),(1,1),note='Both claim table moves next to bench, altering relation; extra plant size claim uncertain apparent scale.')
add('greenhouse','natural',(1,1),unsupported=(['Unchanged table/chairs moved','Persistent plants disappeared'],['Unchanged table/chairs moved','Persistent plants disappeared']),uncertain=(['Lighting increase not established'],[]),note='Neither sees the changed watering-can appearance/location.')
add('classroom','identity',(0,1),(1,0),note='Candidate 1 invents lighting; candidate 2 removes unchanged speaker on identical pixels.')
add('classroom','zoom_1p10',(1,1),(1,1),note='Both invent individual chair movement or board facing reversal.')
add('classroom','roll_8_safe',(0,0),(1,1),other=(0,1),uncertain=([],['Wrong smaller-board apparent scale, no explicit physical resizing; excluded from physical-FP']),note='Both infer illumination; board actually magnified by safe crop.')
add('classroom','roll_minus8_zoom',(0,0),(1,1),other=(1,1),uncertain=(['Wrong apparent scale; physical resizing not explicit'],['Wrong apparent scale; physical resizing not explicit']),note='Both claim board smaller despite affine enlargement.')
add('classroom','natural',(1,1),facts=([1],[1]),unsupported=(['Unchanged chair moved'],['Blackboard facing reversed']),note='Both cover true brightness increase but invent an object change.')

assert len(rows)==len({r['id'] for r in rows})==60
obj={'reviewer':'Codex assistant visual assessment, not independent human gold','model_mapping_opened_before_saving':False,
 'scoring_clarification_before_decoding':'Physical-FP metric follows original object/state criterion; illumination assertions are separate, not silently reclassified as object changes. Ambiguous image-coordinate shifts or apparent size claims are not forced into physical-FP. Wrong apparent scale/direction gets other_error; identity_difference captures any invented change on identical pixels. No prompt/threshold/locked fact changes.',
 'ack_policy':'No candidate explicitly identifies global camera roll/zoom/framing as explanation. Mere object motion or lighting assertion does not count.',
 'cases':rows}
(ROOT/'masked_assessments.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (ROOT/'review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['id','scene','partition','condition','candidate','caption','physical_fp','illumination_inference','other_geometry_error','identity_difference','fact_hits','note','board'])
    for row in rows:
        p=next(p for p in preds if p['id']==row['id'])
        for c in [1,2]:
            q=row[f'candidate_{c}'];writer.writerow([p['id'],p['scene'],p['partition'],p['condition'],c,q['caption'],q['fp'],q['illumination_fp'],q['other_error'],q['identity_difference'],str(q['facts']),row['review_note'],'boards/'+p['id']+'.jpg'])
print('Saved 120 masked assessments without opening model key.')
