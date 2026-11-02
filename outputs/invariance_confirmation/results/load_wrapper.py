"""Compare merged BF16 with active FP32 LoRA, without editing repository code."""
import argparse,json,runpy,sys,types
from pathlib import Path
import torch
from peft import PeftModel,get_peft_model_state_dict,set_peft_model_state_dict

parser=argparse.ArgumentParser();parser.add_argument('--adapter-mode',choices=['merged_bf16','unmerged_fp32'],required=True);parser.add_argument('--load-audit',type=Path,required=True)
args,remaining=parser.parse_known_args()
original=PeftModel.from_pretrained.__func__

@classmethod
def audited_load(cls,model,model_id,*pos,**kw):
    pm=original(cls,model,model_id,*pos,**kw)
    state=torch.load(Path(model_id)/'adapter_model.bin',map_location='cpu',weights_only=True)
    loaded=get_peft_model_state_dict(pm)
    assert set(loaded)==set(state),'Saved adapter keys not all loaded'
    before_dtypes=sorted({str(p.dtype) for p in loaded.values()})
    if args.adapter_mode=='unmerged_fp32':
        # Re-load after cast so even a loader dtype conversion cannot lose adapter bits.
        for name,p in pm.named_parameters():
            if 'lora_' in name:p.data=p.data.to(torch.float32)
        set_peft_model_state_dict(pm,state)
        loaded=get_peft_model_state_dict(pm)
        assert all(p.dtype==torch.float32 for p in loaded.values())
        assert all(torch.equal(loaded[k].detach().cpu(),state[k].float()) for k in state)
        # Return the original multimodal LM with active LoRA Linear modules intact.
        # This avoids an unnecessary PEFT generation wrapper as well as any merge.
        pm.merge_and_unload=types.MethodType(lambda self:self.base_model.model,pm)
    b=[v for k,v in loaded.items() if 'lora_B' in k]
    assert b and all(torch.count_nonzero(v)>0 for v in b)
    info={'mode':args.adapter_mode,'saved_dtypes':sorted({str(p.dtype) for p in state.values()}),'initial_loaded_dtypes':before_dtypes,
          'effective_adapter_dtypes':sorted({str(p.dtype) for p in loaded.values()}),'n_adapter_tensors':len(loaded),'all_saved_keys_loaded':True,
          'all_lora_B_nonzero':True,'saved_values_restored_exactly_after_fp32_cast':args.adapter_mode=='unmerged_fp32'}
    args.load_audit.parent.mkdir(parents=True,exist_ok=True);args.load_audit.write_text(json.dumps(info,indent=2))
    print('ADAPTER LOAD AUDIT',json.dumps(info),flush=True)
    return pm

PeftModel.from_pretrained=audited_load
source=Path('/mnt/m3diff/baseline_reproduction_v1/code/baseline_eval.py')
sys.argv=[str(source)]+remaining
runpy.run_path(str(source),run_name='__main__')
