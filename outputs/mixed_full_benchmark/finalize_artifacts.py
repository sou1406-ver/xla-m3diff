"""Assemble local reviewable artifacts after scoring and final budget snapshot."""
from pathlib import Path
import json,subprocess,sys,zipfile,hashlib
HERE=Path(__file__).parent;OUT=HERE.parent
def run(path,*args):subprocess.run([sys.executable,'-X','utf8',str(path),*args],check=True)
scored=json.loads((HERE/'results/SCORED.json').read_text(encoding='utf8'))
if scored['full_test_complete']:run(HERE/'validate_completed_run.py')
run(HERE/'audit_caption_behavior.py')
run(OUT/'caption_cleanup_v2/check_corpus.py','--include-full')
if (OUT/'caption_cap_probe/base128_results/SUCCESS.json').exists():run(OUT/'caption_cap_probe/analyze_probes.py')
run(HERE/'write_final_report.py')
run(OUT/'m3diff_portable/build_manifest.py','--zip')
research=OUT/'m3diff_full_benchmark_results.zip'
with zipfile.ZipFile(research,'w',zipfile.ZIP_DEFLATED) as z:
 for p in (HERE/'results').rglob('*'):
  if p.is_file() and p.suffix in ['.json','.jsonl','.csv','.txt','.log','.py']:z.write(p,'results/'+str(p.relative_to(HERE/'results')))
 for p in HERE.iterdir():
  if p.is_file() and p.suffix in ['.py','.json','.txt']:z.write(p,'code_and_protocol/'+p.name)
 z.write(OUT/'M3DIFF_KET_QUA_MOI_NHAT.md','REPORT.md')
 cap_root=OUT/'caption_cap_probe'
 for p in cap_root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.md','.json','.jsonl','.log']:z.write(p,'caption_cap_probe/'+str(p.relative_to(cap_root)))
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
artifacts=[]
for p in [OUT/'m3diff_portable.zip',research]:
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None,('Corrupt final ZIP',p)
  if p.name=='m3diff_portable.zip':
   assert 'model/m3diff-mixed-lora/adapter_model.bin' in z.namelist()
   assert 'm3diff-inference-portable.ipynb' in z.namelist()
   assert not any('input_checks' in n or '__pycache__' in n for n in z.namelist())
 artifacts.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'ZIP_CRC_all_members_pass':True})
(OUT/'FINAL_ARTIFACTS.json').write_text(json.dumps({'official_evaluation':scored,'artifacts':artifacts},indent=2),encoding='utf8')
print('Final archives verified',json.dumps(artifacts))
