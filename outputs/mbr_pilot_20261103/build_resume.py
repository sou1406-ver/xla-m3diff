"""Prepare continuation inputs; never score the existing550pairs."""
from pathlib import Path
import ast, hashlib, json
P=Path(__file__).parent;F=P/'full1570';R=P/'resume1020_v1';R.mkdir(exist_ok=True)
assert not (R/'ADMISSION.json').exists()
q=json.loads((F/'questions1570.json').read_text());base=(F/'results1570.jsonl').read_bytes()
assert hashlib.sha256(base).hexdigest()=='9c2d55ad4d4cf6cb556255340c2cf2f7894d838d4eec7cf4f7d21089e4aa47fe'
old=[json.loads(s) for s in base.splitlines()];assert len(old)==550
assert [r['id'] for r in old]==[x['id'] for x in q[:550]]
assert all(not (F/n).exists() for n in ['METRICS.json','PER_PAIR.json','SELECTION.json'])
(R/'questions1020.json').write_text(json.dumps(q[550:],indent=2))
sel=json.loads((F/'selection1570.json').read_text());(R/'selection1020.json').write_text(json.dumps(sel[550:],indent=2))
source=(P/'evaluate1570.py').read_text()
source=source.replace("P=Path('/mnt/m3diff/mbr_pilot_20261103/full1570')", "P=Path('/mnt/m3diff/mbr_pilot_20261103/resume1020_v1')")
source=source.replace("assert not (P/'FULL_ATTEMPT.json').exists(),'No automatic repeated benchmark'", "from resume_store import prefix,save\nsession=os.environ['MBR_SESSION_ID']")
source=source.replace("'cap_usd'] <= 18", "'cap_usd'] <= 11")
source=source.replace('questions1570.json','questions1020.json').replace('selection1570.json','selection1020.json')
source=source.replace("(P/'FULL_ATTEMPT.json').write_text(json.dumps({'started':start,'gpu':torch.cuda.get_device_name(0),'model':'base_original','budget_cap_usd':18.00}))", "(P/'sessions'/f'{session}_gpu.json').write_text(json.dumps({'started':start,'gpu':torch.cuda.get_device_name(0),'model':'base_original'}))")
source=source.replace("(P/'GENERATION_AUDIT.json')", "(P/'sessions'/f'{session}_generation_audit.json')")
source=source.replace("records=[];batch_size=2", "records=prefix(questions,P/'pairs');batch_size=2")
source=source.replace("for index,q in enumerate(questions):\n", "for index,q in enumerate(questions):\n    if index<len(records):continue\n")
# len(records) grows during generation; skip only the prefix present at start.
source=source.replace("for index,q in enumerate(questions):\n    if index<len(records):continue", "already_saved=len(records)\nfor index,q in enumerate(questions):\n    if index<already_saved:continue")
source=source.replace("if index==0:", "if index==already_saved:")
source=source.replace("with (P/'results1570.jsonl').open('a') as f:f.write(json.dumps(r)+'\\n')", "r['session_id']=session\n        save(P/'pairs',r)")
source=source.replace("'planned':1570", "'planned':1020").replace('len(records)==1570','len(records)==1020')
source=source.replace("(P/'FULL_DONE.json')", "(P/'sessions'/f'{session}_done.json')")
source=source.replace('MBR1570_PROGRESS','RESUME_PROGRESS')
ast.parse(source);(P/'evaluate_resume.py').write_text(source)
funcs=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
a,b=funcs((P/'evaluate1570.py').read_text()),funcs(source)
for name in ['generate','clean','measured']:assert a[name]==b[name]
scorer=(P/'score1570_cpu.py').read_text().replace("P = ROOT / 'full1570'", "P = ROOT / 'resume1020_v1' / 'combined_full1570'")
ast.parse(scorer);(P/'score_resume.py').write_text(scorer)
print('Prepared1020remainingIDs;unchangedgenerationfunctions;noCIDErscoring.')
