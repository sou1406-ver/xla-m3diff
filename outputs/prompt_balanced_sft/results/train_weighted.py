"""Matched training forward passes with an explicit negative-loss ablation."""
import os,json,hashlib,math
from pathlib import Path
import torch
from transformers import set_seed
set_seed(42)
from llava.train import train as T,llava_trainer
WEIGHT=float(os.environ['M3DIFF_NEGATIVE_WEIGHT']);assert WEIGHT in [0.,1.]
T.maybe_zero_3=lambda param,ignore_status=False,name=None:param.detach().cpu().clone()
original_item=T.LazySupervisedDataset.__getitem__
def weighted_item(self,i):
    result=original_item(self,i);negative=bool(self.list_data_dict[i].get('is_invariance_negative',False))
    result['_sft_weight']=WEIGHT if negative else 1.;result['_is_negative']=negative;return result
T.LazySupervisedDataset.__getitem__=weighted_item
original_collate=T.DataCollatorForSupervisedDataset.__call__
def weighted_collate(self,instances):
    output=original_collate(self,instances)
    output['_sft_weight']=torch.tensor([i['_sft_weight'] for i in instances],dtype=torch.float32)
    output['_is_negative']=torch.tensor([i['_is_negative'] for i in instances],dtype=torch.bool)
    return output
T.DataCollatorForSupervisedDataset.__call__=weighted_collate
def fingerprint(params):
    h=hashlib.sha256()
    for name,p in sorted(params):
        h.update(name.encode());h.update(str(p.dtype).encode());h.update(str(tuple(p.shape)).encode());h.update(p.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return h.hexdigest()
original_init=llava_trainer.LLaVATrainer.__init__;CURRENT=None
def audited_init(self,*args,**kwargs):
    global CURRENT
    original_init(self,*args,**kwargs);CURRENT=self
    assert self.args.seed==42 and not self.args.group_by_modality_length and not self.args.remove_unused_columns
    params=list(self.model.named_parameters());names=[n for n,p in params if p.requires_grad]
    assert names and all('lora_' in n for n in names)
    assert all(p.dtype==torch.float32 for n,p in params if 'lora_' in n)
    out=Path(self.args.output_dir);out.mkdir(parents=True,exist_ok=True)
    info={'seed':42,'negative_loss_weight':WEIGHT,'lora_init_sha256':fingerprint([(n,p) for n,p in params if 'lora_' in n]),'MDP_init_sha256':fingerprint([(n,p) for n,p in params if 'vision_resampler' in n]),'trainable_names':names,'all_LoRA_FP32':True}
    (out/'initialization_audit.json').write_text(json.dumps(info,indent=2))
    self._weight_diagnostics={'positive_samples':0,'negative_samples':0,'positive_unweighted_loss_sum':0.,'negative_unweighted_loss_sum':0.,'negative_weighted_loss_sum':0.,'zero_weight_samples':0,'all_valid_target_tokens':True,'all_losses_finite':True}
llava_trainer.LLaVATrainer.__init__=audited_init
original_loss=llava_trainer.LLaVATrainer.compute_loss
def weighted_loss(self,model,inputs,return_outputs=False,**kwargs):
    weight=inputs.pop('_sft_weight');negative=inputs.pop('_is_negative')
    assert weight.numel()==negative.numel()==1
    assert int((inputs['labels']!=-100).sum())>0,'Sample has no assistant target tokens'
    output=original_loss(self,model,inputs,return_outputs=return_outputs,**kwargs)
    loss=output[0] if return_outputs else output
    assert bool(torch.isfinite(loss)),'Nonfinite unweighted loss'
    kind='negative' if bool(negative.item()) else 'positive';value=float(loss.detach());w=float(weight.item())
    self._weight_diagnostics[kind+'_samples']+=1;self._weight_diagnostics[kind+'_unweighted_loss_sum']+=value
    if kind=='negative':self._weight_diagnostics['negative_weighted_loss_sum']+=value*w
    if w==0:self._weight_diagnostics['zero_weight_samples']+=1
    result=loss*weight.mean()
    return (result,output[1]) if return_outputs else result
llava_trainer.LLaVATrainer.compute_loss=weighted_loss
original_sampler=llava_trainer.LLaVATrainer._get_train_sampler
class AuditedSampler(torch.utils.data.Sampler):
    def __init__(self,inner,path):self.inner=inner;self.path=path;self.orders=[]
    def __len__(self):return len(self.inner)
    def __iter__(self):
        order=list(iter(self.inner));self.orders.append(order);self.path.write_text(json.dumps(self.orders));return iter(order)
def sampler(self):
    inner=original_sampler(self);return AuditedSampler(inner,Path(self.args.output_dir)/'sample_orders.json') if inner is not None else None
llava_trainer.LLaVATrainer._get_train_sampler=sampler
if __name__=='__main__':
    T.train(attn_implementation='sdpa')
    stats=CURRENT._weight_diagnostics;assert stats['positive_samples']==384 and stats['negative_samples']==128,stats
    assert stats['zero_weight_samples']==(128 if WEIGHT==0 else 0),stats
    if WEIGHT==0:assert stats['negative_weighted_loss_sum']==0
    (Path(CURRENT.args.output_dir)/'weight_diagnostics.json').write_text(json.dumps(stats,indent=2))
    print('WEIGHT DIAGNOSTICS',json.dumps(stats),flush=True)
