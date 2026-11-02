#    Copyright 2023 Haotian Liu
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import os
import warnings

from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
import torch
from llava.model import LlavaQwenForCausalLM
from llava.constants import DEFAULT_IMAGE_PATCH_TOKEN


def load_pretrained_model(
    model_path,
    model_base,
    model_name,
    load_8bit=False,
    load_4bit=False,
    device_map="auto",
    device="cuda",
    use_flash_attn=False,
    **kwargs,
):
    kwargs = {"device_map": device_map, **kwargs}
    normalized_model_name = model_name.lower()
    is_multimodal_model = any(
        marker in normalized_model_name for marker in ("llava", "m3diff")
    )

    if device != "cuda":
        kwargs["device_map"] = {"": device}

    if load_8bit:
        kwargs["load_in_8bit"] = True
    elif load_4bit:
        kwargs["load_in_4bit"] = True
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    else:
        kwargs.setdefault("torch_dtype", torch.float16)

    if use_flash_attn:
        kwargs["attn_implementation"] = "flash_attention_2"

    if is_multimodal_model:
        # Load LLaVA model
        if "lora" in normalized_model_name and model_base is None:
            warnings.warn(
                "There is `lora` in model name but no `model_base` is provided. If you are loading a LoRA model, please provide the `model_base` argument."
            )
        if "lora" in normalized_model_name and model_base is not None:
            from llava.model.language_model.llava_qwen import LlavaQwenConfig

            lora_cfg_pretrained = LlavaQwenConfig.from_pretrained(model_path)
            lora_config_file = os.path.join(model_path, "config.json")
            if os.path.isfile(lora_config_file):
                import json

                with open(lora_config_file, "r", encoding="utf-8") as f:
                    saved_lora_config = json.load(f)
                if "vocab_size" not in saved_lora_config:
                    base_cfg_pretrained = AutoConfig.from_pretrained(model_base)
                    base_vocab_size = getattr(base_cfg_pretrained, "vocab_size", None)
                    if base_vocab_size is None:
                        base_vocab_size = getattr(
                            getattr(base_cfg_pretrained, "text_config", None),
                            "vocab_size",
                            None,
                        )
                    if base_vocab_size is None:
                        raise ValueError(
                            f"Neither {lora_config_file} nor the base model "
                            f"{model_base!r} defines vocab_size."
                        )
                    lora_cfg_pretrained.vocab_size = base_vocab_size
            tokenizer = AutoTokenizer.from_pretrained(model_base, use_fast=False)
            model = LlavaQwenForCausalLM.from_pretrained(
                model_base, low_cpu_mem_usage=True, config=lora_cfg_pretrained, **kwargs
            )

            token_num, tokem_dim = model.lm_head.out_features, model.lm_head.in_features

            if model.lm_head.weight.shape[0] != token_num:
                model.lm_head.weight = torch.nn.Parameter(
                    torch.empty(token_num, tokem_dim, device=model.device, dtype=model.dtype)
                )
                model.model.embed_tokens.weight = torch.nn.Parameter(
                    torch.empty(token_num, tokem_dim, device=model.device, dtype=model.dtype)
                )

            print("Loading additional LLaVA weights...")
            if os.path.exists(os.path.join(model_path, "non_lora_trainables.bin")):
                non_lora_trainables = torch.load(
                    os.path.join(model_path, "non_lora_trainables.bin"), map_location="cpu"
                )
            else:
                from huggingface_hub import hf_hub_download

                def load_from_hf(repo_id, filename, subfolder=None):
                    cache_file = hf_hub_download(
                        repo_id=repo_id, filename=filename, subfolder=subfolder
                    )
                    return torch.load(cache_file, map_location="cpu")

                non_lora_trainables = load_from_hf(model_path, "non_lora_trainables.bin")
            non_lora_trainables = {
                (k[11:] if k.startswith("base_model.") else k): v
                for k, v in non_lora_trainables.items()
            }
            if any(k.startswith("model.model.") for k in non_lora_trainables):
                non_lora_trainables = {
                    (k[6:] if k.startswith("model.") else k): v
                    for k, v in non_lora_trainables.items()
                }

            model.load_state_dict(non_lora_trainables, strict=False)

            from peft import PeftModel

            print("Loading LoRA weights...")
            model = PeftModel.from_pretrained(model, model_path)
            print("Merging LoRA weights...")
            model = model.merge_and_unload()
            print("Model is loaded...")
        elif model_base is not None:
            print("Loading LLaVA from base model...")
            tokenizer = AutoTokenizer.from_pretrained(model_base, use_fast=False)
            cfg_pretrained = AutoConfig.from_pretrained(model_path)
            model = LlavaQwenForCausalLM.from_pretrained(
                model_base, low_cpu_mem_usage=True, config=cfg_pretrained, **kwargs
            )

            mm_projector_weights = torch.load(
                os.path.join(model_path, "mm_projector.bin"), map_location="cpu"
            )
            mm_projector_weights = {k: v.to(torch.float16) for k, v in mm_projector_weights.items()}
            model.load_state_dict(mm_projector_weights, strict=False)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
            model = LlavaQwenForCausalLM.from_pretrained(
                model_path, low_cpu_mem_usage=True, **kwargs
            )
    else:
        # Load language model
        if model_base is not None:
            from peft import PeftModel

            tokenizer = AutoTokenizer.from_pretrained(model_base, use_fast=False)
            model = AutoModelForCausalLM.from_pretrained(
                model_base, low_cpu_mem_usage=True, **kwargs
            )
            print(f"Loading LoRA weights from {model_path}")
            model = PeftModel.from_pretrained(model, model_path)
            print("Merging weights")
            model = model.merge_and_unload()
            print("Convert to FP16...")
            model.to(torch.float16)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
            model = AutoModelForCausalLM.from_pretrained(
                model_path, low_cpu_mem_usage=True, **kwargs
            )

    image_processor = None

    if is_multimodal_model:
        mm_use_im_patch_token = getattr(model.config, "mm_use_im_patch_token", True)
        if mm_use_im_patch_token:
            tokenizer.add_tokens([DEFAULT_IMAGE_PATCH_TOKEN], special_tokens=True)
        tokenizer_size = len(tokenizer)
        embedding_size = model.get_input_embeddings().num_embeddings
        if tokenizer_size > embedding_size:
            model.resize_token_embeddings(tokenizer_size)
        vision_tower = model.get_vision_tower()

        if not vision_tower.is_loaded:
            vision_tower.load_model(
                device_map=kwargs["device_map"],
                torch_dtype=kwargs.get("torch_dtype", model.dtype),
            )

        image_processor = vision_tower.image_processor

    if hasattr(model.config, "max_sequence_length"):
        context_len = model.config.max_sequence_length
    else:
        context_len = 2048

    return tokenizer, model, image_processor, context_len
