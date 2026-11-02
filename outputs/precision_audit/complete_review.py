"""Manual annotation of the 44 new strings; exact matches already have saved labels."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
work=json.loads((ROOT/'review_working.json').read_text());preds=json.loads((ROOT/'comparison_results/masked_predictions.json').read_text())
def mark(i,c,fp,illum=0,ack=0,facts=None,unsupported=None,uncertain=None,note=''):
    row=work['cases'][i];key=f'candidate_{c}';assert row[key] is None,'Do not overwrite a reused annotation'
    p=preds[i];row[key]={'caption':p[key],'fp':fp,'illum':illum,'ack':ack,'identity_diff':int(p['condition']=='identity' and bool(fp or illum or ack)),
      'facts':facts or [],'unsupported':unsupported or [],'uncertain':uncertain or [],'suppression':0,'annotation_source':'manual_new_caption','note':note}

mark(3,2,1,note='Stool cannot move from scene right to left under small global roll/zoom. Table image rotation alone not counted separately.')
mark(4,1,1,facts=[1,3,4],unsupported=['Unsupported stool movement in addition to new stool appearance'],note='Cushion color/goose/total stools correct; shape omitted.')
mark(6,1,1,note='Invented head turning under pure zoom.')
mark(9,1,1,facts=[1],unsupported=['Initial hands at chest','Both arms extended to side instead of one overhead and one near waist'],uncertain=['Anatomical versus image-side lean wording not forced into extra error'],note='Captures squat-to-side-bend but misses locked overhead-arm fact.')
mark(10,1,1,note='Invented leg straightening on identical pixels.')
mark(11,1,1,note='Invented limb changes under zoom; meaning matches earlier erroneous pose description.')
mark(12,2,1,note='Invented facing and leg changes under global roll.')
mark(13,2,1,note='Invented facing, hand and waist changes under global roll/zoom.')
mark(17,2,1,note='Claimed movement across board toward box changes object-relative arrangement, not just image-coordinate shift.')
mark(19,2,0,facts=[1],uncertain=['Food quantity comparison unreliable under changed view'],note='Correct mouse-to-hole event; food count not forced as confirmed error.')
mark(27,1,1,note='Invented leg configuration change under global roll.')
mark(29,1,1,facts=[1],unsupported=['Both initial arms described overhead','Both final arms described forward'],note='Captures raised forward leg, no locked sky/framing fact.')

mark(31,2,1,illum=1,note='Invented individual bed-facing change under pure zoom.')
mark(32,1,1,illum=1,note='Both beds individually face window; global roll only.')
mark(34,1,1,unsupported=['Persistent flowers disappeared','Red bed panel mislabeled as hanging lamp','Red waste bin added instead of bed-end color change'],note='No locked hospital fact correctly identified.')
mark(36,2,1,uncertain=['Border plant visibility may be crop'],note='Bike cannot move from right to left road side under center zoom.')
mark(38,1,1,note='Invented bike relocation and fence replacement; border plant claim not needed for FP.')
mark(42,2,1,uncertain=['Mat apparent orientation follows global roll'],note='Invented chair-facing change and new cookies under geometry-only transform.')
mark(45,2,1,note='Cabinet disappears on identical pixels.')
mark(47,2,1,note='Invented keyboard, monitor and chair changes under global roll.')
mark(48,2,1,note='Invented chair disappearances across nonexistent many table rows, despite unchanged scene content.')
mark(49,1,1,unsupported=['Keyboard replacement','Unchanged chair decreased in size'],note='Misses actual rear monitor rotation.')
mark(51,2,1,illum=1,note='Invented table-facing reversal and pot relocation under pure zoom.')
mark(52,2,1,note='Invented table-to-bench relation and hose shortening.')
mark(53,2,1,illum=1,note='Invented table relocation and changed hose-to-pot relation.')
mark(57,1,1,illum=1,note='Persistent central blackboard removed, beyond a possible apparent-scale statement.')
mark(60,1,1,note='Striped pants disappear on identical pixels.')
mark(67,1,1,note='Keyboard changes horizontal-to-vertical and laptop facing under pure zoom.')
mark(68,1,1,note='Invented keyboard-to-lens relation and new mouse; not simple global coordinates.')
mark(69,1,1,note='Explicit key compression and changed mouse facing under global roll/zoom.')
mark(70,1,1,note='Invented changed keyboard relation and disappearance of purported blue screen under zoom-out.')
mark(74,1,1,note='Invented driveway-to-street movement and physical snow melting under 2D roll.')
mark(80,1,1,illum=1,note='Invented basins swapping actual shelf levels under global roll.')
mark(83,2,1,illum=1,unsupported=['Pink basin moves shelf level despite persistent arrangement'],uncertain=['Bottle/carton visibility changes with steep viewpoint'],note='No correct soap-bar swap fact.')
mark(85,2,1,illum=1,note='Invented person relocation across central scene under pure zoom.')
mark(86,1,1,illum=1,note='Invented central human appearance; additional bin movement also not global frame explanation.')
mark(90,1,1,note='Picture frame removed on identical pixels.')
mark(92,2,1,note='Global roll is8 degrees, not physical90-degree bed-frame rotation.')
mark(93,1,1,uncertain=['Edge boxes may be cropped'],note='Persistent central pillow disappearance is unsupported.')
mark(94,1,1,note='Wider view cannot hide previously visible book/frame/pillow content.')
mark(95,1,1,facts=[1],unsupported=['Persistent gray pillow newly appears'],note='Darkening correct, added pillow incorrect.')
mark(104,1,1,note='Invented chair/plate colors and new kettle under geometry-only input.')
mark(106,2,1,note='Invented chair turning and juice becoming empty under zoom-out.')
mark(107,1,1,facts=[1,4],unsupported=['Persistent chair newly appears','Two-stacked-to-one oven change unsupported','Pitcher replacement described as separate new bottle beside existing blue pot'],uncertain=['Fine glass appearance not resolved'],note='Person and floor text correct; pitcher replacement and chair move not captured.')

def save():
    assert len(work['cases'])==108 and all(r[f'candidate_{c}'] is not None for r in work['cases'] for c in [1,2])
    work['mask_key_opened_before_saving']=False
    (ROOT/'masked_assessments.json').write_text(json.dumps(work,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':save()
