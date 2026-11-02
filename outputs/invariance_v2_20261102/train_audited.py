"""Two matched-index data recipes; explicit trainable/gradient/target audits."""
import hashlib, json, math, os
from pathlib import Path
import torch
from transformers import set_seed
set_seed(42)
from llava.train import train as T, llava_trainer

T.maybe_zero_3=lambda param,ignore_status=False,name=None:param.detach().cpu().clone()
CURRENT=None

def fingerprint(params):
    h=hashlib.sha256()
    for name,p in sorted(params):
        h.update(name.encode()); h.update(str(p.dtype).encode()); h.update(str(tuple(p.shape)).encode())
        h.update(p.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return h.hexdigest()

init=llava_trainer.LLaVATrainer.__init__
def audited_init(self,*a,**kw):
    global CURRENT
    init(self,*a,**kw); CURRENT=self
    params=list(self.model.named_parameters()); names=[n for n,p in params if p.requires_grad]
    assert names and all('lora_' in n for n in names)
    assert all(p.dtype==torch.float32 for n,p in params if 'lora_' in n)
    assert not self.args.group_by_modality_length and self.args.seed==42
    out=Path(self.args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/'initialization_audit.json').write_text(json.dumps({
        'trainable_names':names,'only_lora':True,'lora_init_sha256':fingerprint([(n,p) for n,p in params if 'lora_' in n]),
        'MDP_init_sha256':fingerprint([(n,p) for n,p in params if 'vision_resampler' in n])},indent=2))
    self._audit={'samples':0,'min_answer_tokens':100000,'all_finite':True}
llava_trainer.LLaVATrainer.__init__=audited_init
loss=llava_trainer.LLaVATrainer.compute_loss
def audited_loss(self,model,inputs,return_outputs=False,**kw):
    nt=int((inputs['labels']!=-100).sum()); assert nt>0
    output=loss(self,model,inputs,return_outputs=return_outputs,**kw)
    value=output[0] if return_outputs else output
    assert bool(torch.isfinite(value))
    self._audit['samples']+=1; self._audit['min_answer_tokens']=min(nt,self._audit['min_answer_tokens'])
    return output
llava_trainer.LLaVATrainer.compute_loss=audited_loss
sampler=llava_trainer.LLaVATrainer._get_train_sampler
class AuditedSampler(torch.utils.data.Sampler):
    def __init__(self,inner,path): self.inner=inner; self.path=path; self.orders=[]
    def __len__(self): return len(self.inner)
    def __iter__(self):
        order=list(iter(self.inner)); self.orders.append(order); self.path.write_text(json.dumps(self.orders)); return iter(order)
def audited_sampler(self):
    inner=sampler(self)
    return AuditedSampler(inner,Path(self.args.output_dir)/'sample_orders.json') if inner is not None else None
llava_trainer.LLaVATrainer._get_train_sampler=audited_sampler
if __name__=='__main__':
    T.train(attn_implementation='sdpa')
    assert CURRENT.state.global_step==128 and CURRENT._audit['samples']==1024, CURRENT._audit
    out=Path(CURRENT.args.output_dir)
    assert not torch.load(out/'non_lora_trainables.bin',map_location='cpu',weights_only=True)
    (out/'TRAIN_DONE.json').write_text(json.dumps({'steps':128,'only_lora':True,**CURRENT._audit},indent=2))

