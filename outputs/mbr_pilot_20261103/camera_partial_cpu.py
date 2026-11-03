"""Conditional CPU-only partial diagnostic; never retries/extends inference."""
from pathlib import Path
import modal
H=Path(__file__).parent;P=H/'camera240';V=modal.Volume.from_name('m3diff');app=modal.App('m3diff-camera-partial-diagnostic')
image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap','pandas','scipy','opencv-python-headless<4.12')
for n in ['utility.py','score_camera.py','score_captions.py','ft_common.py','camera_detector.py']:image=image.add_local_file(str(P/n),'/root/'+n,copy=True)
image=image.add_local_file(str(H/'camera_partial_score.py'),'/root/score.py',copy=True)
@app.function(image=image,cpu=(4,4),memory=(8192,8192),timeout=240,retries=0,max_containers=1,scaledown_window=2,volumes={'/mnt/m3diff':V})
def score_partial():
 import json,subprocess,sys,hashlib,time,collections
 V.reload();src=Path('/mnt/m3diff/mbr_pilot_20261103/camera240');out=src/'partial_diagnostic'
 assert (src/'PIPELINE_DONE.json').exists() and (src/'GPU_DONE.json').exists(),'Must wait until original inference has stopped'
 assert not (out/'ATTEMPT.json').exists(),'No CPU diagnostic retry'
 raw=(src/'results.jsonl').read_bytes();lines=raw.splitlines();records=[];excluded=[]
 for i,line in enumerate(lines):
  try:r=json.loads(line)
  except json.JSONDecodeError:
   assert i==len(lines)-1;excluded.append({'line':i+1,'reason':'truncated last JSON line'});continue
  assert r['greedy']['caption'].strip() and len(r['methods']['batch8']['samples'])==8
  assert all(c.strip() for c in r['methods']['batch8']['samples'])
  assert r['methods']['batch8']['seed']==20261105+int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%1000000
  records.append(r)
 qs=json.loads((src/'questions.json').read_text());assert 0<len(records)<240
 assert [r['id'] for r in records]==[q['id'] for q in qs[:len(records)]]
 ids={r['id'] for r in records};assert len(ids)==len(records)
 out.mkdir(exist_ok=True);(out/'ATTEMPT.json').write_text(json.dumps({'started':time.time(),'no_gpu':True,'partial_only':True}));V.commit()
 try:
  (out/'results.jsonl').write_bytes(b'\n'.join(line for line in lines[:len(records)])+b'\n')
  (out/'questions.json').write_text(json.dumps(qs[:len(records)]))
  manifest=[json.loads(l) for l in (src/'manifest.jsonl').read_text().splitlines()];assert len(manifest)==240
  matched=[r for r in manifest if r['pair_id'] in ids];assert len(matched)==len(records)
  (out/'manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in matched))
  planned=collections.Counter(r['cond'] for r in manifest);observed=collections.Counter(r['cond'] for r in matched)
  coverage={'partial_only':True,'completed':len(records),'planned':240,'missing':240-len(records),'by_condition':{c:{'planned':n,'matched':observed[c],'missing':n-observed[c]} for c,n in planned.items()},'unique_bg_sources':len({r['bg_source'] for r in matched}),'excluded_lines':excluded,'source_raw_sha256':hashlib.sha256(raw).hexdigest(),'note':'Ordered prefix, not a random subset. Missing conditions prevent full240 or full60 conclusions.'}
  (out/'COVERAGE.json').write_text(json.dumps(coverage,indent=2))
  subprocess.run([sys.executable,'/root/score.py'],check=True,timeout=220)
  rows=__import__('csv').DictReader((out/'REVIEW_240.csv').open());breakdown={}
  for r in rows:
   k=r['model']+'|'+r['cond'];g=breakdown.setdefault(k,{'n':0,'object_flags':0,'camera_mentions':0,'joint_type_name':0});g['n']+=1
   for field,col in [('object_flags','false_obj'),('camera_mentions','cam_ok')]:g[field]+=r.get(col,'').lower()=='true'
   g['joint_type_name']+=r.get('obj_type_ok','').lower()=='true' and r.get('obj_name_ok','').lower()=='true'
  (out/'BY_CONDITION.json').write_text(json.dumps(breakdown,indent=2))
  result={'status':'PARTIAL_SCORED_NOT_FULL_CAMERA240','coverage':coverage,'metrics':json.loads((out/'METRICS.json').read_text())};(out/'OUTCOME.json').write_text(json.dumps(result,indent=2));return result
 finally:V.commit()
@app.local_entrypoint()
def main():
 import json,time
 root='/mbr_pilot_20261103/camera240/';local=P/'partial_diagnostic';local.mkdir(exist_ok=True)
 start=time.time()
 while time.time()-start<4500:
  try:done=json.loads(b''.join(V.read_file(root+'PIPELINE_DONE.json')))
  except FileNotFoundError:time.sleep(30);continue
  try:gen=json.loads(b''.join(V.read_file(root+'GEN_DONE.json')))
  except FileNotFoundError:gen={}
  if gen.get('complete'):print('Full generation complete: partial scorer skipped.',flush=True);return
  result=score_partial.remote()
  for n in ['OUTCOME.json','COVERAGE.json','BY_CONDITION.json','METRICS.json','SELECTION.json','REVIEW_240.csv','base.jsonl','mbr.jsonl','results.jsonl','questions.json','manifest.jsonl']:(local/n).write_bytes(b''.join(V.read_file(root+'partial_diagnostic/'+n)))
  print(json.dumps(result),flush=True);return
 raise RuntimeError('Local wait timeout; no inference retried')
