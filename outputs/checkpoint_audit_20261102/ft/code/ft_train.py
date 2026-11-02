"""Chạy llava/train/train.py của repo trên 1 GPU, không cần DeepSpeed/FlashAttention.

- Attention dùng SDPA của PyTorch (biến môi trường ATTN, mặc định 'sdpa').
- Không cần DeepSpeed: hàm maybe_zero_3 được thay bằng bản copy thường.
- Sửa chỗ thiếu khi chạy tiếp từ checkpoint: Trainer chỉ nạp lại LoRA, ở đây nạp thêm
  non_lora_trainables.bin (MDP + projector) để không bị lệch với trạng thái optimizer.
"""
import os
import torch
from llava.train import llava_trainer, train as T

_orig = llava_trainer.LLaVATrainer._load_from_checkpoint


def _load(self, resume_from_checkpoint, model=None):
    _orig(self, resume_from_checkpoint, model)
    p = os.path.join(resume_from_checkpoint, "non_lora_trainables.bin")
    if os.path.exists(p):
        sd = torch.load(p, map_location="cpu")
        m = model if model is not None else self.model
        res = m.load_state_dict(sd, strict=False)
        print(f"[resume] nạp lại {len(sd)} tensor MDP/projector, thiếu khớp: {len(res.unexpected_keys)}", flush=True)


llava_trainer.LLaVATrainer._load_from_checkpoint = _load
# Chạy 1 GPU không DeepSpeed: thay hàm gom tham số ZeRO-3 bằng bản copy thường
T.maybe_zero_3 = lambda param, ignore_status=False, name=None: param.detach().cpu().clone()

if __name__ == "__main__":
    T.train(attn_implementation=os.environ.get("ATTN", "sdpa"))
