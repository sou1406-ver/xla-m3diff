"""Optional bounded decoder-cap characterization, after official evaluation."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-caption-cap-probe-v1');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
 .pip_install_from_requirements(str(HERE.parent/'mixed_full_benchmark/requirements.txt'))
 .add_local_dir(str(HERE/'code'),'/root/cap_code',copy=True))
for name in ['questions.json','cached_1024.json','protocol.json','source_audit.json']:
 image=image.add_local_file(str(HERE/name),'/root/cap_inputs/'+name,copy=True)
@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=360,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def run_probe():
 import os,sys,json,time,subprocess,hashlib,zipfile,re,shutil
 start=time.monotonic();root=Path('/mnt/m3diff');out=root/'caption_cap_probe_v1';out.mkdir(exist_ok=True)
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip();assert re.search(r'\bA10(?:G)?\b',gpu)
 for name in ['questions.json','cached_1024.json','protocol.json','source_audit.json']:shutil.copy2('/root/cap_inputs/'+name,out/name)
 protocol=json.loads((out/'protocol.json').read_text());model=root/'invariance_ablation_v1/m3diff-mixed-objective-lora'
 runtime_questions=json.loads((out/'questions.json').read_text())
 for q in runtime_questions:
  q['image']=[('baseline_cache/OmniDiff/'+p if p.startswith(('Real/','Render/')) else p) for p in q['image']]
  assert all((root/p).is_file() for p in q['image']),q['id']
 (out/'questions_runtime.json').write_text(json.dumps(runtime_questions,ensure_ascii=False,indent=2))
 assert hashlib.sha256((model/'adapter_model.bin').read_bytes()).hexdigest()==protocol['adapter_sha256']
 repo=root/'baseline_reproduction_v1/repo'
 env=dict(os.environ,HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo))
 args=[sys.executable,'/root/cap_code/run_caption.py','--model-path',model,'--model-base',root/'baseline_cache/M3Diff','--question-file',out/'questions_runtime.json','--answers-file',out/'cap256.jsonl','--image-folder',root,'--load-audit',out/'load_audit.json','--max-new-tokens','256']
 stopped=False
 with (out/'inference.log').open('w') as log:
  proc=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
  try:proc.wait(timeout=max(1,260-(time.monotonic()-start)))
  except subprocess.TimeoutExpired:
   stopped=True;proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
 rows=[];path=out/'cap256.jsonl'
 if path.exists():
  for line in path.read_text().splitlines():
   try:rows.append(json.loads(line))
   except json.JSONDecodeError:break
 expected=json.loads((out/'questions.json').read_text());reference={r['id']:r for r in json.loads((out/'cached_1024.json').read_text())}
 assert len(rows)==len({r['id'] for r in rows}) and all(r['id'] in reference for r in rows)
 differences=[{'id':r['id'],'exact_cached_match':r['caption']==reference[r['id']]['caption'],'cached_1024':reference[r['id']]['caption'],**r} for r in rows]
 (out/'comparison.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2))
 status={'n_expected':len(expected),'n_completed':len(rows),'complete':len(rows)==len(expected),'soft_stopped':stopped,'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'GPU':gpu,'adapter_sha256':protocol['adapter_sha256'],'cached_reference_not_same_run_timing':True}
 (out/'SUCCESS.json').write_text(json.dumps(status,indent=2))
 for p in Path('/root/cap_code').glob('*.py'):shutil.copy2(p,out/('code_'+p.name))
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py']:z.write(p,p.name)
 volume.commit();print(json.dumps(status),flush=True)
 if proc.returncode and not stopped:raise RuntimeError('Probe failed; logs and partial outputs saved')
@app.local_entrypoint()
def main():run_probe.remote()
