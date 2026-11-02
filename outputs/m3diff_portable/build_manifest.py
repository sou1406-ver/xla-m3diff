"""Validate local export against GPU file hashes and package the portable subset."""
from pathlib import Path
import hashlib,json,zipfile,shutil,argparse
ROOT=Path(__file__).parent;model=ROOT/'model/m3diff-mixed-lora';results=ROOT.parent/'mixed_full_benchmark';audit=json.loads((results/'portable_smoke_audit.json').read_text());inputs=json.loads((results/'portable_smoke.jsonl.run_config.json').read_text());load=json.loads((results/'portable_smoke_load_audit.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert audit['n']==audit['exact_caption_matches_reference_loader']==2
assert load['exact_saved_values_restored'] and load['saved_keys_loaded']==392
expected={Path(p).name:h for p,h in inputs['model_files_sha256'].items() if '/invariance_ablation_v1/m3diff-mixed-objective-lora/' in p}
assert set(expected)=={'adapter_model.bin','adapter_config.json','config.json','non_lora_trainables.bin'}
for name,h in expected.items():assert sha(model/name)==h,(name,'Local export differs from GPU')
with zipfile.ZipFile(model/'adapter_model.bin') as z:assert z.testzip() is None
assert inputs['loader_sha256']==sha(ROOT/'code/run_caption.py'),'Portable GPU-tested loader changed'
assert inputs['eval_runner_sha256']==sha(ROOT/'code/baseline_eval.py')
training=ROOT.parent/'invariance_ablation/results'
provenance={'training_completed':json.loads((training/'mixed_objective_TRAIN_DONE.json').read_text()),'matched_control_audit':json.loads((training/'matched_training_audit.json').read_text()),'training_protocol':json.loads((training/'protocol.json').read_text()),'source_sha256':{n:sha(training/n) for n in ['train.json','train_weighted.py','mixed_objective_TRAIN_DONE.json','matched_training_audit.json']},'training_data_in_export':False,'purpose':'Training provenance only. Inference elsewhere needs the saved adapter and correct base, not retraining.'}
(ROOT/'TRAINING_PROVENANCE.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf8')
manifest={'adapter_name':'mixed_objective','artifact_type':'PEFT LoRA, published M3Diff base required','adapter_files_sha256':expected,'adapter_bytes':(model/'adapter_model.bin').stat().st_size,'model_base':{'repo':'IVC-liuyuan/M3Diff','revision':'d6a8880dc789b0816660278c087ac9ebdfe18dd0'},'repo_commit':'4e346e52185620ec6fa17235d93b0c26a9d47a71','mode':'BF16 base +FP32 unmerged LoRA','GPU_portable_smoke':audit,'saved_adapter_tensors_loaded':392,'all_adapter_values_exactly_restored':True,'same_loader_and_eval_source_hashes_as_GPU_test':True,'no_retraining_on_other_machine':True,'Modal_required_for_inference':False,'evaluation_status':'Full benchmark in progress; diagnostic overall object-or-lighting improvement not established','deployment_default':'Published baseline; this is an experimental portable adapter, not a proved rotation/zoom fix.'}
scored=results/'results/SCORED.json'
if scored.is_file():
 status=json.loads(scored.read_text(encoding='utf8'))
 manifest['official_evaluation']=status
 manifest['evaluation_status']=f"Official matched-ID evaluation completed for {status['n_total']}/1570; full_test_complete={status['full_test_complete']}. See EVALUATION.md for all scores and adverse tradeoffs. Overall geometry adoption gate failed."
 manifest['evaluation_report_sha256']=sha(ROOT/'EVALUATION.md')
 manifest['official_scores_sha256']=sha(results/'results/summary_x100.json')
 evaluation=ROOT/'evaluation';evaluation.mkdir(exist_ok=True)
 for name in ['summary_x100.json','summary_x100.csv','completion_audit.json','SCORED.json','caption_behavior_audit.json','FULL_RUN_VALIDATED.json']:
  if (results/'results'/name).is_file():shutil.copy2(results/'results'/name,evaluation/name)
 for name in ['CAP_AUDIT.json','KET_QUA.md']:
  if (ROOT.parent/'caption_cap_probe'/name).is_file():shutil.copy2(ROOT.parent/'caption_cap_probe'/name,evaluation/('caption_cap_'+name))
 cleanup=ROOT.parent/'caption_cleanup_v2/corpus_audit_with_full.json'
 if cleanup.is_file():shutil.copy2(cleanup,evaluation/'cleanup_corpus_audit.json')
(ROOT/'EXPORT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for n in ['portable_smoke_audit.json','portable_smoke_load_audit.json']:shutil.copy2(results/n,ROOT/n)
parser=argparse.ArgumentParser();parser.add_argument('--zip',action='store_true');args=parser.parse_args()
if args.zip:
 allowed={'README.md','requirements-linux.txt','make_question.py','download_base.py','check_portable_inputs.py','INPUT_CHECKS.json','ADAPTER_FILE_CHECK.json','EXPORT_MANIFEST.json','TRAINING_PROVENANCE.json','portable_smoke_audit.json','portable_smoke_load_audit.json','EVALUATION.md','m3diff-inference-portable.ipynb'}
 with zipfile.ZipFile(ROOT.parent/'m3diff_portable.zip','w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for p in ROOT.rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=p.relative_to(ROOT)
   if rel.parts[0] in ['code','model','evaluation'] or len(rel.parts)==1 and p.name in allowed:z.write(p,str(rel))
print(json.dumps({'all4export_files_match_GPU':True,'adapter_sha256':expected['adapter_model.bin'],'portable_loader_exact_caption_matches':'2/2','LoRA_tensors_loaded':392,'zip_written':args.zip}))
