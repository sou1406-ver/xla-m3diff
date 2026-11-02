"""Same loaded base/GPU: natural controls at1024 followed by candidate cap."""
import json,os,sys,time,runpy
from pathlib import Path
import torch
from llava.model import builder

question_path=Path(os.environ['CAP_PROBE_QUESTIONS'])
protocol=json.loads(Path(os.environ['CAP_PROBE_PROTOCOL']).read_text())
natural=set(protocol['natural_ids'])
answer_path=Path(os.environ['CAP_PROBE_ANSWERS'])
completed=set()
if answer_path.exists():
 for line in answer_path.read_text().splitlines():
  if line.strip():completed.add(json.loads(line)['id'])
order=[q['id'] for q in json.loads(question_path.read_text()) if q['id'] not in completed]
control_path=Path(os.environ['CAP_PROBE_CONTROLS'])
timing_path=Path(os.environ['CAP_PROBE_PAIRED_TIMINGS'])

def append(path,row):
 with path.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())

original=builder.load_pretrained_model
def controlled_loader(*args,**kwargs):
 loaded=original(*args,**kwargs);tokenizer,model=loaded[:2]
 generate=model.generate;index=0
 def controlled_generate(*pos,**kw):
  nonlocal index
  rid=order[index];index+=1
  control_seconds=None
  if rid in natural:
   control_kw=dict(kw,max_new_tokens=1024)
   torch.cuda.synchronize();start=time.monotonic()
   control=generate(*pos,**control_kw)
   torch.cuda.synchronize();control_seconds=time.monotonic()-start
   text=tokenizer.batch_decode(control,skip_special_tokens=True)[0].strip()
   from llava.conversation import conv_templates,SeparatorStyle
   conv=conv_templates['qwen_2'];stop=conv.sep if conv.sep_style!=SeparatorStyle.TWO else conv.sep2
   if text.endswith(stop):text=text[:-len(stop)].strip()
   append(control_path,{'id':rid,'image_id':rid,'caption':text,'generated_token_slots':int(control.shape[-1]),'last_token_id':int(control[0,-1]),'tokenizer_eos_token_id':tokenizer.eos_token_id,'generation_seconds':control_seconds,'max_new_tokens':1024})
  torch.cuda.synchronize();start=time.monotonic()
  output=generate(*pos,**kw)
  torch.cuda.synchronize();candidate_seconds=time.monotonic()-start
  append(timing_path,{'id':rid,'control1024_seconds':control_seconds,'candidate_seconds':candidate_seconds,'candidate_cap':kw['max_new_tokens'],'same_loaded_model_GPU_and_inputs':True,'control_always_generated_first':True})
  return output
 model.generate=controlled_generate
 return loaded
builder.load_pretrained_model=controlled_loader
target=Path(__file__).with_name('run_caption.py');sys.argv[0]=str(target)
runpy.run_path(str(target),run_name='__main__')
