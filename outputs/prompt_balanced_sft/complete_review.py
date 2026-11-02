"""The17 unseen strings, scored before opening balanced mode key."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
work=json.loads((ROOT/'review_working.json').read_text());preds=json.loads((ROOT/'results/masked_predictions.json').read_text())
def mark(i,c,fp=0,illum=0,ack=0,facts=None,unsupported=None,uncertain=None,note=''):
 k=f'candidate_{c}';assert work['cases'][i][k] is None
 work['cases'][i][k]={'caption':preds[i][k],'fp':fp,'illum':illum,'ack':ack,'identity_diff':int(preds[i]['condition']=='identity' and bool(fp or illum or ack)),'facts':facts or [],'unsupported':unsupported or [],'uncertain':uncertain or [],'suppression':0,'annotation_source':'manual_new_caption','note':note}
mark(1,1,facts=[1,3,4])
mark(4,1)
mark(5,2,1,unsupported=['Initial side plank instead of one-legged balance','Backbend instead of standing forward bend'],note='Explicit backbend contradicts locked forward-bend fact, not credited merely for head-down legs-apart words')
mark(20,1,illum=1)
mark(21,1,1,unsupported=['Persistent table/chair disappear','Bench color replacement unsupported'])
mark(31,2,1,note='Lens independently rotates under crop; monitor static-tilt statement not needed for FP')
mark(32,1,1,note='Pen disappears under global roll; unqualified object coordinate shifts not needed')
mark(34,2,1,note='Independent lens rotation under zoom-out')
mark(35,2,1,unsupported=['Lens replacement by stack','Lens replacement by mouse','Monitor off-to-on unsupported','Lens holder relocates across keyboard'],uncertain=['Wall flags visibility may follow changed framing'])
mark(40,2,1,note='Red car disappears under wider view, opposite visibility direction')
mark(41,2,illum=1,facts=[1],uncertain=['Truck visibility under night exposure not physical removal evidence'])
mark(51,1,1,illum=1,note='Nonexistent person changes body orientation under global transform')
mark(52,1,1,illum=1,note='Nonexistent person turns to camera under wider view')
mark(62,1,illum=1,uncertain=['Wall text left/up wording may describe image coordinates under global roll; no physical text relocation established'])
mark(68,1,1,note='Chair color replacement and glass disappearance under roll')
mark(69,2,1,illum=1,note='Independent chair-facing change and juice transparency change under transform')
mark(71,1,facts=[1,2,4],note='Existing chair now visible does not identify forward movement, but is not an unsupported addition')
for r,p in zip(work['cases'],preds):
 for c in [1,2]:assert r[f'candidate_{c}'] and r[f'candidate_{c}']['caption']==p[f'candidate_{c}']
(ROOT/'masked_assessments.json').write_text(json.dumps(work,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('All144 candidate annotations saved; balanced key still unopened by this script.')
