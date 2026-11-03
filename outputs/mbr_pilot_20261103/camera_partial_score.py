from pathlib import Path
import json,pickle,hashlib,sys,subprocess,csv,statistics,shutil
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from utility import select
P=Path('/mnt/m3diff/mbr_pilot_20261103/camera240/partial_diagnostic');ROOT=P.parent.parent
rows=[json.loads(x) for x in (P/'results.jsonl').read_text().splitlines()]
qs=json.loads((P/'questions.json').read_text());assert 0<len(rows)<240 and [r['id'] for r in rows]==[q['id'] for q in qs]
assert hashlib.sha256((ROOT/'train_idf.pkl').read_bytes()).hexdigest()=='e9497a9226a39a2519965001de2c93e6e08ff58c6dc2507cd83a52a02784aa99'
cache=pickle.load((ROOT/'train_idf.pkl').open('rb'))
caps={r['id']:[r['greedy']['caption']]+r['methods']['batch8']['samples'] for r in rows}
toks=PTBTokenizer().tokenize({f'{i}|{j}':[{'caption':s}] for i,cs in caps.items() for j,s in enumerate(cs)})
selection=[]
for i,cs in caps.items():
 j,u=select([toks[f'{i}|{k}'][0] for k in range(9)],cache);selection.append({'id':i,'selected_index':j,'utilities':u,'greedy':cs[0],'MBR':cs[j]})
(P/'SELECTION.json').write_text(json.dumps(selection,indent=2))
for arm,key in [('base','greedy'),('mbr','MBR')]:
 (P/f'{arm}.jsonl').write_text(''.join(json.dumps({'id':r['id'],'caption':r[key]})+'\n' for r in selection))
# Scoring labels are opened only after train-IDF selection has finished.
shutil.copyfile('/mnt/m3diff/synth/code/synth_common.py','/root/synth_common.py')
subprocess.run([sys.executable,'/root/score_camera.py','--root',str(P),'--base',str(P/'base.jsonl'),'--ft',str(P/'mbr.jsonl'),'--synth-code','/root','--out',str(P/'REVIEW_240.csv')],check=True)
rr=list(csv.DictReader((P/'REVIEW_240.csv').open()));truth=lambda s:s.lower()=='true'
summary={}
for arm,label in [('base','greedy'),('ft','MBR')]:
 a=[r for r in rr if r['model']==arm];pure=[r for r in a if r['cond'] not in ['cam_add','cam_remove']];obj=[r for r in a if r['cond'] in ['cam_add','cam_remove']]
 summary[label]={'camera_only_n':len(pure),'object_flags':sum(truth(r['false_obj']) for r in pure),'camera_mentions_pure':sum(truth(r['cam_ok']) for r in pure),'camera_direction_correct':sum(truth(r['dir_ok']) for r in pure),'camera_object_n':len(obj),'joint_type_name':sum(truth(r['obj_type_ok']) and truth(r['obj_name_ok']) for r in obj),'camera_mentions_object':sum(truth(r['cam_ok']) for r in obj),'mean_words':statistics.mean(len(r[label].split()) for r in selection),'median_words':statistics.median(len(r[label].split()) for r in selection)}
summary['partial_only_not_full_camera240']=True
summary['note']='Locked regex proxies on synthetic2D camera data; no claim about internal perception, factual human accuracy, or real3D robustness. Matched fresh greedy, no cached baseline.'
(P/'METRICS.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
