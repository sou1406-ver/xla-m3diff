"""Meaningful export checks: exact pixels, one-pixel change and stale-ID resume."""
from pathlib import Path
import json,sys,subprocess,tempfile
from PIL import Image,PngImagePlugin
HERE=Path(__file__).parent;sys.path.insert(0,str(HERE/'code'))
from input_guard import prepare_inputs
test=Path(tempfile.mkdtemp(prefix='input_checks_',dir=HERE))
a=test/'before.png';b=test/'same_RGB_other_metadata.png';changed=test/'one_pixel_change.png'
im=Image.new('RGB',(8,8),(50,100,150));im.save(a);meta=PngImagePlugin.PngInfo();meta.add_text('test','different file bytes, same decoded pixels');im.save(b,pnginfo=meta)
assert a.read_bytes()!=b.read_bytes()
im.putpixel((3,3),(51,100,150));im.save(changed)
def question(path,images):path.write_text(json.dumps([{'id':'one','image':[str(p.resolve()) for p in images],'conversations':[{'from':'human','value':"What's the difference between 2 images?  <image><image>Difference:"}]}]),encoding='utf8')
sameq=test/'same_questions.json';question(sameq,[a,b]);sameout=test/'same_answers.jsonl'
args=['--model-path','not_needed_for_identical_pixels','--question-file',str(sameq),'--answers-file',str(sameout),'--image-folder','.']
run=subprocess.run([sys.executable,str(HERE/'code/run_caption.py'),*args,'--exact-identity-guard'],capture_output=True,text=True)
assert run.returncode==0,run.stderr
row=json.loads(sameout.read_text());assert row['caption_source']=='exact_decoded_RGB_identity_guard'
unchanged=subprocess.run([sys.executable,str(HERE/'code/run_caption.py'),*args,'--exact-identity-guard'],capture_output=True,text=True)
assert unchanged.returncode==0,unchanged.stderr
changedq=test/'changed_questions.json';question(changedq,[a,changed]);changedout=test/'changed_answers.jsonl'
assert prepare_inputs(['--model-path','not_needed','--question-file',str(changedq),'--answers-file',str(changedout)],'unmerged_fp32',True) is False
assert not changedout.exists(),'One-pixel change must never be automatically suppressed'
altered=Image.new('RGB',(8,8),(80,100,150));altered.save(b)
stale=subprocess.run([sys.executable,str(HERE/'code/run_caption.py'),*args,'--exact-identity-guard'],capture_output=True,text=True)
blocked=stale.returncode!=0 and 'Images/questions/model/options differ' in stale.stderr
assert blocked,'Changed image at same path/ID must reject stale prediction resume'
# Restore original fixture so the executable check can run again.
im=Image.new('RGB',(8,8),(50,100,150));im.save(b,pnginfo=meta)
result={'exact_RGB_despite_different_metadata':True,'same_pair_guard_exits_without_torch_or_model_load':True,'unchanged_inputs_resume_successfully':True,'one_changed_pixel_not_guarded':True,'same_ID_changed_file_blocks_stale_resume':True,'GPU_model_smoke':'Not rerun by this CPU check; see portable_smoke_audit.json and EXPORT_MANIFEST.json for the separate 2/2 GPU comparison.'}
(HERE/'INPUT_CHECKS.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
