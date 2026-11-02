"""New-arm annotations bound to cryptographically shuffled, model-name-masked captions."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
masked=json.loads((HERE/'new_masked.json').read_text())
codes={
'Real_00':['000/001','101/100','011/010','010/001','000/000'],
'Real_01':['100/000','100/100','100/100','100/100','000/000'],
'Real_02':['000/001','110/010','110/110','010/110','000/000'],
'Real_03':['000/010','001/000','001/001','001/001','000/000'],
'Real_04':['100/010','110/000','000/110','000/110','000/000'],
'Real_05':['100/100','100/100','100/100','100/100','100/000'],
'Real_06':['000/001','000/100','000/001','100/100','000/001'],
'Real_07':['100/100','100/100','100/100','100/100','100/100'],
'Render_00':['011/010','011/110','011/110','110/111','001/000'],
'Render_01':['010/010','110/110','010/011','010/110','000/000'],
'Render_02':['000/000','010/000','111/110','011/000','000/000'],
'Render_03':['010/000','010/110','110/110','110/110','000/000'],
'Render_04':['010/000','110/110','110/110','110/110','000/100'],
'Render_05':['000/110','110/010','010/010','010/110','000/000'],
'Render_06':['010/010','110/110','110/010','101/010','000/000'],
'Render_07':['010/010','110/110','110/110','110/110','000/000']}
natural={
'Real_00':[([2,3],['Right-front box said to move although it remains'],['Bottle described as white']),([2],['Purple disinfectant bottle said to be added instead of existing bottle changing'],[])],
'Real_01':[([],[],['Subtle claimed head-raise direction unclear']),([],[],['Subtle head-raise/right-facing direction unclear'])],
'Real_02':[([1,2],[],[]),([1],[],['Bird on ground may refer to background bird; primary large stump bird not established; global dimming and peanut count uncertain'])],
'Real_03':[([],[],['Zoom statement omits locked foreground bicycle event']),([1],[],['White part called rear light; bicycle physical origin uncertain'])],
'Real_04':[([1],['Newly visible red car and black-car disappearance not established'],['Global brightening unclear']),([1],['Red car said to become visible although already present'],['Global brightening unclear'])],
'Real_05':[([1],['Arms said to extend to sides'],[]),([],['Arms said to extend to sides, body turn omitted'],[])],
'Real_06':[([1,2],['Books said to disappear'],['Monitor posture change unclear; replacement can describe occupied position']),([1,2],['Book stack replaced by upright yellow notebooks'],[])],
'Real_07':[([1,2],['Adult said to lie down; extra left-bear pose change not established'],['Cub support surface unclear']),([1,2],['Adult said to lie on snow rather than remain seated/lean over cub'],[])],
'Render_00':[([1],[],[]),([1],[],[])],
'Render_01':[([1,2],[],['Floor letters called sign']),([1,2],['Person said to face table rather than stove'],[])],
'Render_02':[([1,2],['Chair rotation not established'],[]),([1,2],['Chair moves to left although remains at right'],[])],
'Render_03':[([],['Invented disappearing/orienting people'],[]),([],['Invented walking person'],['Lamp apparent-size wording may reflect its real orientation change, not required fact'])],
'Render_04':[([],['Global brightening and chair relocation not established'],[]),([],['Desk rows disappear'],[])],
'Render_05':[([],['Table relocates from left to right'],['Darker image may summarize real dark tabletop; not forced into false-light error']),([],[],['Black tabletop is described but its color change not stated'])],
'Render_06':[([1],['Two chairs said to remain despite right-chair removal'],['White teapot description is not itself an added-object claim']),([1,2,3,4],['Left chair also disappears; yellow cup becomes transparent'],['Green countertop appliance called kettle; pan appearance not confidently established'])],
'Render_07':[([1,2],[],[]),([1,2],[],[])]}
conditions=['identity','zoom_in','zoom_out','roll','brightness'];cases=[]
for r in masked:
    scene=r['scene'].removeprefix('v2_');case={'id':r['id']}
    for i in [1,2]:
        label=f'candidate_{i}';cap=r[label]['caption'];entry={'caption':cap,'raw_sha256':r[label]['raw_sha256']}
        if r['condition']=='natural':
            facts,unsupported,uncertain=natural[scene][i-1]
            entry.update(facts=facts,unsupported=unsupported,uncertain=uncertain,physical=0,false_light=0,wrong_geometry=0,ack=0)
        else:
            code=codes[scene][conditions.index(r['condition'])].split('/')[i-1]
            entry.update(physical=int(code[0]),false_light=int(code[1]),wrong_geometry=int(code[2]),facts=[],unsupported=[],uncertain=[],
                ack=int(r['condition']=='brightness' and code[1]=='0' and any(w in cap.lower() for w in ['bright','illumin','lit up','light in'])))
            if (scene,r['condition'],i) in [('Real_03','zoom_in',2),('Real_06','zoom_in',1),('Real_06','zoom_out',1),('Real_06','roll',2)]:entry['ack']=1
            if scene=='Real_03' and r['condition'] in ['zoom_in','roll'] and i==1:entry['uncertain']=['New tree-branch obscuration not supported by known crop/roll; classified as false visual-geometry explanation, not physical addition']
            if scene=='Render_02' and r['condition']=='roll' and i==2:entry['uncertain']=['Chair clockwise rotation can describe known in-plane image rotation; not forced into intrinsic-object error']
            if scene=='Render_05' and r['condition']=='roll' and i==1:entry['uncertain']=['Blackboard image-coordinate shift can follow roll; not forced into physical error']
            if 'third image' in cap.lower():entry['unsupported']=['Mentions a nonexistent third image']
        case[label]=entry
    cases.append(case)
result={'reviewer':'Codex assistant; model names hidden, not independent human assessment','stage':'new','masked_file_sha256':hashlib.sha256((HERE/'new_masked.json').read_bytes()).hexdigest(),'cases':cases}
(HERE/'new_assessments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('Recorded',len(cases),'new-arm masked cases before decoding.')
