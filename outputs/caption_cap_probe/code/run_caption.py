"""Portable M3Diff inference: published base plus trained LoRA, no Modal dependency."""
import argparse,json,os,runpy,sys,types
from pathlib import Path

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--adapter-mode',choices=['unmerged_fp32','merged_bf16'],default='unmerged_fp32')
parser.add_argument('--load-audit',type=Path,default=Path('adapter_load_audit.json'))
parser.add_argument('--exact-identity-guard',action='store_true')
args,remaining=parser.parse_known_args()
os.environ.setdefault('M3DIFF_QUANT','none');os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
defaults={'--torch-dtype':'bfloat16','--temperature':'0','--num_beams':'1','--max-new-tokens':'1024','--conv-mode':'qwen_2','--num-chunks':'1','--chunk-idx':'0'}
for flag,value in defaults.items():
 if not any(token==flag or token.startswith(flag+'=') for token in remaining):remaining.extend([flag,value])
if '--no-flash-attention' not in remaining:remaining.append('--no-flash-attention')
if '--help' not in remaining and '-h' not in remaining:
 from input_guard import prepare_inputs
 if prepare_inputs(remaining,args.adapter_mode,args.exact_identity_guard):sys.exit(0)
import torch
from peft import PeftModel,get_peft_model_state_dict,set_peft_model_state_dict
from llava.model import builder

# The upstream loader infers model type from directory name. Explicitly select
# M3Diff so moving/renaming the adapter folder does not switch architecture.
original_loader=builder.load_pretrained_model
def portable_loader(model_path,model_base,model_name,*pos,**kw):
 return original_loader(model_path,model_base,'m3diff-portable-lora' if model_base is not None else 'm3diff-portable',*pos,**kw)
builder.load_pretrained_model=portable_loader
original_peft=PeftModel.from_pretrained.__func__
@classmethod
def audited_load(cls,model,model_id,*pos,**kw):
 pm=original_peft(cls,model,model_id,*pos,**kw)
 state=torch.load(Path(model_id)/'adapter_model.bin',map_location='cpu',weights_only=True)
 loaded=get_peft_model_state_dict(pm);assert set(loaded)==set(state),'Adapter keys mismatch'
 if args.adapter_mode=='unmerged_fp32':
  for name,param in pm.named_parameters():
   if 'lora_' in name:param.data=param.data.to(torch.float32)
  set_peft_model_state_dict(pm,state);loaded=get_peft_model_state_dict(pm)
  assert all(p.dtype==torch.float32 and torch.equal(p.detach().cpu(),state[k].float()) for k,p in loaded.items())
  pm.merge_and_unload=types.MethodType(lambda self:self.base_model.model,pm)
 info={'mode':args.adapter_mode,'adapter_path':str(Path(model_id).resolve()),'saved_keys_loaded':len(loaded),'saved_dtypes':sorted({str(p.dtype) for p in state.values()}),'effective_dtypes':sorted({str(p.dtype) for p in loaded.values()}),'exact_saved_values_restored':args.adapter_mode=='unmerged_fp32','Modal_required':False}
 args.load_audit.parent.mkdir(parents=True,exist_ok=True);args.load_audit.write_text(json.dumps(info,indent=2),encoding='utf8')
 print('ADAPTER LOAD AUDIT',json.dumps(info),flush=True);return pm
PeftModel.from_pretrained=audited_load
source=Path(__file__).with_name('baseline_eval.py')
sys.argv=[str(source)]+remaining
runpy.run_path(str(source),run_name='__main__')
