"""Prepare a sequential handoff without modifying the live phase1 process."""
from pathlib import Path
import ast,json
P=Path(__file__).parent
s=(P/'resume_modal.py').read_text()
worker=s[s.index('@app.function(image=image'):s.index('@app.function(image=score_image')]
worker=worker.replace('def generate(deadline):','def generate_phase2(deadline):').replace('timeout=11400','timeout=15900').replace("p/'ADMISSION.json'","p/'ADMISSION_PHASE2.json'").replace("ad['cap_usd']==11","ad['cap_usd']==13.5").replace("p/'STATE.json'","p/'STATE_PHASE2.json'").replace('/root/evaluate_resume.py','/root/evaluate_resume_phase2.py')
scorer=s[s.index('@app.function(image=score_image'):s.index('@app.function(image=modal.Image.debian_slim')]
header='''from pathlib import Path
import modal
H=Path(__file__).parent;V=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr-continuation-phase2')
image=modal.Image.debian_slim(python_version='3.12').apt_install('git').pip_install('uv')
for n in ['evaluate_resume_phase2.py','resume_store.py']:image=image.add_local_file(str(H/n),'/root/'+n,copy=True)
score_image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap')
for n in ['score_resume.py','resume_store.py','utility.py']:score_image=score_image.add_local_file(str(H/n),'/root/'+n,copy=True)
ROOT='/mnt/m3diff/mbr_pilot_20261103';DEST=ROOT+'/resume1020_v1'
'''
tail=(P/'phase2_controller.txt').read_text()
(P/'phase2_modal.py').write_text(header+worker+scorer+tail)
gen=(P/'evaluate_resume.py').read_text().replace("P/'ADMISSION.json'","P/'ADMISSION_PHASE2.json'").replace("admission['cap_usd'] <= 11","admission['cap_usd'] <= 13.5")
(P/'evaluate_resume_phase2.py').write_text(gen)
f=lambda x:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(x).body if isinstance(n,ast.FunctionDef)}
a,b=f((P/'evaluate_resume.py').read_text()),f(gen)
for n in ['generate','clean','measured']:assert a[n]==b[n]
ast.parse((P/'phase2_modal.py').read_text());print('Phase2 prepared:livephase1unchanged,identicalgenerationfunctions.')
