"""Record image/caption judgments made after viewing all ten locked boards."""
from pathlib import Path
import json,csv,collections,hashlib
HERE=Path(__file__).parent
sel=json.loads((HERE/'REVIEW_SELECTION.json').read_text(encoding='utf-8'))
original=list(csv.DictReader((HERE.parent/'r64_camera_eval_20261102/REVIEW_240.csv').open(encoding='utf-8-sig')))
byid={r['pair_id']:r for r in original}
# Indexed by displayed board number, not selected after seeing model results.
notes={
1:'Both identify removed bottle; base additionally invents a cup replacement. Bottle color is yellow/orange in rendering.',
2:'Base identifies bag disappearance but calls handbag suitcase: partial. R64 says suitcase shrank, missing removal.',
3:'Base invents several cup/object events and relational movement; r64 gives wrong camera type only.',
4:'Base invents person turning toward/away from camera. R64 describes camera rotation, no object event. Direction not scored here.',
5:'Both detect something added but label pasted teddy fragment mouse/fish. Unnatural cutout makes category visually ambiguous; neither matches target teddy.',
6:'Base uniquely describes removed white object with red/blue stripes, but does not name it as car. R64 names removed white car.',
7:'Both invent vehicle movement; r64 also introduces new vehicle. Camera-only zoom cannot add a new vehicle.',
8:'Both identify added teddy. Reference calls it red but visible bear is brown with red scarf; category/event accepted, not exact color.',
9:'Base invents missing painting and switch/curtain; r64 gives wrong camera type only.',
10:'Base invents chair removals, keyboard and chair changes; r64 gives wrong camera type only.',
11:'Both identify added cup; base adds unsupported brightness. Color wording differs from composite but category/event accepted.',
12:'Both images differ by zoom; base invents flower color change. R64 camera zoom statement only.',
13:'Base identifies removed apple slices but adds false loader orientation change. R64 calls target banana: partial, removal understood but wrong category.',
14:'Base invents potted-plant relocation. R64 reverses zoom direction but no object event.',
15:'Base invents replacement of streetlamp and person absence. R64 wrong camera type only.',
16:'Base invents people changing facing direction. R64 objects appear larger is image appearance, not a physical size claim; camera type still wrong.',
17:'Base misses pasted book. R64 calls it dog and invents vase replacement; both miss target book.',
18:'Base invents chair movement relative to bench and hose deformation. R64 camera zoom only.',
19:'Base invents pillow relocation/new pillow; revealed wall decor alone could be field-of-view. R64 reverses zoom only.',
20:'Base invents kettle replacement, plate movement/addition and drink fill change; r64 reverses zoom only.',
21:'Both identify clock addition; base also invents frame addition/pillow size. R64 wrong camera direction, event retained.',
22:'Base identifies removed printed publication, calls it newspaper rather than book: partial category. R64 identifies removed book; gray vs white not scored.',
23:'Base invents chair movement closer to tree and cup absence. R64 wrong camera type only.',
24:'Both identify teddy addition. Reference orange vs visible brown bear not used to fail category/event. R64 reverses pan.',
25:'Base invents mouse design, monitor pose, laptop relocation etc. R64 zoom only.',
26:'Base invents plant relocation and watering-can size change. R64 wrong camera type only.',
27:'Both say brighter: wrong illumination explanation but no claimed object change. This is not success on overall camera understanding.',
28:'Base invents person pose/facing changes. R64 wrong camera type only.',
29:'Base says right-edge packaging disappeared; pan actually crops it out. Ambiguous disappearance vs physical removal, kept uncertain. R64 camera pan only.',
30:'Both identify added teddy. Pasted teddy includes a human-body fragment; composite quality limits interpretation of fine details.',
31:'Base invents monitor/chair replacements; r64 wrong camera type only.',
32:'Curtain becomes visible by zoom-out, but base also invents cabinet-box content replacement. R64 zoom-out only.',
33:'Both identify removed red apple; base additionally invents basin swap and illumination. R64 adds wrong illumination but retains event.',
34:'Base invents keyboard replacement and chair turning; r64 wrong camera type only.',
35:'Base invents pillow movement and new book. Blanket visibility alone ambiguous, but other claims suffice. R64 reverses zoom only.',
36:'Both identify added book. Phone sits in pasted book crop; base mentioning phone is supported by visible composite.',
37:'Both invent flower color change; r64 does not acknowledge camera. Both also say darker.',
38:'Both identify removed car; base adds wrong dog facing change. R64 retains object event.',
39:'Both identify removed clock; base adds chair/computer replacements. R64 clock color black vs blue not used to fail category/event.',
40:'Base invents dog facing change. Black object lower-left absence can be cropping; r64 wrong camera type only.'}
# Target event: correct requires correct add/remove plus target category or a unique
# visually grounded description; wrong close category remains partial.
events={1:('correct','correct'),2:('partial','incorrect'),5:('incorrect','incorrect'),6:('correct','correct'),8:('correct','correct'),11:('correct','correct'),13:('correct','partial'),17:('incorrect','incorrect'),21:('correct','correct'),22:('partial','correct'),24:('correct','correct'),30:('correct','correct'),33:('correct','correct'),36:('correct','correct'),38:('correct','correct'),39:('correct','correct')}
rows=[]
for i,m in enumerate(sel['rows'],1):
    row=dict(byid[m['pair_id']]);row['review_index']=i
    row['assistant_image_reviewed']=True;row['assistant_note']=notes[i]
    row['review_board']=f'review_board_{(i-1)//4:02d}.jpg'
    if i in events:
        row['assistant_base_correct_target_event'],row['assistant_r64_correct_target_event']=events[i]
        row['assistant_base_object_hallucination']='not_applicable'
        row['assistant_r64_object_hallucination']='not_applicable'
    else:
        row['assistant_base_object_hallucination']='uncertain' if i==29 else ('no' if i==27 else 'yes')
        row['assistant_r64_object_hallucination']='yes' if i in [7,37] else 'no'
        row['assistant_base_correct_target_event']=row['assistant_r64_correct_target_event']='not_applicable'
    rows.append(row)
with (HERE/'ASSISTANT_REVIEW_40.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={'rater':'assistant; not human, not blind; images and model names visible','sample':'stratified40,24camera-only+16camera-object; not population estimate','camera_only':{},'camera_object':{}}
for arm in ['base','r64']:
    pure=[r for r in rows if r['assistant_'+arm+'_object_hallucination']!='not_applicable']
    obj=[r for r in rows if r['assistant_'+arm+'_correct_target_event']!='not_applicable']
    summary['camera_only'][arm]=dict(collections.Counter(r['assistant_'+arm+'_object_hallucination'] for r in pure))
    summary['camera_object'][arm]=dict(collections.Counter(r['assistant_'+arm+'_correct_target_event'] for r in obj))
    comparison=[]
    for r in pure:
        sem=r['assistant_'+arm+'_object_hallucination'];kw=r[('base' if arm=='base' else 'ft')+'_keyword_false_obj']=='True'
        if sem!='uncertain' and kw!=(sem=='yes'):comparison.append({'id':r['pair_id'],'keyword':kw,'semantic':sem,'note':r['assistant_note']})
    summary['camera_only'][arm]['keyword_disagreements']=comparison
summary['rubric']='Object hallucination excludes camera/lighting errors and image-appearance size language. Camera-only physical event claims unsupported by transform count yes. Cropped-out disappearance without clear physical implication may be uncertain. Object-event requires correct operation and category or unique grounded referent; partial wrong close category not forced to correct. Additional errors remain in notes.'
(HERE/'ASSISTANT_REVIEW_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
