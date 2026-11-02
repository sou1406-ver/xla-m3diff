"""Bounded base-model decoder-cap check, without any training."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-base-caption-cap-v1');volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
 .pip_install_from_requirements(str(HERE.parent/'mixed_full_benchmark/requirements.txt'))
 .add_local_dir(str(HERE/'code'),'/root/cap_code',copy=True))
for name in ['base_questions.json','cached_base_1024.json','base_protocol.json','source_audit.json']:
 image=image.add_local_file(str(HERE/name),'/root/cap_inputs/'+name,copy=True)
@app.function(image=image,gpu='A10',cpu=4,memory=32768,timeout=360,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def run_probe(cap:int):
 import os,sys,json,time,subprocess,hashlib,zipfile,re,shutil
 assert cap in [128,256]
 start=time.monotonic();root=Path('/mnt/m3diff');out=root/f'baseline_caption_cap_{cap}_v1';out.mkdir(exist_ok=True)
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip();assert re.search(r'\bA10(?:G)?\b',gpu)
 for name in ['base_questions.json','cached_base_1024.json','base_protocol.json','source_audit.json']:shutil.copy2('/root/cap_inputs/'+name,out/name)
 protocol=json.loads((out/'base_protocol.json').read_text());assert cap in protocol['allowed_caps_frozen']
 questions=json.loads((out/'base_questions.json').read_text())
 for q in questions:
  q['image']=[('baseline_cache/OmniDiff/'+p if p.startswith(('Real/','Render/')) else p) for p in q['image']]
  assert all((root/p).is_file() for p in q['image']),q['id']
 (out/'questions_runtime.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2))
 model=root/'baseline_cache/M3Diff';repo=root/'baseline_reproduction_v1/repo'
 env=dict(os.environ,HF_HOME=str(root/'baseline_cache/huggingface'),HF_HUB_DISABLE_XET='1',TOKENIZERS_PARALLELISM='false',M3DIFF_QUANT='none',PYTHONWARNINGS='ignore',CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(repo))
 launcher='/root/cap_code/run_caption.py'
 if cap==128:
  launcher='/root/cap_code/controlled_bootstrap.py'
  env.update(CAP_PROBE_QUESTIONS=str(out/'questions_runtime.json'),CAP_PROBE_PROTOCOL=str(out/'base_protocol.json'),CAP_PROBE_ANSWERS=str(out/'captions.jsonl'),CAP_PROBE_CONTROLS=str(out/'same_GPU_1024_controls.jsonl'),CAP_PROBE_PAIRED_TIMINGS=str(out/'paired_timings.jsonl'))
  (out/'same_GPU_control_extension.json').write_text(json.dumps({'added_before_any_base128_outputs':True,'control':'All19 natural pairs generated1024 then128 with identical loaded base, sameGPU, sameinput tensors and greedy. Four long cases use cap128 only. Control always first; timing has warm-up/order limitations. Cached1024 long captions remain cross-job references.'},indent=2))
 args=[sys.executable,launcher,'--model-path',model,'--question-file',out/'questions_runtime.json','--answers-file',out/'captions.jsonl','--image-folder',root,'--max-new-tokens',str(cap)]
 stopped=False
 with (out/'inference.log').open('w') as log:
  proc=subprocess.Popen(list(map(str,args)),cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
  try:proc.wait(timeout=max(1,(300 if cap==128 else 260)-(time.monotonic()-start)))
  except subprocess.TimeoutExpired:
   stopped=True;proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
 rows=[];path=out/'captions.jsonl'
 if path.exists():
  for line in path.read_text().splitlines():
   try:rows.append(json.loads(line))
   except json.JSONDecodeError:break
 reference={r['id']:r for r in json.loads((out/'cached_base_1024.json').read_text())}
 assert len(rows)==len({r['id'] for r in rows}) and all(r['id'] in reference for r in rows)
 comparison=[{'exact_cached_match':r['caption']==reference[r['id']]['caption'],'cached_1024':reference[r['id']]['caption'],**r} for r in rows]
 (out/'comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2))
 status={'model':'published base, no LoRA','cap':cap,'n_expected':len(questions),'n_completed':len(rows),'complete':len(rows)==len(questions),'soft_stopped':stopped,'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'GPU':gpu,'base_config_sha256':hashlib.sha256((model/'config.json').read_bytes()).hexdigest(),'cached_reference_not_same_run_timing':True}
 status['same_GPU_natural_controls_enabled']=cap==128
 status['caption_row_generation_seconds_includes_control']=cap==128
 (out/'SUCCESS.json').write_text(json.dumps(status,indent=2))
 for p in Path('/root/cap_code').glob('*.py'):shutil.copy2(p,out/('code_'+p.name))
 with zipfile.ZipFile(out/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py']:z.write(p,p.name)
 volume.commit();print(json.dumps(status),flush=True)
 if proc.returncode and not stopped:raise RuntimeError('Base cap probe failed; partial outputs/log saved')
@app.local_entrypoint()
def main(cap:int=256):run_probe.remote(cap)
