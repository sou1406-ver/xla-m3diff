"""Assistant annotations recorded against masked captions before decoding model keys."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
masked=json.loads((HERE/'initial_masked.json').read_text())
# For identity/zoom-in/zoom-out/roll/brightness: physical, false-light, wrong-geometry.
# Two candidate codes per case; apparent size under zoom is not automatically physical change.
codes={
'Real_00':['000/000','100/100','010/100','100/001','000/000'],
'Real_01':['100/000','100/100','100/100','100/100','100/000'],
'Real_02':['100/000','010/100','110/110','010/110','000/100'],
'Real_03':['000/100','000/100','001/100','100/000','100/000'],
'Real_04':['100/100','110/000','000/100','110/110','000/100'],
'Real_05':['100/100','100/100','100/100','100/100','100/100'],
'Real_06':['000/100','100/100','100/001','100/100','000/100'],
'Real_07':['100/100','100/100','100/100','100/100','100/100'],
'Render_00':['010/010','110/100','110/010','110/110','000/000'],
'Render_01':['100/010','100/110','010/100','100/010','000/000'],
'Render_02':['100/000','010/110','110/110','100/100','000/100'],
'Render_03':['010/010','110/110','110/110','110/110','000/000'],
'Render_04':['100/000','110/011','010/110','011/110','100/000'],
'Render_05':['100/000','110/011','010/010','011/010','000/100'],
'Render_06':['100/010','100/010','010/110','100/010','000/000'],
'Render_07':['100/010','100/110','110/100','100/010','000/000']}
# Natural: fact IDs, unsupported claims, uncertain statements. Minimum fact list is not exhaustive.
natural={
'Real_00': [([2,3],['Right-front box is said to rotate/move although it remains; source bottle color is inaccurate'],[]),([2,3],['Right-front box is said to move to stack although it remains'],['Bottle described as white rather than clear'])],
'Real_01': [([],[],['Subtle head-raise direction not confidently established']),([],[],['Subtle head-raise direction not confidently established'])],
'Real_02': [([1,2],['Implies an additional original squirrel in stump center'],['Global dimming not confidently established']),([1],[],['Bird description could refer to small background bird; does not establish large bird on stump'])],
'Real_03': [([1],[],['White component called rear light; bicycle origin/move uncertain']),([1],[],['Foreground relocation/new visibility credited without forcing physical origin'])],
'Real_04': [([1],['Red car replacement and black-car removal not established'],[]),([1],['Black-car removal and newly visible red car not established'],['Global brightening unclear'])],
'Real_05': [([],['Arms described as extended backward/forward instead of maintaining bent/crossed pose'],[]),([1],['Arms described as extended to sides'],[])],
'Real_06': [([1],['Second mouse disappearance, book-color change, flag disappearance and keyboard-cover disappearance'],[]),([1,2],['Books disappear; camera additionally placed right of keyboard'],[])],
'Real_07': [([1,2],['Adult is said to lie on snow rather than remain seated/lean over cub'],['Cub support surface uncertain']),([2],['Adult mouth said to be open after it closes'],[])],
'Render_00': [([1],[],[]),([1],[],[])],
'Render_01': [([1,2],[],[]),([1,2],['Person said to face table rather than counter/stove'],[])],
'Render_02': [([1,2],['Chair rotation not established'],['Cup-color detail may be real; not required']),([1,2],['Chair relocates left and two cups reduce to one'],[])],
'Render_03': [([],['Invented disappearing/moving people'],[]),([],['Invented walking person'],[])],
'Render_04': [([1],['Blackboard shrinkage not established'],['Bag row description imprecise']),([1],['Global illumination change not established'],[])],
'Render_05': [([],['Blackboard shrinkage and desk-row disappearance'],[]),([],['Tabletop color change reversed; global brightening not established'],[])],
'Render_06': [([1,3,4],['Box replaced by pizza; teapot disappearance; juice replaced by white wine'],['Correct green countertop appliance identified as coffee maker']),([1,3,4],['Left chair disappears; yellow cup becomes white'],['Countertop appliance called kettle; plate/sandwich details uncertain'])],
'Render_07': [([1],['Lamp direction reversal not established'],[]),([1,2],[],[])]}
conditions=['identity','zoom_in','zoom_out','roll','brightness'];cases=[]
for r in masked:
    scene=r['scene'].removeprefix('v2_');case={'id':r['id']}
    for i in [1,2]:
        label=f'candidate_{i}'; cap=r[label]['caption']; entry={'caption':cap,'raw_sha256':r[label]['raw_sha256']}
        if r['condition']=='natural':
            facts,unsupported,uncertain=natural[scene][i-1]
            entry.update(facts=facts,unsupported=unsupported,uncertain=uncertain,physical=0,false_light=0,wrong_geometry=0,ack=0)
        else:
            code=codes[scene][conditions.index(r['condition'])].split('/')[i-1]
            entry.update(physical=int(code[0]),false_light=int(code[1]),wrong_geometry=int(code[2]),facts=[],unsupported=[],uncertain=[],
                         ack=int(r['condition']=='brightness' and not any(map(int,code)) and any(w in cap.lower() for w in ['bright','illumin','lit up','light in'])))
            if scene=='Real_00' and r['condition']=='identity':entry['uncertain']=['Symmetry statement is vague; no explicit change claim']
            if scene=='Real_05' and r['condition']=='identity' and i==1:entry['uncertain']=['Explicit posture-change assertion has redundant endpoints; scored as unsupported change']
            if scene in ['Render_04','Render_05'] and r['condition']=='zoom_out':entry['uncertain']=['Smaller apparent blackboard under wider framing is not forced into physical error']
        case[label]=entry
    cases.append(case)
result={'reviewer':'Codex assistant; model names hidden, not independent human assessment','stage':'initial','masked_file_sha256':hashlib.sha256((HERE/'initial_masked.json').read_bytes()).hexdigest(),'cases':cases}
(HERE/'initial_assessments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('Recorded',len(cases),'masked cases before decoding.')
