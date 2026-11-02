"""Input manifest prevents stale-ID resume; optional exact decoded-pixel shortcut."""
from pathlib import Path
import argparse,hashlib,json,os

def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def prepare_inputs(remaining,adapter_mode,exact_identity_guard=False):
 parser=argparse.ArgumentParser(add_help=False)
 for name in ['question-file','answers-file','model-path']:parser.add_argument('--'+name,required=True)
 parser.add_argument('--model-base');parser.add_argument('--image-folder',default='.')
 args,extra=parser.parse_known_args(remaining)
 qfile=Path(args.question_file);out=Path(args.answers_file);out.parent.mkdir(parents=True,exist_ok=True)
 questions=json.loads(qfile.read_text(encoding='utf-8-sig'));ids=[q['id'] for q in questions];assert len(ids)==len(set(ids)),'Question IDs must be unique'
 images={}
 for q in questions:
  assert len(q['image'])==2,'Each question needs exactly2 images'
  for name in q['image']:
   path=Path(os.path.join(args.image_folder,name)).resolve();assert path.is_file(),f'Image missing: {path}'
   if str(path) not in images:images[str(path)]=file_sha(path)
 weights={}
 for folder in [args.model_path,args.model_base]:
  if not folder:continue
  for name in ['config.json','adapter_config.json','adapter_model.bin','non_lora_trainables.bin','download_revision.json']:
   path=Path(folder)/name
   if path.is_file():weights[str(path.resolve())]=file_sha(path)
 bundle_manifest=Path(__file__).resolve().parents[1]/'EXPORT_MANIFEST.json'
 if bundle_manifest.is_file() and (Path(args.model_path)/'adapter_model.bin').is_file():
  expected=json.loads(bundle_manifest.read_text(encoding='utf8'))['adapter_files_sha256']
  for name,digest in expected.items():
   path=(Path(args.model_path)/name).resolve()
   if weights.get(str(path))!=digest:raise RuntimeError(f'Exported adapter file differs from verified GPU checkpoint: {name}. Re-copy the complete model folder.')
 if (Path(args.model_path)/'adapter_config.json').exists() and not args.model_base:raise ValueError('This LoRA adapter needs --model-base pointing to the published M3Diff base.')
 fingerprint={'questions_sha256':file_sha(qfile),'image_file_sha256':images,'model_files_sha256':weights,'model_path':args.model_path,'model_base':args.model_base,'runtime_options':extra,'adapter_mode':adapter_mode,'exact_identity_guard':exact_identity_guard,'eval_runner_sha256':file_sha(Path(__file__).with_name('baseline_eval.py')),'loader_sha256':file_sha(Path(__file__).with_name('run_caption.py'))}
 lock=out.with_name(out.name+'.run_config.json')
 if out.exists() and out.stat().st_size:
  if not lock.exists() or json.loads(lock.read_text(encoding='utf8'))!=fingerprint:raise RuntimeError('Images/questions/model/options differ from this output, or its input manifest is missing. Choose a new --answers-file; do not reuse stale IDs.')
 lock.write_text(json.dumps(fingerprint,ensure_ascii=False,indent=2),encoding='utf8')
 rows={};repair=False
 if out.exists():
  lines=out.read_text(encoding='utf8').splitlines()
  for i,line in enumerate(lines):
   if not line.strip():continue
   try:r=json.loads(line)
   except json.JSONDecodeError:
    assert i==len(lines)-1,'Corrupt JSONL before last line';repair=True;continue
   assert r['id'] in set(ids) and r['image_id']==r['id'] and r['id'] not in rows and isinstance(r['caption'],str) and r['caption'].strip(),'Invalid/duplicate prediction row'
   rows[r['id']]=r
 guarded=[]
 if exact_identity_guard:
  from PIL import Image
  for q in questions:
   if q['id'] in rows:continue
   paths=[Path(os.path.join(args.image_folder,p)) for p in q['image']]
   with Image.open(paths[0]) as im:a=im.convert('RGB')
   with Image.open(paths[1]) as im:b=im.convert('RGB')
   if a.size==b.size and a.tobytes()==b.tobytes():
    rows[q['id']]={'id':q['id'],'image_id':q['id'],'caption':'The two images are identical; no visible changes.','caption_source':'exact_decoded_RGB_identity_guard'};guarded.append(q['id'])
 if guarded or repair:
  temporary=out.with_name(out.name+'.guard.tmp');temporary.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows.values()),encoding='utf8');temporary.replace(out)
 audit={'n_questions':len(ids),'n_already_completed_or_guarded':len(rows),'new_guarded_ids':guarded,'approximate_geometry_used':False,'all_completed_without_loading_model':len(rows)==len(ids)}
 out.with_name(out.name+'.input_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8');print('INPUT AUDIT',json.dumps(audit),flush=True)
 return len(rows)==len(ids)
