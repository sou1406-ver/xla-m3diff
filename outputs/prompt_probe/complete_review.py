"""Manual review of all40 masked questions, then exact within-question propagation."""
from pathlib import Path
import json
ROOT=Path(__file__).parent
work=json.loads((ROOT/'review_working.json').read_text());preds=json.loads((ROOT/'results/masked_predictions.json').read_text())
def mark(i,c,fp=0,illum=0,ack=0,wrong_geometry=0,note='',uncertain=None):
 k=f'candidate_{c}';assert work['cases'][i][k] is None
 work['cases'][i][k]={'caption':preds[i][k],'fp':fp,'illum':illum,'ack':ack,'wrong_geometry':wrong_geometry,'identity_diff':int(preds[i]['condition']=='identity' and bool(fp or illum or wrong_geometry)),'facts':[],'unsupported':[],'uncertain':uncertain or [],'suppression':0,'note':note,'annotation_source':'manual_current_masked_caption'}
for i in range(10):
 for c in [1,2,3]:
  if work['cases'][i][f'candidate_{c}'] is None:
   assert preds[i][f'candidate_{c}'] in ['The white T-shirt on the left disappears.','The white short-sleeved shirt on the left side of the clothesline disappears.']
   mark(i,c,1,note='All masked clothesline outputs reviewed: unchanged white garment falsely disappears under same crop, for every question style')

mark(16,2,uncertain=['Unqualified lens rotation and rightward camera/laptop motions can follow global roll/image coordinates; no explicit side-to-side crossing or facing reversal established'])
for i in range(10,20):
 for c in [1,2,3]:
  if work['cases'][i][f'candidate_{c}'] is None:
   mark(i,c,1,note='All masked desk outputs reviewed: book/mouse/pen disappearances, independent laptop-facing/45to90deg changes, pressed keys or lens-mount revelation under global8deg roll; unqualified coordinate motions alone not used')

for i in range(20,30):
 for c in [1,2,3]:
  k=f'candidate_{c}'
  if work['cases'][i][k] is not None:continue
  text=preds[i][k]
  if text=='The scene has become more visible.':
   mark(i,c,illum=1,note='Visibility/illumination-style tag follows prior rubric. Vague more-visible can mean wider framing; report a separate strict sensitivity count excluding this ambiguous phrase.')
  else:
   mark(i,c,1,note='All masked bunk outputs reviewed: persistent book/frame/pillow disappearances, level swaps or90deg frame turn under wider view; newly visible border content alone not used')

for i in range(30,40):
 for c in [1,2,3]:
  k=f'candidate_{c}'
  if work['cases'][i][k] is not None:continue
  text=preds[i][k]
  if text=='The scene is now more lit up.':mark(i,c,illum=1,note='False brightening on identical pixels')
  else:
   assert text.startswith('The word "Caution"')
   mark(i,c,1,note='Wall text moves or turns horizontal-to-vertical on identical pixels')

def finish():
 for r in work['cases']:
  for c in [1,2,3]:
   k=f'candidate_{c}'
   if r[k] is not None:continue
   text=preds[r['index']][k];same=[r[f'candidate_{j}'] for j in [1,2,3] if r[f'candidate_{j}'] is not None and r[f'candidate_{j}']['caption']==text]
   if same:r[k]={**same[0],'annotation_source':'exact_same_current_question_caption'}
 remaining=[(r['index'],c) for r in work['cases'] for c in [1,2,3] if r[f'candidate_{c}'] is None];print('UNSCORED',len(remaining),remaining[:15])
 if not remaining:(ROOT/'masked_assessments.json').write_text(json.dumps(work,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 else:(ROOT/'review_partial.json').write_text(json.dumps(work,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':finish()
