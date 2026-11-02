"""Single-GPU SFT with explicit pre-model seed and auditable initialization/order."""
import os
import json
import hashlib
from pathlib import Path
from transformers import set_seed

set_seed(42)  # Must precede creation of the model and randomly initialized LoRA.

import torch
from llava.train import llava_trainer, train as T

T.maybe_zero_3=lambda param,ignore_status=False,name=None:param.detach().cpu().clone()

def fingerprint(named):
    h=hashlib.sha256();names=[];count=0
    for name,param in sorted(named):
        names.append(name);count+=param.numel()
        h.update(name.encode());h.update(str(param.dtype).encode());h.update(str(tuple(param.shape)).encode())
        h.update(param.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return {'sha256':h.hexdigest(),'n_parameters':count,'names':names}

original_init=llava_trainer.LLaVATrainer.__init__
def audited_init(self,*args,**kwargs):
    original_init(self,*args,**kwargs)
    assert self.args.seed==42
    assert not self.args.group_by_modality_length
    params=list(self.model.named_parameters())
    info={'model_init_seed':42,'trainer_seed':self.args.seed,'group_by_modality_length':False,
          'lora_initialization':fingerprint([(n,p) for n,p in params if 'lora_' in n]),
          'MDP_initialization':fingerprint([(n,p) for n,p in params if 'vision_resampler' in n]),
          'trainable_names':[n for n,p in params if p.requires_grad],
          'trainable_parameters':sum(p.numel() for _,p in params if p.requires_grad)}
    out=Path(self.args.output_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'initialization_audit.json').write_text(json.dumps(info,indent=2))
    print('INITIALIZATION AUDIT',info['lora_initialization']['sha256'],info['MDP_initialization']['sha256'],flush=True)
llava_trainer.LLaVATrainer.__init__=audited_init

original_sampler=llava_trainer.LLaVATrainer._get_train_sampler
class AuditedSampler(torch.utils.data.Sampler):
    def __init__(self,inner,path):self.inner=inner;self.path=path
    def __len__(self):return len(self.inner)
    def __iter__(self):
        order=list(iter(self.inner))
        self.path.write_text(json.dumps(order))
        return iter(order)

def audited_sampler(self):
    inner=original_sampler(self)
    return AuditedSampler(inner,Path(self.args.output_dir)/'sample_order.json') if inner is not None else None
llava_trainer.LLaVATrainer._get_train_sampler=audited_sampler

if __name__=='__main__':T.train(attn_implementation=os.environ.get('ATTN','sdpa'))
