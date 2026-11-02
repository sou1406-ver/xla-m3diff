"""One caption-SFT attempt; finite loss, frozen backbone and deadline audits."""
import os,time,json,hashlib,math
from pathlib import Path
import torch
from transformers import TrainerCallback
from llava.train import llava_trainer,train as T
OUT=Path('/mnt/m3diff/r64_v2_final_round');MODEL=OUT/'m3diff-v2-final-lora'
T.maybe_zero_3=lambda p,ignore_status=False,name=None:p.detach().cpu().clone()
class Audit(TrainerCallback):
    def __init__(self,model):self.model=model;self.started=time.time();self.stop_reason=None
    def on_train_begin(self,args,state,control,**kwargs):
        rows=[];init=hashlib.sha256();bzero=True
        for n,p in self.model.named_parameters():
            if not p.requires_grad:continue
            assert 'lora_' in n or 'vision_resampler' in n or 'mm_projector' in n,n
            assert 'vision_tower' not in n,n
            rows.append({'name':n,'n':p.numel(),'dtype':str(p.dtype)})
            if 'lora_' in n:
                init.update(n.encode());init.update(p.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes())
                if 'lora_B' in n:bzero=bzero and bool(torch.count_nonzero(p).item()==0)
        assert bzero,'Must start from fresh LoRA initialized on original base'
        assert state.max_steps==450,state.max_steps
        (OUT/'TRAIN_INITIALIZATION_AUDIT.json').write_text(json.dumps({'fresh_lora_B_zero':bzero,'initial_lora_sha256':init.hexdigest(),'max_steps':state.max_steps,'trainable':rows,'total_trainable':sum(r['n'] for r in rows),'base_model_name_or_path':self.model.config._name_or_path,'output_dir':args.output_dir,'started':self.started},indent=2))
        print('TRAIN_AUDIT: fresh LoRA, frozen vision/base LM,450updates',flush=True)
    def on_log(self,args,state,control,logs=None,**kwargs):
        if logs and 'loss' in logs and not math.isfinite(float(logs['loss'])):raise FloatingPointError('Nonfinite loss: no retry/adoption')
    def on_step_end(self,args,state,control,**kwargs):
        if state.global_step<state.max_steps and time.time()>=float(os.environ['V2_SOFT_DEADLINE_UNIX']):
            self.stop_reason='round_budget_time_limit';control.should_training_stop=True
        (OUT/'TRAIN_PROGRESS.json').write_text(json.dumps({'global_step':state.global_step,'max_steps':state.max_steps,'elapsed_train_seconds':time.time()-self.started,'stop_reason':self.stop_reason}))
        return control
    def on_train_end(self,args,state,control,**kwargs):
        finite=all(bool(torch.isfinite(p).all().item()) for p in self.model.parameters() if p.requires_grad)
        (OUT/'TRAIN_END.json').write_text(json.dumps({'global_step':state.global_step,'max_steps':state.max_steps,'stop_reason':self.stop_reason,'parameters_finite':finite,'training_seconds':time.time()-self.started,'complete':state.global_step==450 and self.stop_reason is None and finite},indent=2))
orig=llava_trainer.LLaVATrainer.__init__
def initialize(self,*args,**kwargs):
    orig(self,*args,**kwargs);self.add_callback(Audit(self.model))
llava_trainer.LLaVATrainer.__init__=initialize
if __name__=='__main__':T.train(attn_implementation='sdpa')
