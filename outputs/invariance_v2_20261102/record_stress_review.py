import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;folder=HERE/'positive_stress'
masked=json.loads((folder/'masked.json').read_text())
# Fact IDs refer to the SAME image-first rubric; tuples are facts, unsupported, uncertainty.
scores={
'Real_00':[([2],['Wrong90degree rotation and invented toy box'],[]),([2],['False rightward camera pan; bottle replaced with toy'],[]),([2],['False rightward camera pan'],['Purple figurine may describe newly visible purple bottle holder']),([2],['False rightward camera pan; bottle replaced with toy'],[])],
'Real_01':[([],[],['No clear head-orientation change beyond looking left']),([],[],['Head raise unclear']),([],[],['No clear head-orientation change beyond looking left']),([],[],['Head raise unclear'])],
'Real_02':[([1],['Peanuts moved between stumps not established'],['Small background bird described; large stump bird omitted']),([1],['Peanut from squirrel mouth placed onto stump not established'],['Small background bird described']),([1],['Peanut from squirrel mouth placed onto stump not established'],['Small background bird described']),([1,2],['Peanuts moved between stumps; source-peanut identity not established'],[])],
'Real_03':[([],['False front-right camera-angle explanation'],[]),([],['False lower camera-angle explanation'],[]),([],['False rightward pan/reveal explanation'],[]),([],['False rightward pan explanation'],[])],
'Real_04':[([1],[],['Red-car absence versus occlusion not confidently settled; global brightening unclear']),([1],[],['Red-car visibility versus occlusion not confidently settled; global brightening unclear']),([1],['Wrong90degree rotation; intensified snowfall not established'],['Red-car visibility uncertain']),([1],['False rightward camera pan'],['Global brightening unclear'])],
'Real_05':[([1],[],[]),([1],[],[]),([1],[],[]),([1],[],[])],
'Real_06':[([],['Camera originally present/swapping positions; books disappear'],[]),([],['Camera originally present, mouse rotates90degrees, notebook disappears'],['Camera now present wording is contradictory, not clear appearance']),([],['Wrong90degree rotation; lens/keyboard replacement and book/stand disappearance'],[]),([1,2],['Notebook replacement not established'],[])],
'Real_07':[([1,2],[],[]),([2],['Adult mouth said to remain open'],[]),([1,2],['Adult lies with head on snow'],['Cub support surface unclear']),([1,2],['Adult lies with head on snow'],[])],
'Render_00':[([1],['Wrong90degree rotation'],[]),([1],[],[]),([1],[],[]),([1],[],[])],
'Render_01':[([1,2],['Additional plate with knife not established'],[]),([1,2],[],[]),([1,2],[],[]),([1,2],['Stainless kettle disappearance not established'],[])],
'Render_02':[([1,2],['Chair turns toward tree'],[]),([1,2],['Chair moves right'],[]),([1,2],['Chair rotation not established'],['Illumination claim uncertain']),([1,2],['Wrong90degree rotation, chair relocation and cup-count change'],[])],
'Render_03':[([],['Invented person and global illumination change'],[]),([],['Invented appearing/disappearing people'],['Darkening claim unclear']),([],['Invented person and global illumination change'],[]),([],['Invented person and global illumination change'],[])],
'Render_04':[([],[],['Only display tilt described; yellow-bag event omitted']),([],['Global brightening not established'],['Smaller apparent blackboard under full-field containment not forced into physical error']),([],[],['Only display tilt described; yellow-bag event omitted']),([],['Scene darkening not established'],[])],
'Render_05':[([],['Table replaced by chair'],['Darker image can summarize true dark tabletop']),([],['Desk row replaced by a rectangular table'],['Apparent blackboard shift not forced into physical error']),([],['Blackboard disappearance and global brightening'],[]),([1],['Global brightening not established'],['Contrasted black-table presence credited as implicit tabletop-color change, not physical addition'])],
'Render_06':[([1,2,3,4],['Left chair disappearance and cup replacement'],['Green appliance called kettle']),([1,2,3,4],['Left chair disappearance and cup replacement'],['Green appliance called kettle']),([1,2,3,4],['Left chair disappearance, cup replacement and new yellow kettle'],['Green appliance called kettle']),([],['Wrong90degree rotation, chair color changes and extra chair'],[])],
'Render_07':[([1,2],[],[]),([2],[],[]),([2],['Wrong90degree rotation'],[]),([2],[],[])]}
cases=[]
for m in masked:
    scene=m['scene'].removeprefix('v2_');r={'id':m['id'],'scene':m['scene'],'domain':m['domain']}
    for i in range(4):
        label=f'candidate_{i+1}';facts,unsupported,uncertain=scores[scene][i]
        r[label]={'caption':m[label]['caption'],'raw_sha256':m[label]['raw_sha256'],'facts':facts,'unsupported':unsupported,'uncertain':uncertain,
                  'display_ack':int(scene=='Render_04' and i in [0,2])}
    cases.append(r)
result={'reviewer':'Codex assistant; four model names hidden, not independent human labels','masked_sha256':hashlib.sha256((folder/'masked.json').read_bytes()).hexdigest(),'cases':cases}
(folder/'assessments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('Recorded64 masked stress captions BEFORE decoding.')
