from pathlib import Path
import json,random
root=Path(__file__).resolve().parents[1];out=root/'outputs/r64_synth_eval_20261102';out.mkdir(exist_ok=True)
cam=root/'outputs/r64_camera_eval_20261102'
man=[json.loads(l) for l in (cam/'manifest.jsonl').read_text().splitlines() if l.strip()]
rng=random.Random(20261102);selected=[]
for cond in ['zoom_in','zoom_out','rotate','pan','cam_add','cam_remove']:
    rows=[r for r in man if r['cond']==cond];selected+=rng.sample(rows,8 if cond.startswith('cam_') else 6)
rng.shuffle(selected)
selection={'seed':20261102,'method':'stratified random 6 per camera-only condition;8 per object condition; fixed before synth600 results','rows':selected,'n':40,'rater':'assistant, not independent human'}
(out/'REVIEW_SELECTION.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
nb=json.loads((cam/'r64-camera-only.ipynb').read_text(encoding='utf-8'));nb['cells']=nb['cells'][:9]
for c in nb['cells']:
    c['source']=[l.replace('r64_camera_eval_20261102','r64_synth_eval_20261102') for l in c['source']]
    c['id']='cell'+str(nb['cells'].index(c))
def code(s):nb['cells'].append({'cell_type':'code','id':'cell'+str(len(nb['cells'])),'metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(True)})
board_code='''from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,textwrap
root=Path('/mnt/m3diff');out=root/'r64_synth_eval_20261102';sel=json.loads((out/'REVIEW_SELECTION.json').read_text())
base={r['id']:r['caption'] for r in [json.loads(l) for l in (root/'ft/eval/camtest_base.jsonl').read_text().splitlines() if l.strip()]}
ft={r['id']:r['caption'] for r in [json.loads(l) for l in (root/'ft/eval/camtest_ft.jsonl').read_text().splitlines() if l.strip()]}
try:font=ImageFont.truetype('DejaVuSans.ttf',19)
except OSError:font=ImageFont.load_default()
for i in range(0,40,4):
    canvas=Image.new('RGB',(1600,3000),'white');d=ImageDraw.Draw(canvas)
    for j,row in enumerate(sel['rows'][i:i+4]):
        y=j*750;pid=row['pair_id'];d.text((10,y+5),f'{i+j+1}. {pid} expected: '+row['caption'],fill='black',font=font)
        for side,name in enumerate(['image_A','image_B']):
            with Image.open(root/'ft/camtest'/row[name]) as im:
                im=im.convert('RGB');im.thumbnail((780,390));canvas.paste(im,(side*800+10,y+40))
        for side,cap in enumerate([base[pid],ft[pid]]):
            lines=textwrap.wrap(('BASE: ' if side==0 else 'R64: ')+cap,width=74)
            for k,line in enumerate(lines[:13]):d.text((side*800+10,y+440+k*22),line,fill='black',font=font)
    canvas.save(out/f'review_board_{i//4:02d}.jpg',quality=90)
print('Saved10reviewboards')
'''
code('selection='+repr(selection)+"\njson.dump(selection,open(f'{RUN}/REVIEW_SELECTION.json','w'),ensure_ascii=False,indent=2)\n"+"subprocess.run([PY,'-c',"+repr(board_code)+"],check=True)\n")
code('''# Exactly synth600 only. No OmniDiff or camera rerun.
assert len(json.load(open(f'{SYN}/data/questions.json')))==600
run_eval(f'{SYN}/data/questions.json',f'{EVAL}/synth_ft.jsonl',f'{SYN}/data',lora=True)
for arm,answers in [('base',f'{SYN}/data/answers.jsonl'),('r64',f'{EVAL}/synth_ft.jsonl')]:
    subprocess.run([PY,f'{SYN}/code/score_captions.py','--root',f'{SYN}/data','--answers',answers,'--out',f'{RUN}/{arm}_scores','--n-manual','0'],check=True)
    shutil.copy2(answers,f'{RUN}/{arm}.jsonl')
shutil.copy2(f'{SYN}/data/manifest.jsonl',f'{RUN}/manifest.jsonl')
shutil.copy2(f'{SYN}/data/questions.json',f'{RUN}/questions.json')
json.dump({'complete':True,'synth_count':600,'full_omnidiff_run':False},open(f'{RUN}/SUCCESS.json','w'),indent=2)
print('DONE synth600 only; release GPU now.')
''')
(out/'r64-synth-only.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
runner=(cam/'run_modal.py').read_text().replace('r64_camera_eval_20261102','r64_synth_eval_20261102').replace('r64-camera-only','r64-synth-only').replace('m3diff-r64-camera-eval','m3diff-r64-synth-eval').replace('timeout=2400','timeout=3000').replace('timeout=1800','timeout=2400')
(out/'run_modal.py').write_text(runner,encoding='utf-8')
print('Built synth600-only and locked40reviewrows')
